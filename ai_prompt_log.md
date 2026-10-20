# AI prompt and audit log

## Initial prompt used

> Build a small student-level Python 3.11+ project for an AD331 multi-provider LLM gateway assignment. The user requests an offline, mock-only version with no provider keys or calls. Use Pydantic v2, an async generator, two adapters that imitate different event formats, a Streamlit interface with streamed text and metrics, tests, README, and local Docker files. Label every reply, token count, and cost as simulated or hypothetical. Do not claim official provider integration.

This prompt summarizes the instructions supplied to the AI assistant for this project. The code was then inspected and revised.

## Issue 1: The draft repeated prompt text

The first `sample_reply` built a `topic` from the user's prompt and placed it in the visible sample reply. That was unnecessary and could show private input again on screen or in a recording.

```diff
- topic = " ".join(prompt.split())[:80]
- return f"Simulated OpenAI-style reply. You asked about: {topic}. ..."
+ topic = "async streaming" if "async" in prompt.lower() else "your question"
+ return f"Simulated OpenAI-style reply about {topic}. ..."
```

The final version responds with a generic topic label and never repeats the prompt. This is a display protection, not a promise to safely process secrets.

## Issue 2: The first speed value could spike

The first draft measured generation speed from the timestamp of the first text chunk. On that same chunk, elapsed generation time was almost zero, so even a short reply could display an absurd tokens-per-second value. This was a timing bug in the draft's live metrics.

```diff
- generation_time = max(now - first_text_at, 0.000001)
+ generation_time = elapsed
```

The final code uses time since the request began for the display speed, including the wait for first text. The final metric uses the same denominator. TTFT itself is still captured when the first nonempty delta arrives.

## Other checks

- OpenAI-style final usage events have an empty `choices` array; parsing skips them safely.
- Anthropic-style `message_start` and `message_delta` are not mistaken for text deltas.
- The gateway has no network client and never reads an API key. The test error uses a dummy string and checks that the error does not echo it.
- Cost uses decimal arithmetic and six-place rounding. All rates are illustrative.
- Offline tests do not establish that real SDK calls or provider token accounting work.
