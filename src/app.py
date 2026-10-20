"""Simple Streamlit interface for the offline gateway demo."""

import asyncio

import streamlit as st

from src.gateway import DemoModeError, GatewayError, UnifiedLLMGateway
from src.pricing import DEMO_RATES


st.set_page_config(page_title="LLM Gateway Demo", layout="centered")
st.title("Multi-provider LLM gateway demo")
st.info("Offline simulation. No AI provider is contacted. Replies and token counts are local examples. Costs are hypothetical, not billed amounts.")

provider = st.selectbox("Provider style", ["OpenAI-style", "Anthropic-style"])
models = [name for name in DEMO_RATES if name.startswith(provider)]
model = st.selectbox("Demo model", models)
prompt = st.text_area("Your prompt", value="Explain async streaming in simple words.")
temperature = st.slider("Temperature (shown for interface demo)", 0.0, 1.0, 0.7, 0.1)
simulate_error = st.checkbox("Show a safe demo error")

if st.button("Run offline demo", type="primary"):
    st.subheader("Local sample reply")
    text_box = st.empty()
    metrics_box = st.empty()

    async def run_demo():
        gateway = UnifiedLLMGateway()
        parts = []
        async for chunk in gateway.stream(prompt, model, temperature, simulate_error):
            parts.append(chunk.delta_text)
            text_box.markdown("".join(parts) + ("▌" if not chunk.is_final else ""))
            if chunk.telemetry:
                t = chunk.telemetry
                metrics_box.markdown(
                    f"**Local demo metrics**  \n"
                    f"Time to first text: {t.ttft_ms:.1f} ms  \n"
                    f"Speed: {t.tokens_per_second:.1f} estimated tokens/sec  \n"
                    f"Prompt / reply: {t.prompt_tokens} / {t.completion_tokens} estimated tokens  \n"
                    f"Elapsed: {t.latency_seconds:.2f} sec  \n"
                    f"Hypothetical cost: ${t.hypothetical_cost_usd:.6f} (not billed)"
                )

    try:
        asyncio.run(run_demo())
    except DemoModeError as error:
        st.warning(str(error))
    except GatewayError as error:
        st.error(str(error))

st.caption("The two adapters imitate different event shapes. They do not use official provider SDKs or API keys.")
