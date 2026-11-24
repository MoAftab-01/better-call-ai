# Stage 5: Production reliability and observability

Local verification: 25 November 2026 (Asia/Kolkata). Base: `e3974e820852a557c49b6e57de67520aae6c2eb4`, branch `feat/working-legal-chat-mvp`. No commit, push, deployment, cloud configuration change or paid provider evaluation was performed.

## Existing controls and gaps

The existing application already had the following controls; Stage 5 preserves them.

| Area | Existing behavior |
| --- | --- |
| AI Assistant | Separate public general-information endpoint; Groq only; no retrieval; bounded six-turn history; high-stakes boundary; rejects citation-shaped output; deterministic demo remains separate. |
| Assistant budgets | Global per application/process: 6 attempts/minute and 100 attempts/rolling 24 hours by default. Configurable maxima remain 30/minute and 1,000/day. Rejected invalid requests can consume the attempt budget. |
| Other budgets | Synthetic demo: 10 attempts/minute. Privileged research: 30 requests/minute after access checks. Two shared in-flight chat requests; no per-IP budget. |
| Input bounds | 16,000 streamed body bytes; 2,000-character question; six alternating history messages, 1,200 characters each. Ten-second body-read deadline. |
| Provider bounds | General Groq HTTP timeout 18 seconds, connect timeout 5 seconds, route deadline 22 seconds, maximum completion 768 tokens, maximum response 65,536 bytes; no general-chat retry. Research selection has a bounded retry, 25-second route deadline. Demo selection uses a shorter provider/deadline budget and deterministic fallback. |
| Access/publication | Production research bearer protection, approved public manifest/signature/pins, public/private isolation, explicit CORS origins, no privileged token in the frontend. |
| Public status | Liveness `/api/health`, research readiness `/api/ready`, and separate assistant/demo status. Research readiness 503 while publication is pending is intentional and does not imply AI Assistant downtime. |
| Product tests | Backend/provider/publication/security tests, Node configuration/storage guards and Chrome checks for chat, mocked voice, persistence, references and mobile layouts. |
| Deployment | Render Python 3.12, one worker, no Uvicorn access log; Vercel frontend. Explicit public source package excludes corpus, private archives and ML weights. |

Previously, research had a small string log entry, but the public assistant/demo lacked end-to-end request correlation, structured duration/outcome accounting, returned-token accounting and a restricted operational snapshot. Stage 5 replaces the old research entry with a common operational layer.

## Architecture changes

`backend/chat/telemetry.py` uses only the Python standard library plus the existing Starlette response type. A pure ASGI middleware surrounds CORS, input/authentication guards and routes. Each HTTP request receives a fresh server-generated 32-character hexadecimal `X-Request-ID`, including early rejections; caller-supplied IDs are ignored. CORS exposes this response header to configured browser origins. Responses remain `Cache-Control: no-store`.

Context variables bind provider work to that request, including concurrent tasks and framework thread-pool work. Per-application, lock-protected counters record request status classes, fixed error categories, completed/cancelled/aborted requests, provider outcomes, HTTP attempts/status categories and reported usage. `time.perf_counter()` measures full application response duration and provider-operation duration. Snapshots expose duration count, sum and maximum; they do not invent percentiles.

The logger `better_call_ai.operations` writes compact JSON to stderr. Three event schemas are supported: `request_completed`, `provider_completed` and `provider_usage`. Only fixed keys, validated enumerations and bounded numbers pass the formatter. Unknown routes become `unmatched`, unknown methods become `OTHER`. No request/response object is serialized. An example operational event is:

```json
{"schema_version":1,"event":"request_completed","timestamp":"2026-11-25T00:00:00+00:00","request_id":"0123456789abcdef0123456789abcdef","route":"/api/assistant/chat","method":"POST","status":504,"duration_ms":125.0,"completion":"response","error_code":"provider_timeout"}
```

This is an illustrative schema example, not a production measurement. Provider classifications are `success`, `not_called`, `configuration_error`, `timeout`, `rate_limited`, `unavailable`, `invalid_response`, `cancelled` and `internal_error`. A server-side safety boundary is `not_called`; deterministic demo work has no provider event. Selection retries increment HTTP attempts separately. Deadline cancellations are classified as timeouts; a demo that falls back successfully can still record a timed-out provider operation.

Unexpected pre-header exceptions produce a generic 500 without the exception text. A failure after response headers is recorded as `aborted` and re-raised with a sanitized message; an already-started response cannot be replaced. A failed operational log sink does not change an otherwise valid answer.

Two small reliability fixes accompany instrumentation: the daily-budget `Retry-After` reflects the remaining rolling-day cooldown, and an oversized body chunk is rejected before appending it to the buffer. Existing quotas, concurrency limits, provider timeouts, prompts, output validation and publication decisions are unchanged.

## Usage and cost awareness

Only Groq-returned `prompt_tokens`, `completion_tokens` and `total_tokens` are counted. Each field includes an observation count. Missing fields are not inferred. Integers from zero through 1,000,000,000 are accepted; booleans, negative/fractional/non-finite/oversized values are rejected. Inconsistent complete totals are discarded. Valid fields in otherwise partial/malformed metadata remain explicitly partial/malformed. Missing or malformed usage does not invalidate an otherwise valid answer.

Accounting occurs after a successful provider response is parsed, even if its answer is subsequently rejected. A timeout, non-success HTTP response or unparseable body may have consumed paid resources without supplying usable usage. **Unknown usage is not zero cost.** Totals are provider-reported observations, not an invoice; no pricing, currency estimate or full billing coverage is claimed. Do not add `total_tokens` to prompt plus completion again. Groq documents these usage fields in its [API reference](https://console.groq.com/docs/api-reference).

## Restricted operations interface

`GET /api/ops/metrics` is read-only and omitted from OpenAPI. Hiding it is not the access control.

- In `KANOON_ENV=production`, a valid, separate `KANOON_OPS_TOKEN` is required, even for loopback requests. It must be 32?256 ASCII characters without whitespace and differ from both the research token and Groq key.
- An absent/invalid operations token leaves production metrics closed with 404. A configured token with missing/wrong authorization returns 401. A correct `Authorization: Bearer ...` returns 200. Query-string credentials are not accepted.
- Nonproduction permits direct loopback access without a token only when there is no Authorization, Origin, Forwarded, X-Forwarded-For or X-Real-IP header. Headers cannot grant loopback access. This convenience assumes a trusted local bind; never expose `KANOON_ENV=local` as a public deployment. For local operator access, use Uvicorn `--no-proxy-headers` to retain the actual socket peer.
- Public health, readiness and assistant/demo status responses gain no usage, counters, secrets, filesystem paths or operational configuration. The public request ID is a non-sensitive correlation value.

Only backend operators need the new **optional** variable. Do not put it in `VITE_*`, browser storage, URLs, source control or the research access-token field. No new mandatory environment variables, dependencies or services were introduced. `.env.example` documents the blank optional field. Runtime package inventory adds only the telemetry module.

## Threat model and bounds

The application does **not** log questions, answers, history, saved conversations, source contents, IPs, user agents, raw provider bodies, authorization headers, keys, queries or arbitrary paths. Error messages and provider exceptions are never interpolated into operational logs. Fixed field/value validation also guards accidental future callers of the logger.

Counter labels have fixed cardinality; no per-user/IP/request-ID metric series or latency samples are retained. Integer counters saturate at `2**63 - 1`. At most eight completed provider spans are buffered per request; extra events increment a dropped-event counter. The provider HTTP-attempt summary caps at 16. HTTP response bodies retain the existing size bounds. This bounds in-process telemetry storage, not total web-server/socket memory or externally retained log volume.

These budgets and counters are **in-memory, per application instance in one process**. Restart resets both; multiple workers/replicas have independent limits and totals. They are not durable, distributed quotas or per-user fairness. Global quotas can still be exhausted by another caller. CORS is a browser policy, not authentication against arbitrary HTTP clients. Durable quotas and stronger edge abuse controls require a separately reviewed shared store/ingress policy; no infrastructure was added.

The operations token is a static shared operator secret, not a user identity system. Protect and rotate it through the existing secret manager. External proxies, hosting logs, debug tooling and their retention policies are outside this application formatter; operators must review them separately. Keep Uvicorn access logging disabled as in the current Render command. No local rotating log file or retention service is installed.

## Measured local verification

All provider transports below are synthetic. No claim of new live Groq verification, production latency, cost savings, or real-device microphone verification is made.

| Check | Result |
| --- | --- |
| Complete backend suite | 504 passed; one existing Starlette/HTTPX deprecation warning. |
| New operational test module | 67 passed, covering privacy/schema sanitization, correlation, deterministic duration, all outcome classes, timeouts, usage variants, concurrency, budgets, restart resets, local/production authorization, oversized chunks and log-sink failure. |
| Frontend | Lint, TypeScript and hosted production build passed; Node tests: 27 passed. No frontend source changes. |
| Chrome | 61 completed checks: public no-corpus 6, demo/mock voice 10, demo/unsupported speech 9, assistant/mock voice 24, assistant/unsupported speech 12. Covers follow-ups, cancellation/retry, save/restore/delete, official links, 320px layout, voice controls, zero research submissions and no bearer exposure. Speech hardware/provider responses are mocked. |
| Preservation | All 179 pinned hashes match. Both V1/V2 audit chains PASS, sequence 0 and eligible count 0. No evidence, decisions or approvals changed. |
| Isolated deployment source package | 47 runtime source files plus one generated inventory entry; ZIP hashes verified. Exported into an empty directory and run with the existing minimal runtime environment: no private/ML imports, health/demo/assistant/references 200, readiness 503, research 401/503, authenticated operations 200 and unauthenticated operations 401. No corpus bundled. |

A controlled six-request ASGI smoke test returned success 200, malformed-usage answer 200, provider timeout 504, provider rate limit 429, rejected answer 502 and oversized body 413. It recorded five provider attempts, two successes, one timeout, one rate limit and one invalid response. Three parsed usage observations were two complete and one malformed; accepted synthetic usage totaled **44 prompt + 11 completion = 55 total tokens**, from two valid observations. Active request/provider counters returned to zero. Request duration sum was 25.148 ms, maximum 13.960 ms for this synthetic in-process run; these are not network/provider benchmarks. A separately controlled clock test records exactly **125 ms**. No per-request overhead or production percentile is claimed.

Ignored local results: `backend/data/qa/stage5-final-smoke-a9e2ac0c.json`, `backend/data/qa/stage5-package-5b79ea44.json`, and `frontend/.qa/` browser reports. They are diagnostics, not publication evidence. Source archive: `backend/data/deployment/stage5-5b79ea44.zip`; it has not been published.

## Verification commands

From the repository in PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$testTmp = Join-Path $env:TEMP ('bcai-stage5-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp $testTmp
.\.venv\Scripts\python.exe -B -m backend.review verify
.\.venv\Scripts\python.exe -B -m backend.publication verify

Set-Location frontend
npm.cmd run lint
npm.cmd run typecheck
$env:VITE_API_BASE_URL = 'https://better-call-ai-api.onrender.com'
npm.cmd run build:hosted
node --test tests/*.test.mjs
```

The temporary test directory must be new. These commands do not require a live provider request. Browser automation commands and the consent-based manual voice workflow remain in [the AI Assistant guide](general-assistant.md) and [synthetic demo guide](synthetic-demo.md); use the synthetic test fixture and never target production for automated answer tests.

## Monitoring and deployment implications

No deployment was performed. Keep the existing public/BM25 configuration, one worker, explicit frontend HTTPS CORS origin and `--no-access-log`. Optional production operations access requires securely provisioning a separate `KANOON_OPS_TOKEN` and restarting the backend through the normal reviewed deployment process. Without it, chat and structured logs still work, and production metrics remain unavailable.

For a trusted local server, inspect without credentials:

```powershell
$metrics = Invoke-RestMethod 'http://127.0.0.1:8000/api/ops/metrics'
$metrics.provider_operations
$metrics.request_duration
$metrics.usage_observations
$metrics.reported_tokens
```

For production, read the operator token without echoing or storing it in command history, then query over HTTPS:

```powershell
$opsSecure = Read-Host 'Operations token' -AsSecureString
$opsPlain = [System.Net.NetworkCredential]::new('', $opsSecure).Password
try {
    $opsHeaders = @{ Authorization = 'Bearer ' + $opsPlain }
    $metrics = Invoke-RestMethod 'https://better-call-ai-api.onrender.com/api/ops/metrics' -Headers $opsHeaders
    $metrics.provider_operations
    $metrics.request_duration
    $metrics.usage_observations
    $metrics.reported_tokens
} finally {
    $opsHeaders = $null
    $opsPlain = $null
    $opsSecure = $null
}
```

This requires an explicitly provisioned production token and deployed Stage 5 code; it is not a claim that the current hosted release has this endpoint. Avoid PowerShell transcription/debug sessions that capture secret variables. A snapshot itself counts as an in-flight request and is reflected as completed only in the next snapshot. Compute interval deltas within one process uptime; discard deltas after restart. Monitor provider timeouts/rate limits separately from assistant-budget 429s and expected publication readiness 503s. Watch rising `invalid_response` and unknown/malformed usage observations. Configure any alerts externally only with separate authorization; none were created.

## Manual acceptance checklist

1. In the updated local app, send a normal AI concept question and follow-up; inspect a fresh `X-Request-ID`, safe errors, unverified disclaimer and empty source citations. Inspect only operational fields in stderr, without enabling HTTP/provider debug logging.
2. Check synthetic fallback, microphone permission/start/stop/cancel, dictation without auto-submit, read-aloud, save/restore/delete, official reference links and narrow/mobile layout. Real microphone and device checks remain manual; automated voice tests use browser shims.
3. Verify research remains publication-pending, `/api/ready` is 503, and no private source is exposed. Do not alter corpus approvals or pins.
4. In a local production-configured test instance, verify absent/invalid operations configuration gives 404; configured missing/wrong token gives 401; correct distinct operations token gives 200 with no-store. Research/Groq keys must not authorize metrics. Public endpoints must contain no token/counter data.
5. Compare a known synthetic timeout/rate-limit/rejected response against the corresponding operational categories. Do not generate paid failures or exhaust the production provider budget for this check. If a separately approved live request is made later, count only usage Groq actually returns.
6. Restart a disposable local instance and observe new uptime, zero metrics and reset budgets; do not mistake this for durable accounting. Existing user development servers were not restarted for this task.

See also [public website deployment](public-website-deployment.md), [public corpus deployment](public-corpus-deployment.md) and [evidence migration](evidence-migration.md). Source publication and legal currentness remain unresolved and independently gated.
