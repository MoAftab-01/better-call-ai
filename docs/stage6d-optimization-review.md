# Stage 6D: offline retrieval optimization and review readiness

This work is offline-only. It does not activate public research, approve evidence, clear redistribution rights or establish current law. No application, frontend, provider, deployment or approval implementation is changed.

## Measured bottleneck and scope

The initial three-development-query profile spent 9.4263 seconds overall (profiler overhead included). BM25 scoring accounted for 0.0140 seconds across five searches. There were 1,551 file reads and 35,264 file-stat calls: repeated pin checks, source reads, parsing and path validation dominated. Source preflight, clause collection and citation checks overlap and their cumulative times must not be added. The initial BM25 index build took 2.2837 seconds. This profile is diagnostic, not a cold/warm performance comparison.

Stage 6D therefore adds `backend/retrieval/optimized.py`, an opt-in wrapper around the **unchanged** Stage 6C sufficiency, matching, ranking, diversity, exclusion and citation rules. It reuses parsed source records only inside one assessment. There is no cross-request result, source-authority, review-decision or approval cache. Existing BM25 and cached semantic indexes are shared as before; no new model, vector store or retrieval service is introduced.

At request start, the original loader/pin/migration validation and review replay run, and each source document passes the original full byte/hash/schema/page validation. The request-local catalogue then avoids repeating the same source parsing for every candidate and citation. Every existing loader boundary reloads current trust metadata and replays the review ledger. After citation validation, all raw and processed bytes are read and SHA-256 checked again; source membership/metadata and the review checkpoint must still match. Any change fails closed with no selected evidence. File modification times are never trusted as hash substitutes. The view is cleared and expires on return.

The source view accepts at most 16 documents and 64 MiB of serialized parsed-source content. These are content bounds, **not** a measured RSS guarantee; original bounded file readers and candidate/character limits also remain. Concurrent offline assessments have independent views. This cooperative filesystem design is not WORM storage or protection against an administrator who tampers and restores state between checks. It is not a public authorization API.

## Evaluation methodology

The original 30 questions and separate 31 Stage 6C cases remain byte-exact. `stage6d.py` runs the unchanged Stage 6C `EvidenceRetriever` as the baseline, not the older extractive engine. Paired runs share one index/model and alternate execution order. Both timings include source checking, sufficiency and citation handoff. Ranking/status/temporal class/selected-ID/group/source-date parity is checked per pair. Absolute timings are not comparable with older Stage 6C latency figures, which excluded evaluation citation validation.

`stage6d-heldout.json` contains 20 new source-first questions (8 provisional positives, 12 negatives), including four newly bound archival passage topics, temporal wording, mixed instruments, distractors, missing qualifications and incorrect provenance. Labels were authored from source text **before any query retrieval**; private freeze markers record dataset and implementation hashes. The same agent authored these labels: they are separately authored questions, **not independent expert ground truth**. All labels require human review. No semantic, temporal or ranking changes are permitted after observing held-out results. Failures below are retained, not relabelled or tuned away.

Retrieval metrics score historical positive cases separately from sufficiency decisions. For comparability with Stage 6C, paired scoring treats each required passage as equal grade 2; it does not overwrite the original graded dataset. MRR is truncated at five. Required-document coverage alone cannot prove complete passage coverage or entailment. False-supported-decision rate is relative to provisional labels, with supported evidence decisions as denominator; no generated answers or legal truth are evaluated. Citation checks establish exact source/quote/context/provenance binding, not visual correctness or legal currentness.

Quality runs measure each case once per system and mode. A separate warm run repeats six fixed DEVELOPMENT cases three times; held-out results are never used to select timing questions or tune policy. Cold runs use separate Python processes, reuse only the installed cached model, and separately report index/model build and first-query time. OS caches are not flushed; Python/module import time is excluded. This is one workstation, not a deployment SLA or broad hardware benchmark.

## Verification and preservation

The complete backend suite passed **650 tests in 240.56 seconds**, including 26 new synthetic-only Stage 6D tests. One existing Starlette/HTTPX TestClient deprecation warning remains. An initial targeted run exposed a fault-wrapper copying recursion (22 passed, 1 failed); that implementation defect was fixed before freezing or querying the holdout. The corrected targeted run passed all 23 then-existing tests; three additional evaluation/fault tests passed in the full suite. No assertion or previous policy was weakened.

Coverage includes exact rank/decision parity, same-size/mtime-preserving source tampering, stale QA, changed review checkpoint, mid-request source edits, cache bounds and expiration, missing sources, altered quotations/qualifiers/hashes/source URLs, fault-wrapper preservation and shared hybrid-ranker behavior. Existing citation, provider, public-runtime isolation and publication fail-closed regressions are included in the full suite. No paid provider calls or model downloads are used by this work.

The 179 protected hashes, 10 prior Stage 6 source/documentation files and 38 prior QA artifacts matched their pre-work baselines. Both review chains passed at sequence zero with zero events/approvals and empty allowlists. Final preservation checks are recorded in the private verification report. Six original PDFs, six processed records and 404 physical pages remain required for real-source evaluation. Source bytes and earlier packets/workbooks are not rewritten.

Read-only, TLS-verified hosted checks returned `/api/health` 200 and `/api/ready` 503 with `corpus_available=false`, `research_ready=false` and `legal_currentness=unknown`. The first restricted-network attempt could not connect; an authorized read-only network retry succeeded. No hosted configuration, provider inference, deployment or publication action occurred. Production source/configuration files and the runtime inventory remain unchanged; these offline modules are not added to the runtime package. Frontend files are untouched, so frontend/browser checks were not rerun for this backend-only offline stage.

## Human-review handoff

A new private `backend/data/qa/stage6d-20261128/human-review-workbook-v2.md` and JSON companion preserve the earlier workbook while expanding the handoff. Each notification binds the raw PDF, processed JSON, proposal, physical page/normalized lines, exact text/context and original render hashes. Automated extraction checks, previous agent visual observations and pending human verification are distinct. No new visual certification is claimed.

For BNS S.O. 850(E), retain the original section 106(2) provision exception. For BNSS S.O. 848(E), retain the First Schedule **entry** relating to that BNS provision; do not substitute a BNSS provision exception. Do not import either carve-out into BSA S.O. 849(E). Heading and publication dates remain separate. Hindi glyph mapping and bilingual correctness remain unresolved.

The workbook asks source-specific questions about the existing conditional rights dossier, portal/contract terms, excerpt/context delivery, commercial hosting, persistent caching, downloads and possible permission requirements. Acts and non-Act Gazette notifications require separate analysis; government origin, commentary or an ELIGIBLE recommendation does not clear publication. All inclusion/exclusion proposals are blank. No reviewer identity, decision, signature, key, receipt or approval event is created. Legal-evidence approval, publication authorization and present-law verification remain separate human blockers.

See [Stage 6A/6B](stage6-legal-rag-evaluation.md), [Stage 6C](stage6c-evidence-sufficiency.md), [rights review](publication-review.md), [public corpus controls](public-corpus-deployment.md) and [evidence bindings](evidence-migration.md). Exact passages, render images and diagnostic reports remain in ignored local storage.

## Reproduction

Use the existing environment and exact private source/processed bundle. Missing private evidence must block real-source measurements. The held-out run also requires the original private freeze marker under `backend/data/qa/stage6d-20261128/`; do not regenerate it after changing labels. Public checkouts can run the synthetic tests without publishing the archival corpus. Choose new output names: existing outputs are never overwritten.

```powershell
$tag = [guid]::NewGuid().ToString('N').Substring(0,8)
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp (Join-Path $env:TEMP "bcai-6d-$tag")
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6d --mode bm25 --output "backend/data/qa/stage6d-bm25-$tag.json"

# Optional EXISTING cached data-only model; never download a replacement:
$modelPath = Read-Host 'Existing cached embedding snapshot directory'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6d --mode both --model-path $modelPath --output "backend/data/qa/stage6d-paired-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6d --mode both --dataset frozen --timing-only --model-path $modelPath --output "backend/data/qa/stage6d-warm-$tag.json"

# Run each combination separately in a fresh Python process:
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6d --mode bm25 --cold-system stage6c --output "backend/data/qa/stage6d-cold-c-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6d --mode bm25 --cold-system stage6d --output "backend/data/qa/stage6d-cold-d-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6d --mode hybrid --model-path $modelPath --cold-system stage6c --output "backend/data/qa/stage6d-cold-hc-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6d --mode hybrid --model-path $modelPath --cold-system stage6d --output "backend/data/qa/stage6d-cold-hd-$tag.json"

.\.venv\Scripts\python.exe -B -m backend.review verify
.\.venv\Scripts\python.exe -B -m backend.publication verify
.\.venv\Scripts\python.exe -B -m backend.review allowlist
.\.venv\Scripts\python.exe -B -m backend.publication allowlist
Get-Content backend/data/qa/stage6d-20261128/human-review-workbook-v2.md
```

Numerical results and explicit residual failures follow after the measured runs.

## Paired quality and latency results

All **162 case/mode pairs (324 assessments)** matched in ranking and sufficiency metadata. Dataset files and semantic policy were unchanged. The cached model fingerprint remained `203a93edf7735ba9b7f73ca1f617b1e1ceaf8bf840e26ce9b73abf6456a15314`. Shared-run initialization took 2.291 seconds for BM25 and 23.982 seconds for the cached semantic model/index. These are not cold-process measurements.

Warm-process quality sweep, one timing per case/system/mode; milliseconds, citation validation included:

| Dataset | Mode | Stage 6C median / p95 | Stage 6D median / p95 | Median change | p95 change |
| --- | --- | ---: | ---: | ---: | ---: |
| frozen | bm25 | 2082.8 / 5648.2 | 1906.0 / 2361.4 | -8.5% | -58.2% |
| frozen | hybrid | 1918.8 / 5251.2 | 1780.8 / 2309.1 | -7.2% | -56.0% |
| stage6c | bm25 | 1815.7 / 4021.9 | 2052.8 / 2419.0 | +13.1% | -39.9% |
| stage6c | hybrid | 1688.9 / 3826.5 | 1863.9 / 2231.7 | +10.4% | -41.7% |
| heldout | bm25 | 3102.0 / 3866.9 | 1870.8 / 2327.7 | -39.7% | -39.8% |
| heldout | hybrid | 3196.2 / 4984.4 | 2004.0 / 2945.4 | -37.3% | -40.9% |

The tail improved in every measured group, but the Stage 6C negative-heavy set had a **median regression**. Request-wide fresh source/trust handoff adds work when few candidates/citations would otherwise be validated. This wrapper is not a universal latency improvement and is not enabled in production. These small local samples do not support an SLA or an interview claim of general retrieval accuracy.

Ranking/coverage metrics are identical within each Stage 6C/6D pair:

| Dataset | Mode | Positive cases | Recall@3 | Recall@5 | MRR@5 | nDCG@5 | Required-doc coverage |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| frozen | bm25 | 21 | 1.0000 | 1.0000 | 0.9762 | 0.9786 | 1.0000 |
| frozen | hybrid | 21 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| stage6c | bm25 | 10 | 1.0000 | 1.0000 | 1.0000 | 0.9920 | 1.0000 |
| stage6c | hybrid | 10 | 1.0000 | 1.0000 | 0.9500 | 0.9631 | 1.0000 |
| heldout | bm25 | 8 | 0.2500 | 0.2500 | 0.3750 | 0.2783 | 0.2500 |
| heldout | hybrid | 8 | 0.2500 | 0.2500 | 0.3750 | 0.2783 | 0.2500 |

| Dataset (both modes) | Temporal classification | Temporal safe refusals | Negative abstention | Exact status | False supported / supported decisions |
| --- | ---: | ---: | ---: | ---: | ---: |
| frozen | 100.00% | 100.00% | 100.00% | 100.00% | 0 / 21 |
| stage6c | 100.00% | 100.00% | 100.00% | 100.00% | 0 / 10 |
| heldout | 69.23% | 60.00% | 83.33% | 40.00% | 2 / 2 |

The paired sweep validated **312 citation occurrences** with zero accepted citation-binding mismatches. It produced **20 expected source-integrity rejections** across both systems and modes (the same three frozen Stage 6C faults and two new held-out faults repeated per system/mode). Citation integrity does not excuse a wrong sufficiency decision. Diagnostic ranked passages may be validated even when final evidence selection is withheld.

### Untuned held-out failures

Both BM25 and hybrid show the same label-relative weaknesses. All eight provisional historical positives fail final sufficiency; some required passages are still found, explaining Recall@5 of 0.25 rather than zero. Broad new wording, English word forms and additional framing terms can defeat fixed lexical anchor/coverage thresholds. The BSA museum question explicitly says it is not a statement of present legal position, but the conservative temporal pattern still catches the word ?present?. These explanations describe observed heuristics, not an expert adjudication of labels.

| Case | Expected | Actual (both modes/systems) | False-supported decision |
| --- | --- | --- | --- |
| `signed-statement-training-card` | `historical_evidence_available` | `insufficient_evidence` | No |
| `warehouse-mark-history` | `historical_evidence_available` | `insufficient_evidence` | No |
| `procedural-clock-audit` | `historical_evidence_available` | `insufficient_evidence` | No |
| `unavailable-speaker-credit` | `historical_evidence_available` | `insufficient_evidence` | No |
| `two-unrelated-training-cards` | `historical_evidence_available` | `insufficient_evidence` | No |
| `time-versus-knowledge-file` | `historical_evidence_available` | `insufficient_evidence` | No |
| `conflated-bns-index` | `historical_evidence_available` | `insufficient_evidence` | No |
| `bsa-museum-card` | `historical_evidence_available` | `insufficient_current_evidence` | No |
| `superseded-exception` | `insufficient_current_evidence` | `historical_evidence_available` | YES |
| `fresh-order-question` | `insufficient_current_evidence` | `historical_evidence_available` | YES |
| `next-month-burden` | `insufficient_current_evidence` | `insufficient_evidence` | No |
| `legacy-numbering-shortcut` | `insufficient_evidence` | `clarification_required` | No |

The two false-supported cases are:

- ?Has anything superseded the BNS commencement exception??
- ?Has a fresh Gazette order removed the BNS commencement exception??

These phrases imply later developments without matching the existing temporal vocabulary. The archive cannot prove the requested later position. Both systems nevertheless return `historical_evidence_available`; the output still declares currentness unknown and no approval, but this is a sufficiency-classification defect relative to the frozen expectations. **2/2 supported decisions are false-supported (100% proxy), or 2/20 held-out cases (10% of all cases).** No answers were generated, so neither figure is a measured legal-answer hallucination rate. Ten of twelve negatives abstain; the other two are these failures. Temporal safe refusal is 3/5 and temporal class accuracy 9/13. Exact status matches are 8/20.

The missing-qualification and wrong-source-URL probes both fail closed in both systems/modes. They perturb in-memory candidates only. Source bytes, questions and labels are not changed. No holdout-derived fixes are made here: a future separately reviewed semantic/temporal revision needs another untouched evaluation set and independently reviewed labels.

Original datasets remain SHA-256 `f4fd962a805a41cd7b642c7f05a2c1dd45deff5ac1aeb264cd225eeeeb3693f1` (30), `0bba841b65898e48aeb2c39ffd9e1d8e234440a71e1cc5c421b64f5affe4fc86` (31); heldout SHA-256 `79c1a8e38b5c773d1f7252d67c1346c80e70a13c82dff58376132aab7912946e` (20). Private full rows and timings: `backend/data/qa/stage6d-20261128/paired-comparison.json`.

## Repeated warm measurements

Six fixed development question IDs, three repetitions each per system/mode (18 samples per row, 36 matched pairs overall). The six IDs are `bns-judicial-power`, `bns-compelled-movement`, `bsa-alive-dead`, `bnss-entry-carve-out`, `consumer-outside-archive`, `unverified-subsection`. This is a small development timing sample, not an extra holdout accuracy result. The nearest-rank p95 is the maximum of 18 samples.

| Mode | System | Samples | Median ms | p95 ms |
| --- | --- | ---: | ---: | ---: |
| bm25 | stage6c | 18 | 1942.9 | 4160.6 |
| bm25 | stage6d | 18 | 1733.4 | 1925.8 |
| hybrid | stage6c | 18 | 1901.5 | 3923.6 |
| hybrid | stage6d | 18 | 1743.5 | 2413.3 |

Full repeated rows: `backend/data/qa/stage6d-20261128/warm-repeated.json`. The four historical positives and two negatives do not represent every production workload; do not generalize the median improvement to the negative-heavy Stage 6C set.

## Fresh-process startup and component profiles

One fresh process per system/mode, same fixed cross-document development question; OS caches retained, Python/module imports excluded. Initialization is separate from the first query. No cold-run median/p95 is claimed from one observation. Model/index build variation is not attributed to Stage 6D because that implementation is unchanged.

| Mode | System | BM25 build s | Semantic build s | First query s |
| --- | --- | ---: | ---: | ---: |
| bm25 | stage6c | 2.243 | not loaded | 3.220 |
| bm25 | stage6d | 2.538 | not loaded | 2.127 |
| hybrid | stage6c | 2.569 | 24.706 | 3.342 |
| hybrid | stage6d | 2.358 | 22.178 | 2.331 |

Fresh paired profiling (three development queries, six lexical searches per system/mode, profiler overhead included):

| Mode | System | Total s | Source-document validation s (calls) | BM25 s | Query embedding s | FAISS s | Clause collection + aggregation s | Citation handoff s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | stage6c | 6.5646 | 4.6087 (46) | 0.0114 | 0.0000 | 0.000000 | 2.7105 | 1.2351 |
| bm25 | stage6d | 5.8939 | 1.8349 (18) | 0.0119 | 0.0000 | 0.000000 | 1.1822 | 0.0074 |
| hybrid | stage6c | 6.4405 | 4.5203 (46) | 0.0115 | 0.0630 | 0.000665 | 2.7905 | 1.1987 |
| hybrid | stage6d | 5.8112 | 1.7753 (18) | 0.0108 | 0.0558 | 0.000614 | 1.1328 | 0.0073 |

Cumulative categories overlap; **do not add the columns**. Snapshot initialization and final fresh-byte/trust checks are included in total time, outside the Stage 6C `_sources`/citation timers. Smaller phase times partly reflect moving repeated validation into a single request preflight; they are not proof that equivalent security work disappeared. Baseline citation timing wraps the whole citation loop; optimized timing wraps formatting plus validation. Both total measurements include the same citation obligation plus the optimized fresh handoff.

Exclusive profiler counters reduced file reads from 1,535 to 1,404 and `nt.stat` calls from 34,854 to 31,761 for these three queries. Mutable pin/migration reloads and safe path/hash checks remain the dominant cost; BM25, embeddings and FAISS are not the bottleneck. No attempt was made to cache trust/approval decisions or relax source checks to remove that cost.

Environment: Windows AMD64, Python 3.12.10, 20 logical CPUs reported; the existing semantic implementation sets PyTorch/FAISS to two threads. CPU SKU/physical RAM queries were denied by the restricted CIM interface and were not assumed. Background workload, antivirus, filesystem cache and power state were not controlled. Reports are same-workstation measurements, not statistically isolated deployment guarantees.

Profiles and cold records are under `backend/data/qa/stage6d-20261128/`. The ignored `profile-run.py` records the exact profiling instrumentation; run it from the repository root with offline model environment flags, for example `Get-Content -Raw backend/data/qa/stage6d-20261128/profile-run.py | .\.venv\Scripts\python.exe -B -`, after choosing a new output destination in that private script. It never edits an application source. The original pre-optimization profile is preserved.

## Original Stage 6A/6B benchmark rerun

The unchanged original `backend.retrieval.offline` CLI was also run with its original graded labels and one repetition per question/mode. This tests the older extractive engine; it is **not** the Stage 6C sufficiency baseline used in the paired comparison. Its timing excludes citation checks and cannot be compared directly with the paired wrapper timing.

| Original engine | Recall@3 | Recall@5 | MRR@5 | nDCG@5 | Insufficient-case abstention | Citation checks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.9286 | 0.9286 | 0.9048 | 0.8950 | 0.8889 | 72/72 |
| hybrid | 0.9524 | 0.9524 | 0.9286 | 0.9310 | 0.8889 | 72/72 |

The original cross-document/temporal limitations remain visible in that older engine; no historical results or original labels were rewritten. Full original rows are in `backend/data/qa/stage6d-20261128/original-stage6ab-benchmark.json`.

## Final repository and preservation checks

- Branch `feat/working-legal-chat-mvp`; HEAD `547c32f821aa55d251044006c6d86679eccbe87e` unchanged. Index empty; no tracked changes. There are ten preserved earlier untracked Stage 6A/B/C files plus five new Stage 6D files.
- All 179 protected hashes match; all ten earlier Stage 6 source/docs and 38 prior artifacts match their pre-work hashes. All four frozen Stage 6D implementation/dataset/test hashes still match after evaluation. Six original PDFs remain read-only; each raw/processed page count matches, totaling 404. The original index still contains 555 archival selections.
- Both real chains PASS at sequence zero; zero submissions, events, approvals or allowlist entries. No publication authorization or human legal review is created.
- All 47 runtime paths retain HEAD-equivalent contents and the runtime inventory is unchanged. **44 match exact Git blob bytes.** Three frontend files (`frontend/src/chat.ts`, `frontend/src/components/SourcePanel.tsx`, `frontend/src/styles.css`) differ from Git blobs solely by CRLF versus LF. `core.autocrlf=true`; no text/eol/filter attributes override those paths, and Git reports no tracked modifications. They were not edited in this task. A pre-work raw-byte baseline for these three files is unavailable, so this comparison is not claimed as proof of their historical byte preservation. No normalization or repair was performed.
- No new offline files occur in the runtime inventory. The Stage 6D diagnostic directory is ignored by the repository-local rules. The restricted account warns that it cannot read the user-global Git ignore file; local ignore checks still pass and no settings were changed.
- New-file scans found no credential/private-key patterns or local absolute workstation paths. No private corpus, PDFs, processed records, reviewer artifacts or benchmark extracts were added to tracked publication paths. Local documentation links resolve; `git diff --check` passes. No commit, push, download, paid provider evaluation, frontend change, cloud mutation or deployment occurred.

### New files

1. `backend/retrieval/optimized.py` ? request-local source reuse and fresh handoff validation.
2. `backend/retrieval/stage6d.py` ? paired quality/warm/cold evaluator and held-out fault probes.
3. `backend/retrieval/stage6d-heldout.json` ? frozen 20-case provisional source-bound set.
4. `backend/tests/test_stage6d_optimization.py` ? 26 synthetic-only regression tests.
5. `docs/stage6d-optimization-review.md` ? methodology, measurements, failures and handoff.

New private artifacts are under `backend/data/qa/stage6d-20261128/`: baseline/freeze manifests, test results, paired and repeated-warm rows, four cold observations, component profiles, original Stage 6A/B rerun, the blank-decision human-review workbook and final verification. Generated pytest fixtures are synthetic and remain ignored. Exact original legal text/renders stay in their existing private locations.

## Recommended scope and manual acceptance

**Local offline optimization and evaluation are complete; public RAG/evidence promotion remain BLOCKED.** Ranking/decision parity and integrity tests pass, but the spent holdout reveals poor lexical generalization and temporal false-supported decisions. The optimization does not fix those policy defects and does not justify research release. Its median regressions also require workload-specific judgment before any integration.

1. Review the latency tables, full failure rows and exact provisional labels before accepting this offline stage. Check that the five new files are the only additions beyond the ten original Stage 6 files; leave all of them uncommitted until separately authorized.
2. Independently inspect the original PDF paragraphs/context, including both distinct commencement exceptions, using the private version-2 workbook. Leave Hindi, rights, applicability and any uncertain source association unresolved until genuinely reviewed.
3. Inspect every new relevance/sufficiency label. Propose corrections in a separate version; do not silently edit the frozen 30/31/20 sets or retroactively call this spent holdout untouched after tuning.
4. Before future policy changes, obtain independently authored/human-reviewed labels and a new untouched evaluation set. Treat superseding-order wording, negation/disclaimers and novel concept framing as known regressions, not proof that a single keyword patch would solve currentness.
5. Any evidence approval and publication authorization must use the separate existing controlled human workflows. No public retrieval integration is permitted from this work alone. No deployment or new environment variable is required for this offline-only stage.

Stop for manual acceptance. Source rights, independent visual/label review, currentness coverage and explicit publication decisions remain human/external blockers.
