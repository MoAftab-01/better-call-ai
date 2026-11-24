# AI Assistant — General Information

## Scope and audit decision

This opt-in upgrade reuses FastAPI, HTTPX, the existing conversation workspace and
browser voice controls. It does not activate RAG or change publication/review state.
`backend/chat/general.py` has no retrieval, corpus, filesystem or approval dependency.
The existing research endpoint keeps its privileged authentication and publication
gate. No independently approved public corpus is configured; source-backed research
remains blocked. No new cloud service or dependency is needed.

The separate `GET /api/assistant/status` reports enabled/available state without keys.
Availability means enabled/configured, not a live provider health probe.
`POST /api/assistant/chat` accepts a question and up to six history messages (three
completed user/assistant exchanges). Each history message is limited to 1,200
characters; the current question to 2,000; streamed request body to 16,000 bytes.
Only successful AI exchanges enter frontend context. Failed/cancelled requests do
not add context, retry does not duplicate the question, and mode switching clears it.
No privileged research bearer token is sent to this intentionally public endpoint.

## Actual AI behavior and boundaries

When configured, Groq generates a new explanation from the question and bounded
history. It receives no legal sources, PDFs, indexes, citations or browsing tools.
The server requires a bounded JSON answer, rejects extra fields, truncation,
URLs, citation-shaped strings and some claims of verified authority, then attaches
its own disclaimer, `sources_verified: false`, `legal_currentness: unknown`, and
empty citations. The UI renders plain text and no answer-specific source cards.

This filtering is defense in depth, **not a proof of factual accuracy or complete
hallucination detection**. Uncited prose can still be wrong. No current-law or legal
correctness verification is performed. Exact provisions, case citations, deadlines
and penalties are deliberately outside this source-free mode. Model instructions
require uncertainty and safe refusal rather than invented authority.

A conservative keyword gate returns a server-authored safety boundary for detected
personal high-stakes or evidence-evasion requests, without a model call. Other
requests remain constrained by the system prompt and output checks. The heuristic
is not a comprehensive risk classifier and can refuse benign questions. Messages
are explicitly labelled `generated` or `safety_boundary`, never as verified evidence.

Groq errors never silently become fictional AI answers. The independently selectable
**Try synthetic demo** mode remains the deterministic fallback. Browser dictation
and read aloud are reused: consent, transcript review, no automatic submission,
stop/cancel, and unsupported-browser typed fallback remain intact.

## Backend configuration

Use the existing Render service `better-call-ai-api`, Python 3.12, **one worker**.
Do not deploy or change cloud configuration until separately approved.

| Variable | Required setting |
| --- | --- |
| `AI_ASSISTANT_ENABLED` | `true` to opt in; absent/`false` disables it (restart required) |
| `GROQ_API_KEY` | Real backend-only secret; never in Git, frontend or logs |
| `GROQ_MODEL` | An enabled chat model supporting JSON-object output from the operator's Groq account |
| `AI_ASSISTANT_RPM` | Default `6`; supported range 1–30 attempts per minute |
| `AI_ASSISTANT_DAILY_LIMIT` | Default `100`; supported range 1–1000 attempts per rolling 24 hours |
| `DEMO_ENABLED` / `DEMO_PROVIDER` | `true` / `deterministic` to retain the fallback |
| `KANOON_ENV` | `production` on Render; `local` for loopback testing |
| `CORPUS_KIND` / `RETRIEVAL_MODE` | `public` / `bm25` |
| `KANOON_ALLOWED_ORIGINS` | Exact frontend HTTPS origin, no wildcard |
| `KANOON_ACCESS_TOKEN` | Retain the separate research secret; do not expose it to the browser |
| Public corpus pins, signing keys, approval files | Leave absent; no corpus is being published |

The existing frontend uses `VITE_API_BASE_URL=https://better-call-ai-api.onrender.com`.
There is no new frontend secret or provider key. `.env.example` is not auto-loaded.
Groq configuration is read only from the backend process environment.

Provider connection timeout is 5 seconds; HTTP timeout 18 seconds; the route has a
22-second overall deadline, response cap 65,536 bytes and 768 completion-token cap.
No automatic provider retries. TLS verification remains enabled, environment proxies
are not used and redirects are not followed. The existing shared two-request
concurrency and ten-second request-body deadline apply to AI as well as research/demo.

Caps count malformed/failed attempts too, use server time and a global process
budget, and do not trust forwarded IP headers. They reset on restart and are **not**
a persistent billing cap or distributed/per-user protection. Bots can exhaust the
budget; do not scale workers without shared limits. Set Groq account/project spending
limits separately before public activation. Browser cancellation stops UI updates;
it does not guarantee an already sent provider request is cancelled or unbilled.

## Local and deployment steps

1. In a fresh backend terminal, set local/public/BM25 mode, a deliberately absent
   `PUBLIC_CORPUS_DIR`, `DEMO_ENABLED=true`, `DEMO_PROVIDER=deterministic`, and
   `AI_ASSISTANT_ENABLED=true`. Supply the Groq key securely:

   ```powershell
   $env:KANOON_ENV = 'local'
   $env:CORPUS_KIND = 'public'
   $env:RETRIEVAL_MODE = 'bm25'
   $env:PUBLIC_CORPUS_DIR = '.\public-corpus-not-installed'
   $env:DEMO_ENABLED = 'true'
   $env:DEMO_PROVIDER = 'deterministic'
   $env:AI_ASSISTANT_ENABLED = 'true'
   $env:GROQ_API_KEY = [System.Net.NetworkCredential]::new('', (Read-Host 'Groq API key' -AsSecureString)).Password
   $env:GROQ_MODEL = Read-Host 'Enabled Groq chat model supporting JSON mode'
   .\.venv\Scripts\python.exe -B -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --workers 1 --no-access-log
   ```

2. In a frontend terminal, unset `VITE_API_BASE_URL`, set `KANOON_BACKEND_PORT=8001`,
   and run `npm.cmd --prefix frontend run dev`. Use a free port if already occupied.
3. Verify `/api/assistant/status` reports available. Without a key/model it reports
   unavailable and question submission returns a safe error, not a fabricated answer.
4. After code review, separately authorize commit/push. After deployment approval,
   set the variables above in the existing Render service and deploy the reviewed
   commit; build the existing Vercel frontend against that backend. No new services.
5. Smoke-test health 200, assistant available, research readiness 503, production
   research authentication, exact CORS, source isolation and the synthetic fallback.
6. Disable with `AI_ASSISTANT_ENABLED=false` and restart/redeploy the existing backend
   if necessary. Keep all corpus publication configuration absent throughout.

See [Groq chat documentation](https://console.groq.com/docs/text-chat) and the
[API reference](https://console.groq.com/docs/api-reference) for model/JSON support.
This implementation reuses HTTPX rather than adding another SDK.

## Manual acceptance

- Select **AI Assistant — General Information**; verify the prominent unverified
  label and absence of official-source cards. Research remains publication pending.
- Ask varied conceptual questions: “Explain mediation simply”, “What is a contract?”,
  and “What does a consumer complaint mean in general?” Check for relevant distinct
  generated explanations. Their legal truth still requires independent verification.
- Ask “How is that different?”; confirm relevant follow-up context. Clear or switch
  modes and confirm the previous conversation is not reused.
- Ask for yesterday's amendment, a specific case citation, or exact filing deadline:
  expect uncertainty/refusal or safe output rejection, never invented verified sources.
- Try a personalized arrest/court-deadline question; expect a professional-help
  boundary, not a legal strategy or guaranteed outcome. Do not use real private details.
- Exercise microphone permission allow/deny, start/stop/cancel, transcript review,
  no auto-send, read-aloud/stop, and unsupported-browser typing. Repeat on real mobile.
- Test request cancellation, retry, provider failure, missing credentials, rate limits,
  and explicit switching to the deterministic synthetic demo.

## Verification recorded 24 November 2026

- Full backend suite: **423 passed**, including **58 new assistant tests**; one
  existing Starlette/HTTPX TestClient deprecation warning.
- Frontend lint, TypeScript and hosted build against the actual Render origin: PASS.
  Existing Node provider/configuration guards: **10 passed**.
- Installed Chrome: existing publication-pending/demo regressions **25 checks**;
  new AI mocked-speech **13 checks** and unsupported-speech **12 checks**, all PASS.
  Tests exercise the HTTP assistant route with an explicitly synthetic Groq transport,
  bounded follow-ups, retries, cancellation, missing-provider UI, source isolation and
  320px layout. No research POST or privileged bearer exposure was observed.
- Focused testing exposed plural verified-source claims escaping output rejection;
  the filter was fixed. New browser label/interception setup errors were corrected;
  the final checks above pass. Existing tests were retained without weakened assertions.
- Subsequent local live verification used the operator-configured backend with
  `GROQ_MODEL=openai/gpt-oss-120b`: generated explanations and a contextual follow-up
  returned HTTP 200, empty citations and `sources_verified: false`. The Groq key stayed
  in the operator's backend terminal and was not copied into the repository.
- The maintainer reported **all eight manual acceptance checks passed**, including
  live Groq, contextual follow-ups, microphone dictation, read-aloud and the independent
  synthetic fallback. This is separate from mocked browser tests and does not verify
  legal correctness, currentness, applicability or performance under load.
- A stale local Vite process had proxied port 5173 to the old backend on 8001. Restarting
  that frontend with process-only `KANOON_BACKEND_PORT=8000` fixed mode discovery;
  no tracked Vite proxy configuration changed. The operator restarted the credentialed
  backend in public/BM25 mode with no corpus: health/AI/demo passed, research readiness
  and submission returned 503 (`publication_pending` / `corpus_not_approved`).
- Isolated **43-file public runtime package** passed AI/demo/health checks using a
  synthetic transport; research remained 401/503, with no private or ML dependencies.
- All **179 protected hashes unchanged**; both review audit chains PASS with zero
  events and eligible passages. No legal corpus published, submitted or approved.
- These checks precede the separately approved implementation commit/push. No new
  cloud service, hosting environment change or manual deployment is part of this release preparation.
