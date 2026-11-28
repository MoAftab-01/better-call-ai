# Stage 6F: offline passage retrieval and release readiness

This is a local/offline engineering and evaluation stage. It does not activate public RAG, approve evidence, clear redistribution rights or change existing endpoints. Recommendations below concern an offline-code commit only; no commit/push/deployment is executed.

## Baseline and evaluation boundaries

Branch `feat/working-legal-chat-mvp`, production baseline `547c32f821aa55d251044006c6d86679eccbe87e`. The pre-work manifest captures all 21 Stages 6A-6E files and 76 prior QA artifacts. Original 30/31/20/20 datasets and original result files are immutable. Stage 6D and Stage 6E questions are now explicitly **exposed development diagnostics**, never described as untouched holdouts.

A new Stage 6F source-first set was authored only after final changes and the 744-test pass; its pre-query freeze is `f6d0c53e257927e803a0aa66a9d64bdfdd50590658069e0098b9150d31cebdff`. Eight positives and twelve negatives bind six new source topics plus an existing notification fault target. Labels are same-agent authored, text-inspected and human-unverified. No new visual/human/currentness certification is claimed. No tuning is permitted after its first results. Small provisional sets do not establish statistical generalization or independent legal accuracy.

## Six demonstrated failures and fixes

| Exposed case | Demonstrated cause | Stage 6F change |
| --- | --- | --- |
| `time-versus-knowledge-file` | Gold BSA passage lexical rank 1, dense rank 48, fused rank 9 was removed by the top-five pool. Another BSA passage matched fact/knowledge but missed special. | Bounded lexical/hybrid candidate union before final filtering; explicit qualification anchors must survive. No evaluation ID enters normal policy. |
| `document-destruction-file` | Gold generated but rejected for cancelling/destroying/defacing forms and reading/find framing. | Unique corpus-attested English stems and query-side reading navigation cleanup. |
| `leading-question-reading` | Defining/addressing and objection/objected mismatch depressed coverage. | Contextual definition/addressing navigation cleanup and English objection/object correspondence. |
| `two-evidence-topics` | Repeated same-instrument compare-with collapsed to one requirement; witnesses/refreshing forms mismatched. | Explicit repeated-instrument/with comparison groups; each requires relevant passage evidence. |
| `displaced-exception-claim` | Later-status event displaced was missed; safe abstention used the wrong category. | General displacement/annulment/suspension/revision legal-status events; no claim about actual later instruments. |
| `accounting-year-procedure` | Next accounting year missed a contiguous relative-date pattern. | Bounded relative dates permit up to two modifiers before week/month/year; insufficient current evidence is returned. |

Raw source identity, page/line spans, source text and QA remain unchanged. The fixes alter query interpretation, candidate collection and relevance decisions only. No IPC/CrPC numbering equivalence, effective dates or current-law proof is inferred. Exact before-bindings and root causes are in the private `failure-analysis.json`.

### Passage collection and sufficiency

The underlying BM25, local semantic model and runtime engine remain unchanged. In hybrid mode the offline wrapper gathers separate lexical and hybrid top-five lists globally and per relevant clause; at most 60 candidate occurrences are collected for five clauses. Each is checked with the original candidate/span/text/QA validators before selection. Lexical evidence is not discarded merely because fusion ranks it ninth. Greedy clause coverage selects only relevant candidates within the existing top-five/character budgets; there is no document quota or gold-ID forcing.

Ordinary descriptive requests retain the established weighted coverage floor. Explicit qualification anchors (for example special/especially, only, except, unless, proper, not and without) must be present rather than satisfied by shared broad words. Corpus-attested inflection alternatives are used only when a root is unique; ambiguity and unknown substantive words are retained. This is conservative lexical evidence selection, not semantic entailment or proof of all external qualifications. New unseen failures must be reported rather than patched on the fresh set.

A preliminary blanket 75% coverage increase rejected valid historical development questions and was discarded **before** new-set authoring. Its diagnostic results are preserved. The retained change is explicit qualifier preservation plus candidate-pool correction; old tests/labels are not weakened or rewritten.

### Validation and measurement protocol

The validated Stage 6D request-source view, current pin/migration reloads, review replay, original citation validation and final fresh source-hash handoff are preserved. Production/request latency measurements use complete Stage 6E/6F wrappers, including source and citation checks.

Quality-only evaluation uses a bounded batch source view and immutable feature/index reuse. Mutable trust/review checks still run at each existing loader boundary. Before accepting any final batch report, every source is rehashed and trust/checkpoint checked; any change rejects the entire batch. Progress rows remain provisional until that final check. **Batch policy timings exclude shared preflight/handoff and are not request latency.** Separate full-request paired timings and isolated fresh-process memory are reported below. No authorization decision is cached across revocation boundaries.

All quality metrics separate exact required passages from document coverage and selected evidence from diagnostic rankings. False-supported decisions include positive decisions missing any required gold passage as well as positive decisions on negative labels. False abstentions are unsupported decisions on positive labels. Citation byte/provenance correctness is not legal/currentness or relevance proof.

## Complete Stage 6 publication-path inventory

The intended combined offline-code scope is these 26 source/test/provisional-metadata/documentation files. They are not staged. Do not commit Stage 6F alone without its uncommitted Stage 6 dependencies. No historical stage snapshots are fabricated.

| Stage | File |
| --- | --- |
| 6C | `backend/retrieval/evidence.py` |
| 6E | `backend/retrieval/hardened.py` |
| 6E | `backend/retrieval/intent.py` |
| 6A/6B | `backend/retrieval/notification_review.py` |
| 6A/6B | `backend/retrieval/offline.py` |
| 6D | `backend/retrieval/optimized.py` |
| 6A/6B | `backend/retrieval/stage6-benchmark.json` |
| 6C | `backend/retrieval/stage6c-benchmark.json` |
| 6C | `backend/retrieval/stage6c.py` |
| 6D | `backend/retrieval/stage6d-heldout.json` |
| 6D | `backend/retrieval/stage6d.py` |
| 6E | `backend/retrieval/stage6e-evaluation.json` |
| 6E | `backend/retrieval/stage6e.py` |
| 6A/6B | `backend/tests/test_stage6_offline.py` |
| 6C | `backend/tests/test_stage6c_evidence.py` |
| 6D | `backend/tests/test_stage6d_optimization.py` |
| 6E | `backend/tests/test_stage6e_hardening.py` |
| 6A/6B | `docs/stage6-legal-rag-evaluation.md` |
| 6C | `docs/stage6c-evidence-sufficiency.md` |
| 6D | `docs/stage6d-optimization-review.md` |
| 6E | `docs/stage6e-failure-analysis.md` |
| 6F | `backend/retrieval/passage_level.py` |
| 6F | `backend/retrieval/stage6f.py` |
| 6F | `backend/retrieval/stage6f-evaluation.json` |
| 6F | `backend/tests/test_stage6f_passages.py` |
| 6F | `docs/stage6f-release-readiness.md` |

Private manifests/results, source excerpts/images, QA diagnostics, original PDFs, processed corpus, local indexes, cached weights, review stores and signing/approval material remain outside this publication scope. Actual public release inventory remains `docs/deployment-publication.json`; older prose referring to 41 files is stale relative to its authoritative current 47-file list. That older document is preserved rather than silently rewritten.

## Human review queue

An unsubmitted nine-item queue is in `backend/data/qa/stage6f-20261128/human-review-queue.md` and its JSON companion. It binds exact raw/processed hashes, document IDs, selected spans and context hashes. The Stage 6D workbook is unchanged.

- Three commencement notifications: independently compare complete English paragraph/context with original PDFs, retain BNS section 106(2) versus the BNSS First Schedule entry exception, and do not import either into BSA.
- High-risk passages: special-knowledge burden versus the wrong knowledge/intention paragraph; limitation exclusions; document destruction; leading questions; refreshing memory. A wrong paragraph for one question is not a fabricated corpus-wide exclusion decision.
- Resolve Acts versus Gazette-notification rights separately, including portal terms, excerpts/context, persistent caches, commercial hosting and downloadable redistribution. Government origin and conditional recommendations are not clearance.
- Keep Hindi/bilingual extraction, completeness/cross-references, later amendments/commencement/currentness, independent relevance labels and actual legal applicability unresolved until reviewed.
- Keep legal-evidence approval separate from exact-payload publication authorization. The queue has no reviewer identities, decisions, signatures, keys, receipts or approvals.

See [Stage 6A/6B](stage6-legal-rag-evaluation.md), [Stage 6C](stage6c-evidence-sufficiency.md), [Stage 6D](stage6d-optimization-review.md), [Stage 6E](stage6e-failure-analysis.md), [rights dossier](publication-review.md), [publication controls](public-corpus-deployment.md) and [binding history](evidence-migration.md).

Measured results, production-isolation verification and the recommendation follow below.

## Development results (exposed, not holdout)

Both Stage 6E and Stage 6F were freshly executed on the same source/index/model in alternating order. All 101 original/exposed questions were evaluated in BM25 and hybrid: 202 case/mode pairs, 404 policy assessments. Source/trust checks passed at each final batch boundary. These are quality results; batch policy times are intentionally not represented as request latency.

| Dataset | Mode | Stage 6E Recall@5 | Stage 6F Recall@3 / @5 | Stage 6F MRR@5 | Stage 6F nDCG@5 | Exact required passages selected | Required-doc coverage | Stage 6E to 6F false-supported decisions | Stage 6E to 6F false abstentions |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| frozen30 | bm25 | 1.0000 | 1.0000 / 1.0000 | 0.9762 | 0.9786 | 1.0000 | 1.0000 | 0 to 0 | 0 to 0 |
| frozen30 | hybrid | 1.0000 | 1.0000 / 1.0000 | 1.0000 | 0.9962 | 1.0000 | 1.0000 | 0 to 0 | 0 to 0 |
| stage6c31 | bm25 | 1.0000 | 1.0000 / 1.0000 | 1.0000 | 0.9920 | 1.0000 | 1.0000 | 0 to 0 | 0 to 0 |
| stage6c31 | hybrid | 1.0000 | 1.0000 / 1.0000 | 1.0000 | 0.9920 | 1.0000 | 1.0000 | 0 to 0 | 0 to 0 |
| exposed_d20 | bm25 | 1.0000 | 1.0000 / 1.0000 | 0.9375 | 0.9539 | 1.0000 | 1.0000 | 0 to 0 | 0 to 0 |
| exposed_d20 | hybrid | 0.9375 | 1.0000 / 1.0000 | 0.9375 | 0.9539 | 1.0000 | 1.0000 | 1 to 0 | 0 to 0 |
| exposed_e20 | bm25 | 0.6250 | 1.0000 / 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 to 0 | 3 to 0 |
| exposed_e20 | hybrid | 0.6250 | 1.0000 / 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 to 0 | 3 to 0 |

Stage 6F matches every development status, retains all required passages/documents, and has zero false-supported or false-abstention decisions in these provisional sets. The known hybrid special-knowledge substitution is removed, not relabelled. Original development labels and prior results are unchanged; these gains must not be called untouched-holdout generalization.

## Frozen first-use Stage 6F evaluation

The pre-query source-authored 20-case set was run once per system/mode after finalization. No policy or label changed afterward. Required-passage metrics distinguish selected gold coverage from diagnostic ranking; required-document coverage alone is not sufficiency. All measurements are agent-labelled and human-unverified; there are no independently human-reviewed performance results.

| System | Mode | Recall@3 | Recall@5 | MRR@5 | nDCG@5 | Mean selected gold-passage coverage | All required selected | Required-doc coverage | False-supported / supported | False abstentions / positives | Temporal classification | Exact status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| stage6e | bm25 | 0.8750 | 0.8750 | 0.9375 | 0.8750 | 0.8125 | 0.7500 | 0.9375 | 1 / 7 | 1 / 8 | 0.6923 | 0.7500 |
| stage6f | bm25 | 0.8750 | 0.8750 | 0.9167 | 0.8650 | 0.8125 | 0.7500 | 0.9375 | 1 / 7 | 1 / 8 | 0.9231 | 0.9000 |
| stage6e | hybrid | 0.7500 | 0.8750 | 0.8438 | 0.8038 | 0.8125 | 0.7500 | 0.9375 | 1 / 7 | 1 / 8 | 0.6923 | 0.7500 |
| stage6f | hybrid | 0.8750 | 0.8750 | 0.9167 | 0.8650 | 0.8125 | 0.7500 | 0.9375 | 1 / 7 | 1 / 8 | 0.9231 | 0.9000 |

Stage 6F has **0/12 supported negative cases**, but **1/7 supported decisions lacks required gold**, in both modes. Binary negative-case false positives alone would hide this positive-case passage failure. One of eight positive cases abstains. All five current/later negatives abstain; four receive the exact current-evidence category and one the generic insufficient-evidence category. Temporal class accuracy is 12/13 and exact status is 18/20. These denominators are small and provisional, not legal truth or generated-answer hallucination rates.

### Remaining failures to preserved without tuning

| Case | Expected | Actual | Diagnosis |
| --- | --- | --- | --- |
| `service-and-error-reading` | historical evidence | insufficient evidence | The BNS clause uses prevention/service; the source uses prevents/serving. Current inflection normalization does not cover these deverbal-noun correspondences. Weighted BNS coverage is 0.2263. BNSS evidence alone cannot support the comparison. |
| `oral-and-producer-reading` | both required BSA passages | supported, but oral gold omitted | Both gold passages were generated and pass their group match. Final ranking/truncation selects other related documentary/oral evidence paragraphs and the producer passage, but omits the required oral-evidence exception paragraph. This is a final passage-ranking/completeness failure, not wrong document identity. |
| `intervening-schedule-instrument` | insufficient current evidence | insufficient evidence | The unseen event phrase set aside is not recognized as a later-status change. The actual answer still abstains; no current-law claim is established. |

For the oral comparison, human review must also adjudicate intended exact scope and unjudged alternative relevance; no gold correction is asserted. The original required label is retained and the result is counted as false-supported. Private `new-evaluation-failures.json` gives exact selected IDs, source text, anchors and missing concepts; `new-passage-pool-trace.json` proves both gold IDs were generated before the final top-five selection. The trace re-executes one exposed BM25 case for diagnosis only; no new metrics or tuning replace the recorded first-use results.

The held-out results are now observed. Any further correction must be a separately reviewed revision with another untouched evaluation, not another claim that this set is unexposed. Passage correctness, cross-references and the intended gold labels remain human review items.

### Citation integrity

The development comparison validated 445 citation occurrences across both systems/modes. The first-use comparison validated 105 occurrences, including 55 in Stage 6F. No invalid quote/source/page/context binding was accepted. Three fresh provenance/hash/qualification faults fail closed in each system/mode; original negative/adversarial source tests also pass. Accurate citations do not make an irrelevant or incomplete comparison sufficient.

## Full-request latency and memory impact

Six fixed exposed failure questions were timed twice per system/mode in alternating order, sharing the existing cached model/index. These are **full per-request wrapper** measurements with initial source validation, fresh trust checks, citation validation and final source hashing. Index/model initialization is excluded. Returned evidence differs because correctness changed. Twelve samples per row are too few for a deployment SLA; nearest-rank p95 is the maximum.

| Mode | System | Samples | Median ms | p95 ms |
| --- | --- | ---: | ---: | ---: |
| bm25 | stage6e | 12 | 2135.4 | 2466.8 |
| bm25 | stage6f | 12 | 2257.9 | 2756.1 |
| hybrid | stage6e | 12 | 2180.9 | 2669.8 |
| hybrid | stage6f | 12 | 2719.0 | 3901.9 |

The hybrid lexical union costs additional searches and trust checks; correctness was not traded away to remove them. Corpus-derived feature construction remains bounded and read-only. Neither batch-quality timings nor the older search-only benchmark are used as full-request latency.

Fresh-process BM25 observations, one process per policy, no semantic model loaded:

| Policy | Index build s | Policy feature build s | RSS after index MiB | RSS after policy MiB | Process peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: |
| stage6e | 2.498 | 0.078 | 58.570 | 60.641 | 185.199 |
| stage6f | 2.618 | 0.187 | 58.598 | 61.281 | 185.301 |

Observed post-policy RSS increases by about 0.64 MiB between these single-process observations; within-process feature increments were about 2.07 versus 2.68 MiB. Peaks include index/source validation, not just matching. Hybrid quality-process peak was 706.12 MiB and is a separate dependency footprint. These Windows observations are not Render/Linux/free-tier certification. No new production environment variables are required.

**Timing anomalies:** the development report recorded a 7,794.8-second cached-model build interval; its cause is unresolved and it is not presented as representative startup performance. The later frozen-evaluation build was 42.64 seconds; the original-benchmark build was 17.46 seconds. All actual intervals remain recorded. The first 31-test focused run reported 645.66 seconds; its duration rerun passed in 21.54 seconds. No cause is invented and no source/quality rows are discarded to improve metrics. Full-request comparisons above were collected separately. Background workload, scheduling, antivirus, filesystem cache and power state were not controlled.

## Regression and public boundary verification

**744 backend tests passed in 327.37 seconds**, including 37 new Stage 6F tests and all previous offline benchmark tests. One existing Starlette/HTTPX deprecation warning remains. Tests cover lexical survival under simulated hybrid truncation, qualification completeness, corpus-attested inflections, same-instrument comparisons, missing instruments/concepts, quote/hash/ID/qualifier tampering, exclusions, source edits, revocation checkpoints, pool bounds, forged evaluation labels/approval flags and fresh-process public import isolation. No previous test or benchmark label was modified.

The original Stage 6A/6B benchmark was rerun with the original graded labels:

| Mode | Recall@3 | Recall@5 | MRR@5 | nDCG@5 | Citation checks |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.9286 | 0.9286 | 0.9048 | 0.8950 | 72 / 72 |
| hybrid | 0.9524 | 0.9524 | 0.9286 | 0.9310 | 72 / 72 |

Frontend files are unchanged, so frontend lint/type/build/browser checks were not rerun. No live AI provider evaluation or cloud operation was performed.

- All **179 protected hashes**, all **21 prior Stage 6 files** and **76 prior artifacts** match their pre-work hashes. All original datasets/results and the existing review workbook are unchanged. Final implementation and fresh-set hashes still match the pre-query freeze.
- Six original PDFs remain read-only, six processed records retain recorded SHA-256 hashes, and both PDF/processed counts total **404 pages**. Selection fingerprint remains unchanged at **555 passages**, with **152 hard-quarantined Act pages**; no formerly excluded passage is made eligible.
- Both real audit chains PASS at sequence zero, with zero submissions/events/approvals and empty allowlists. No signing keys, reviewer identities or publication decisions were created for real evidence.
- All **47 runtime-file byte baselines** match (including the three CRLF hashes previously recorded); there are no endpoint/configuration changes or new required production variables.
- Static AST audit found **no runtime-to-offline Stage 6 import edges**. The current deployment inventory excludes all 26 offline scope paths. A fresh **47-file public-only export**, with no PDFs/corpus/review data/weights, returned health **200**, readiness **503 / publication_pending**, and unauthenticated research **401**; no ML/offline Stage 6 modules were loaded. The export source path was checked to prevent accidentally importing the original workspace.
- All 26 proposed publication paths were scanned: no credential/private-key/workstation-path patterns, unexpected binary paths or complete normalized source-paragraph matches (selections >=60 characters) were found. This bounded scan is not copyright clearance or proof against every possible partial excerpt. Manual source/rights review remains necessary.
- Actual cloud artifacts/settings were **not** inspected or changed. A future Git-based hosting checkout may physically contain public source code; the audit proves local reviewed-package exclusion and tested import isolation, not absence from a cloud filesystem.
- Private diagnostics, generated test sources, page/source material, review stores and model data remain ignored and are not proposed for staging. No local archive or generated corpus is in the 26-file code scope.

## Reproduction and recommendation

Requires existing dependencies; do not install/download replacements automatically. Real-source evaluation additionally needs the exact private PDFs/processed/catalogue bundle and preserved private Stage 6 baseline/freeze manifests. A public clone can run the synthetic tests, but cannot reproduce real-corpus measurements from unpublished bytes alone; the CLI fails closed instead of claiming empty success. Use unique output names.

```powershell
$tag = [guid]::NewGuid().ToString('N').Substring(0,8)
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp (Join-Path $env:TEMP "bcai-6f-$tag")
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6f --mode bm25 --output "backend/data/qa/stage6f-dev-$tag.json"
$modelPath = Read-Host 'Existing cached embedding snapshot directory'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6f --mode both --model-path $modelPath --new-evaluation backend/retrieval/stage6f-evaluation.json --output "backend/data/qa/stage6f-recheck-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6f --mode both --model-path $modelPath --timing --output "backend/data/qa/stage6f-timing-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6f --mode bm25 --memory-only stage6e --output "backend/data/qa/stage6f-mem-e-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6f --mode bm25 --memory-only stage6f --output "backend/data/qa/stage6f-mem-f-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.review verify
.\.venv\Scripts\python.exe -B -m backend.publication verify
.\.venv\Scripts\python.exe -B -m backend.review allowlist
.\.venv\Scripts\python.exe -B -m backend.publication allowlist
Get-Content backend/data/qa/stage6f-20261128/human-review-queue.md
```

**Offline-code commit recommendation: YES, for a separately approved combined research-code/evaluation commit containing the reviewed 26 dependency-linked files and documented limitations.** This is not approval to commit now, claim legal accuracy or publish any private data. No real-source fixture/diagnostic/approval artifact belongs in that scope. The public-only runtime is unchanged and isolation checks pass.

**Public RAG activation: NO-GO.** The fresh set retains a passage-selection false-supported decision, a historical false abstention and an incorrect currentness-abstention category. Rights, English/Hindi extraction, completeness/cross-references, currentness, independent gold labels, legal-evidence review and separate publication authorization remain unresolved. Reproducing already observed sets is not a new untouched evaluation. Future fixes require another reviewed version and new post-finalization cases.

Branch and HEAD remain unchanged; index is empty, no tracked files changed, and the working tree contains the 21 preserved untracked Stage 6 files plus five new Stage 6F files. No commit, push, deployment, corpus publication or cloud change occurred. Stop for manual review.
