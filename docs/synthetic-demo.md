# Isolated synthetic chat and browser voice

This opt-in demonstration is separate from research and publication approval.
Three original fictional exercises cover a rent receipt, a wrong parcel and a
student document timeline. They assert no rights, remedies, statutes or deadlines.
Every reply says it is synthetic and has zero official citations. Unmatched
questions receive a scope explanation. This is not a general legal chatbot.

## Configuration and local manual review

No dependencies, source downloads, publication approvals or corpus are needed.
The template is documentation; it is not automatically loaded.

Backend, from the repository root in PowerShell:

```powershell
$env:KANOON_ENV = 'local'
$env:CORPUS_KIND = 'public'
$env:RETRIEVAL_MODE = 'bm25'
$env:DEMO_ENABLED = 'true'
$env:DEMO_PROVIDER = 'deterministic'
.\.venv\Scripts\python.exe -B -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Frontend, in a second PowerShell at the same repository root:

```powershell
Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
npm.cmd --prefix frontend run dev
```

Open http://127.0.0.1:5173. The source-publication-pending notice stays visible.
Choose **Try synthetic demo** to opt in. Only then is sending enabled. Try a
fictional rent receipt or parcel exercise, Enter to send and Shift+Enter for a
newline. Check user/assistant messages, loading, cancellation, retry and Clear.
Switching modes clears the conversation and source selection. Research remains
blocked. No token is requested for this narrow public endpoint.

For a later, separately authorised deployment, leave existing public/BM25,
one-worker production settings, access protection and exact HTTPS CORS unchanged.
Set DEMO_ENABLED=true in the backend only. The frontend discovers availability
from GET /api/demo/status. No frontend flag, bearer token or rebuild-time secret
is needed. Disable with DEMO_ENABLED=false and restart the backend. This does
not alter publication pins, signatures, manifests, approvals or audit state.
Do not populate missing publication configuration to enable the demo.

Optional Groq: set DEMO_PROVIDER=groq plus backend-only GROQ_API_KEY and GROQ_MODEL.
The existing provider transport sends only the current question and three
synthetic examples, with separate demo instructions and no chat history. The
model selects a known synthetic ID; arbitrary model prose is never returned.
The server supplies the fixed fictional response. Missing configuration, errors,
invalid IDs or an eight-second selection deadline use deterministic examples.
No live provider call is needed for testing. Avoid personal/confidential data.

## API and safety boundaries

- GET /api/demo/status returns enabled/mode/provider, never keys or research access.
- POST /api/demo/chat accepts only a nonblank message up to 2,000 characters.
  Extra source IDs, paths, history and research controls are rejected.
- The demo route has no retrieval/review/publication dependency. It never creates
  a research service, reads source files, loads indexes or writes approval events.
- Response schema requires synthetic_demo, fixed server text and empty citations.
- Existing /api/chat authentication is unchanged. Demo availability never changes
  /api/ready or corpus approval. Existing research response contracts remain intact.
- The public endpoint deliberately has no privileged bearer authentication. Only
  its synthetic capability is public. It has a global cap of ten attempts per
  minute per process, shared two-request concurrency, 16,000 streamed body bytes,
  ten-second body deadline and ten-second demo handler deadline. Groq HTTP timeout
  is five seconds (including connection), selection budget eight seconds.
- The global rate cap includes malformed requests; it does not trust client IP or
  forwarded headers. Keep one worker. This small demo can be exhausted by visitors;
  it is not distributed denial-of-service protection or a general provider proxy.
- Production browser Origins must exactly match KANOON_ALLOWED_ORIGINS. CORS is
  not authentication: non-browser clients may call this intentionally public API.
  Local-only HTTP loopback callers are accepted only outside production.
- No server conversation persistence; demo sends no history. Browser messages stay
  in memory until cleared/reloaded; research retains its existing six-turn policy.

## Voice acceptance (real hardware pending)

Browser speech is reused without auto-submission. Explicit consent enables
Dictate question; transcription only fills the draft. Check microphone permission
allow/deny, start, stop, cancel, accuracy and no automatic POST. Read aloud must
include the synthetic disclaimer and support Stop reading. Clear/mode switch
stops voice controls. Unsupported APIs leave typing and full response text usable.
Check a real mobile browser on HTTPS or localhost. Browser speech providers may
receive audio/text; native audio quality and microphone behaviour are not proven
by mocked speech tests or mobile viewport emulation.

## Verification commands

From the repository root:

```powershell
$testTemp = Join-Path $env:TEMP ('bcai-demo-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp $testTemp
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run typecheck
$env:VITE_API_BASE_URL = 'https://better-call-ai-api.onrender.com'
npm.cmd --prefix frontend run build:hosted
node --test frontend/tests/provider-guard.test.mjs frontend/tests/hosted-env.test.mjs
```

The new browser harness uses the explicit loopback no-corpus demo test server and
headless installed Chrome/CDP, not a real microphone. Use two test terminals:

```powershell
# Backend test terminal, loopback only. This fixture sets local/public mode.
$env:DEMO_ENABLED='true'; $env:DEMO_PROVIDER='deterministic'
.\.venv\Scripts\python.exe -B -m uvicorn backend.tests.demo_e2e_server:app --host 127.0.0.1 --port 8021 --no-access-log
# Separate frontend test terminal: same root; omit VITE_API_BASE_URL.
Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
$env:KANOON_BACKEND_PORT='8021'
npm.cmd --prefix frontend run dev -- --port 5191
# Third test terminal, after both servers are running:
$env:PUBLIC_E2E_BACKEND_URL='http://127.0.0.1:8021'
$env:PUBLIC_E2E_FRONTEND_URL='http://127.0.0.1:5191'
node frontend/tests/public-runtime.mjs --pending-publication
node frontend/tests/demo-browser.mjs
node frontend/tests/demo-browser.mjs --no-speech
```

The demo browser fixture uses local/public mode so the normal loopback Vite
proxy works without weakening production HTTPS-origin restrictions. Production
authentication, CORS and publication denial are exercised in backend tests.
Provider calls are disabled. Rate-limit/error and cancellation UI checks use CDP
interception; separate backend tests exercise actual server limits, deadlines,
provider transport, invalid output and public/private isolation. Results go only
to ignored frontend/.qa. No cloud configuration is changed by these commands.

The runtime source inventory adds only backend/chat/demo.py (42 files total).
It still excludes private source PDFs, processed corpus, indexes, approvals,
audit archives and diagnostics. No candidate corpus is published by this feature.

## Verification recorded 2026-11-14

- Final complete backend suite: 365 passed in 392.57 seconds, including all 32
  new demo tests. One existing Starlette/HTTPX TestClient deprecation warning.
- Frontend lint, TypeScript and hosted production build: PASS. Hosted build used
  the actual configured Render HTTPS origin; no deployment was performed.
- Existing Node environment/provider guards: 10 passed.
- Installed headless Chrome: 6 existing no-corpus checks, 10 synthetic voice demo
  checks and 9 unsupported-speech demo checks passed. Zero research POSTs and no
  Authorization header on demo requests. Real microphone/audio and live Groq
  were not tested; Groq key/model were absent in this execution environment.
- Isolated 42-file minimal-runtime source package: demo and health 200, research
  readiness 503, unauthenticated research 401 and authorised no-corpus research
  503. No private corpus, review or ML dependencies loaded.
- 179 protected file hashes unchanged. Six source PDFs and six processed records,
  404 pages and all 555 archival selections remained mechanically bound. This
  does not certify visual accuracy, current law or legal applicability.
- Both audit chains PASS; zero real events/submissions/approvals and empty
  verified-evidence allowlists. Publication approval remains absent.
- Existing tests and dependency versions retained; no commit, push or deployment.

The initial focused test run encountered Windows default temporary-directory ACL
errors. Re-running with a fresh explicit --basetemp resolved the environment issue.
Browser harness origin/event-timing issues were corrected without relaxing the
production origin gate. The final checks above passed; native-device acceptance
and optional live Groq remain manual/integration limitations.
