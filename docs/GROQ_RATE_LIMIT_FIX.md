# Groq request protection

All active Groq integrations (classification, satellite briefing, chat) use one process-shared guard. SDK retries are disabled; no video thread sleeps through a cooldown. A 429 uses Retry-After seconds/date or Groq's retry message. Without guidance, backoff grows from 5 to 300 seconds. Explicit server guidance may exceed 300 seconds and is respected. Requests resume only when a later event or user request arrives.

Track reasoning is requested only after three observations when ConvNeXt is uncertain (or margin <0.25). Failed track attempts wait at least 60 seconds. Successful label/reasoning is retained for the video's lifetime; it is displayed as cached on subsequent observations, without counting it as fresh repeated classification evidence. New video runs reset track caches. Local ConvNeXt continues on every observed crop. Scene cuts have new track IDs.

Successful identical Groq requests are cached for one hour, maximum 128 entries, including briefings/chat. This cache is checked before cooldown admission. Results are never silently replaced with fabricated VLM output. Fresh/cached metadata is additive to existing endpoint fields. Tracking tables show cached reasoning or unavailable/local fallback. Satellite and intelligence pages show source/status. Health exposes availability and counters.

Optional environment settings (no credential changes required):

| Setting | Default |
| --- | --- |
| GROQ_MIN_INTERVAL_SECONDS | 10 |
| GROQ_TRACK_RETRY_SECONDS | 60 |
| GROQ_LOCAL_TOKEN_BUDGET | 180000 |
| GROQ_REQUEST_TOKEN_RESERVE | 3000 |
| GROQ_CACHE_TTL_SECONDS | 3600 |
| GROQ_CLASSIFY_MAX_TOKENS | 120 |
| GROQ_BRIEFING_MAX_TOKENS | 250 |
| GROQ_CHAT_MAX_TOKENS | 300 |

Budget admission reserves 3000 tokens, then reconciles reported actual usage after success. Failed/unknown-usage attempts retain the conservative reserve. The local budget resets after 24 hours in this process. Logs contain counters and cooldown durations, never keys, images, prompts, exception bodies, or user messages. Enable INFO logging to see success/cache logs; rate-limit events are WARNING. Counters cover actual requests, known prompt/completion/total tokens, unknown usage, cache hits, track cache hits, suppressed calls, errors and rate-limit events. Health counters are process cumulative, not per-video.

Measured offline verification:
- 100 identical requests: 1 network call, 99 cache hits, 99% reduction versus uncached requests.
- 100 requests under injected HTTP 429: 1 failed network call, 99 suppressed requests, 99% reduction versus unprotected attempts.
- Real Destroyer1 video with forced uncertain classification and injected Groq 429: 120 processed frames, two vessel IDs, zero error frames, local classifier continued, one Groq network call. This is not a measured production token-saving percentage.
- 35 tracking/Kalman regression tests passed. Seven Groq tests passed, including real video integration.

Limitations: guard/cache/budget are in-memory and shared within one Python process only. Restart or multiple workers require external shared storage for fleet-wide accounting. Groq organization usage by other applications is not visible here; Groq remains authoritative. Image input tokens still apply despite shorter text prompts/output caps. Conservative request reservation can suppress a cheaper request near the local budget. Successful track reasoning is retained without automatic refresh; materially changed viewpoint may need a new video/run. Pipeline already has mutable per-video state and concurrent video runs require separate pipeline instances. No live paid Groq requests were used for validation; tests injected realistic errors/responses. Endpoint routes and existing response fields remain compatible.

Files changed: models/groq_vlm.py; models/vlm_guard.py (new); pipeline/orchestrator.py; backend/main.py; frontend/src/api/types.ts; frontend/src/features/tracking/index.tsx; frontend/src/features/satellite/index.tsx; frontend/src/features/intelligence/index.tsx; tests/test_groq_rate_limit.py (new); GROQ_RATE_LIMIT_FIX.md (new).
