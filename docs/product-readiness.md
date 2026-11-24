# Product readiness and measured evaluation

Status on 24 November 2026: safe incremental changes implemented locally, awaiting
manual acceptance. No commit, push, cloud configuration change or deployment.
The deployed general-information assistant remains separate from corpus-backed research.

## Exact remaining legal-source blockers

The original local bundle already exists; no new legal documents were downloaded.
All six raw PDFs and six processed records (404 pages) still match the protected
baseline. Original acquisition records separately establish byte integrity, printed
document identity and official-host provenance. These do not establish legal
currentness, case applicability, complete visual extraction or cryptographic PDF
signature validity. See the unchanged [acquisition audit](legal-source-acquisition-stage2c.json).

| Local original source | Acquisition identity/provenance | Extraction / evidence / publication |
| --- | --- | --- |
| BNS Act 45/2023 | PASS for acquired original Gazette bytes | PARTIAL / no approved passages / rights review missing |
| BNSS Act 46/2023 | Same scope | PARTIAL / no approved passages / rights review missing |
| BSA Act 47/2023 | Same scope | PARTIAL / no approved passages / rights review missing |
| BNS S.O. 850(E) | Same scope | Complete English paragraph identified; not approved or publication-authorized |
| BNSS S.O. 848(E) | Same scope | Complete English paragraph identified; not approved or publication-authorized |
| BSA S.O. 849(E) | Same scope | Complete English paragraph identified; not approved or publication-authorized |

All six remain quality-PARTIAL, including unresolved Hindi extraction. There are
555 mechanically bound archival selections, not 555 verified provisions. The
existing candidate-specific checks passed their narrow automated span/context
rules, while 152 Act pages remain hard-excluded and page-wide warnings persist.
Prior agent visual sampling covered 12 selections, not the remaining 543. No
human legal-evidence approval is implied. Both audit chains remain PASS with
zero real events and empty evidence allowlists.

The source-sharded candidate-v3 and publication/signature/delivery tooling already
exist. Rights/portal conditions, Act commentary sufficiency and the intended
hosting/cache/download/commercial uses still require source-specific human/legal
resolution. No signed real publication receipt or independent deployment trust
anchors are configured. Government authorship is not assumed to mean public domain.

The three existing English notification paragraphs are a possible *minimal review
candidate*, not an approved public corpus. A real authorized reviewer must inspect
wording/context/QA and resolve rights before issuing a source-specific signed
publication decision. Legal-passage approval is separate. Do not manufacture keys,
reviewers or receipts, copy candidate-v3 into production, or create a duplicate
candidate merely to avoid these decisions. Existing source-hash and delivery gates
must accept the exact authorized subset before public retrieval can be enabled.

BNS's original exception concerns its provision in section 106(2); BNSS's concerns
the First Schedule entry relating to that provision. They are not interchangeable.
Neither original enactment nor commencement text proves the present legal position.
See [publication review](publication-review.md), [public runtime/delivery](public-corpus-deployment.md),
and [versioned evidence bindings](evidence-migration.md). Historical provider/deployment
blockers in older reports do not override the subsequently working AI release.

## Existing retrieval reused, not rebuilt

Read-only local BM25 initialization still loads **555** selections: 204 BNS Act,
259 BNSS Act, 89 BSA Act, and three notification paragraphs. Source bindings and
exclusion gates remain active. This is unapproved local archival capability,
not authorized public evidence. No new index or corpus artifact was created.

Optional local Sentence Transformers/FAISS/RRF integration already exists, uses an
explicit local model and preserves BM25 fallback. It was not redownloaded or newly
benchmarked here. Public runtime remains BM25-only and fails closed without the
approved package, receipt, pins and signer. No approved-public retrieval relevance
metric can honestly be reported because there is no approved public corpus.

## Tangible product changes

- Three official portal navigation links: [India Code](https://indiacode.gov.in/),
  [Supreme Court of India](https://www.sci.gov.in/), and [NALSA](https://nalsa.gov.in/).
  Verified HTTPS GETs returned 200 with the expected portal titles at the recorded
  timestamps on 24 November. Redirects were restricted to known official hosts,
  with timeouts and a 2 MiB HTML cap. eGazette About Us was not added because the
  browsing check timed out; no accessibility claim is fabricated for it.
- `GET /api/references` returns reviewed navigation metadata only. The UI shows
  dates and scope, rejects unknown URLs, handles loading/errors and retries. The
  model receives none of this directory, and links are never presented as citations
  supporting an answer. Portal accessibility is not document authenticity or currentness.
- Explicit consent-based **Save on this device**, **Restore saved conversation**,
  and **Delete saved copy**. One AI/synthetic conversation, at most 40 bounded
  alternating messages, is stored as versioned plain text on the current origin.
  No automatic persistence, restoration or model transmission. Research result
  objects, credentials, source/citation records and approval metadata are excluded.
- Restore clears the current conversation/draft and labels restored text unverified.
  Only a subsequent explicit question sends at most six restored messages as untrusted
  context. Corrupt/oversized data, system roles, unknown versions and authority metadata
  are rejected. React escapes stored markup; no HTML is executed.
- Storage is unencrypted and readable by this browser profile/site scripts. Do not
  save confidential details. Clear/reload removes active chat only; saved copies persist
  until explicitly deleted or browser site data is cleared. Browser storage failures
  do not crash chat. Voice, cancellation, retry and existing responsive styling are retained.

## Actual evaluation, without invented accuracy claims

The runnable [six-case set](evaluation-general-information.json) covers mediation,
a contextual arbitration follow-up, consumer concepts, unknowable recent changes,
unsupported verified citations and a fictional personal-arrest question.
[Machine-readable results](product-evaluation-results.json) contain only aggregate
measurements/checks; generated answer text stays in ignored local QA reports.

- Five real Groq-generated responses and one server-authored high-stakes boundary;
  all six returned HTTP 200 with empty citations, unverified labels and unknown currentness.
- Three of three topic-term smoke checks passed. These are lexical checks, not
  independent expert relevance or legal-accuracy judgments. Follow-up used the actual
  preceding answer as bounded context. Two uncertainty/citation-refusal cases and
  one personalized safety boundary were observed; no official citations were invented.
- Initial automatic classification was **5/6** because a curly apostrophe in an
  explicit “I don’t have the ability to verify” refusal was not recognized. The
  evaluator was fixed with positive and negative regression tests. A separate
  reassessment of the same unchanged responses is **6/6**, with **zero additional
  provider requests**. The original report remains unchanged and hash-referenced.
- For the five generated local HTTP requests only: median **1192.43 ms**, maximum
  **1392.31 ms**. Tiny single-run observations, not an SLA, throughput result or
  guarantee of production/cold-start performance. Legal correctness was not verified.

The evaluation supplements, rather than replaces, failure/timeout/rate-limit,
source-isolation and citation-guard tests. Approved-public retrieval evaluation
is explicitly BLOCKED, not counted as a passing relevance test.

## Verification and reproduction

- Full backend suite: **437 passed**, one existing Starlette/HTTPX deprecation warning.
- Frontend lint, TypeScript and hosted production build: PASS.
- Node storage/provider/configuration guards: **27 passed**.
- Chrome recorded checks: **61 passed** (6 pending-publication, 19 deterministic
  demo, 24 AI/storage/reference/mock-voice and 12 unsupported-speech checks).
  No research POST or privileged bearer exposure. New navigation timing/cancelled
  interception races were fixed in the harness without removing safety assertions.
- Isolated **46-file public runtime source package** passed health, reference, AI
  and demo checks with synthetic transport; research remained 401/503 and no private
  evidence or ML dependencies were present. No corpus was packaged.
- All **179 protected hashes unchanged**, six raw/processed records and 404 pages
  accounted for; both audit chains PASS, no evidence/publication decisions written.
- Production read-only checks: health 200, AI enabled/available, research readiness
  503 (`publication_pending`). No production provider request or configuration change.

```powershell
$testTemp = Join-Path $env:TEMP ('bcai-product-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp $testTemp
npm.cmd --prefix frontend run lint
npm.cmd --prefix frontend run typecheck
$env:VITE_API_BASE_URL = 'https://better-call-ai-api.onrender.com'
npm.cmd --prefix frontend run build:hosted
node --experimental-strip-types --test frontend/tests/conversation-storage.test.mjs frontend/tests/provider-guard.test.mjs frontend/tests/hosted-env.test.mjs
# Optional live evaluation: six attempts against an already configured loopback backend.
# Respect rate limits; output must be new and remains ignored. This spends provider quota.
.\.venv\Scripts\python.exe -B -m backend.evaluation --base-url http://127.0.0.1:8000 --output ('backend/data/qa/product-' + [guid]::NewGuid().ToString('N') + '.json')
```

Browser fixtures/commands remain in [the AI guide](general-assistant.md) and
[synthetic/browser guide](synthetic-demo.md). Use `backend.tests.assistant_e2e_server:app`
for the expanded harness; it uses synthetic transport and the reference endpoint.
Do not run a synthetic test fixture as a production entry point.

## Deployment requirements and exact manual acceptance

No new services, dependencies or environment variables. After separate commit/push
and deployment approval, deploy the reviewed code to the existing Render backend
and Vercel frontend. Keep the [AI production variables](general-assistant.md), exact
CORS origin, one worker, public/BM25 mode and corpus/signing/approval configuration
absent. `VITE_API_BASE_URL` stays the existing Render HTTPS origin. The explicit
runtime source inventory now includes the new reference module and storage UI.
Local/private evidence, model files, QA reports and generated assets remain excluded.

To test locally, restart the backend in the credential-configured terminal with the
existing public/BM25/no-corpus settings and run Vite with `KANOON_BACKEND_PORT` matching
its port. Do not stop unrelated processes. No provider key is needed for storage or
reference metadata, but a working AI conversation needs backend Groq configuration.

For the existing local setup, stop only your backend with Ctrl+C in its credentialed
terminal, preserve the key and public/no-corpus environment, and restart:

```powershell
.\.venv\Scripts\python.exe -B -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

Keep the existing frontend at **http://127.0.0.1:5173/** pointed to backend 8000.
Do not launch a second Vite process if it is already running. Check
**http://127.0.0.1:8000/api/references** returns three links and
**http://127.0.0.1:8000/api/ready** remains 503 before browser acceptance.

1. Refresh, confirm publication pending, enter AI mode and ask a conceptual question
   and follow-up; verify unverified labels and no answer citation cards.
2. Check three Official reference portals links, dates and scope; open one and confirm
   the official HTTPS destination. Links do not mean the model read their contents.
3. Expand Save or restore; confirm saving is disabled until explicit consent. Save
   a completed non-confidential exchange; no access token should be requested.
4. Reload: no auto-restore or provider call. Explicitly Restore; check the unverified
   local-text badge, then send a follow-up only if you want restored text sent as context.
5. Clear current chat: saved copy remains. Delete saved copy, reload and try Restore:
   it should report no saved conversation. Do not assume storage is encrypted or shared
   between localhost, preview and production origins.
6. Try denied/full browser storage; chat must remain usable and storage errors clear.
7. Exercise dictation consent/permission, stop/cancel, no auto-send, read-aloud/stop,
   and a real phone. Voice automation mocks APIs; this update needs manual acceptance.
8. Recheck readiness/submission blocked, synthetic fallback, provider error/retry,
   keyboard controls, 320px layout and no horizontal overflow.

Full public corpus activation is still blocked by human/legal decisions, not missing
retrieval engineering. This update does not resolve or bypass that blocker.
