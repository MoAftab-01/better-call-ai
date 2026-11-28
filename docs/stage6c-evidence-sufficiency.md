# Stage 6C: Temporal sufficiency and cross-document evidence

28 November 2026 (Asia/Kolkata). Base HEAD `547c32f821aa55d251044006c6d86679eccbe87e`; branch `feat/working-legal-chat-mvp`.

**NOT HUMAN APPROVED**  
**NOT PUBLICATION AUTHORIZED**  
**CURRENT LEGAL POSITION NOT VERIFIED**

This is an opt-in local/offline implementation. Production AI, demo, voice, storage, references, publication gates and the existing retrieval engine are unchanged. No corpus is published, approved or added to the public runtime. No provider call, model/source download, paid dependency, cloud configuration change, commit, push or deployment is involved.

## Frozen baseline and exact failures

The five Stage 6A/6B files remain byte-exact, including all original labels and its report. The original 30-question dataset SHA-256 is `f4fd962a805a41cd7b642c7f05a2c1dd45deff5ac1aeb264cd225eeeeb3693f1`. A new ignored `backend/data/qa/stage6c-20261128/baseline-manifest.json` records all five hashes and 27 prior result/packet/render artifacts. Existing legal-source bytes and audit records are not repinned.

Private `original-failures.json` in that directory retains the exact original questions, complete saved rankings, candidate texts, source/page/line/hash bindings and lexical overlaps for both modes. No legal excerpts are copied into this document.

1. **Temporal:** `Which 2026 amendment changed BNS accident lawful act proper care and caution?`
   Both modes returned `passage_bcd638f4aa77c9feea500abbcb22ba6749810c875dabe20b116f9613dbb74c0f` (original BNS, physical page 11, lines 17-23), then `passage_878a0b7be71c17088cc67574deb1235d9148bf1fff73811db11906ccf3df409d` (page 45, lines 7-24). These are original 2023 text, not evidence of a 2026 amendment. The old filter recognized words such as current/today/now but not this year/amendment request. Valid citations and archival warnings did not supply a distinct sufficiency refusal. No existing public answer is alleged to have falsely claimed verified current law; public RAG was blocked.
2. **Cross-document:** `Compare the archived BNSS rule about interpreting evidence and the BSA rule about marital communications.`
   Both modes returned only `passage_8f3dc529628793268553b3591ba3ba1176186912d83d6cea453855bb525ff395` (BSA, page 38, lines 25-29), an unjudged hit. Required labels were `passage_05be5c9c8db180bc015844153c190c8440d29c41387502e15d3e538782f1821f` (BNSS page 96, lines 8-15) and `passage_120f53e9a0c44debca48f09013f6d377562cd4098cc54bb3932da8e9f4ba8486` (BSA page 37, lines 19-24). The original exact-token overlap was one term for the BNSS target and zero for the BSA target. Both failed the existing two-term post-ranking gate; semantic ranking could not repair that exclusion. Interpreting/interpreted and marital/married/communications/communication are distinct raw tokens.

There was also a BM25-only partial miss for `Compare the original BNS passages on a Judge acting judicially and acts following a Court order.` The original rank list contained the judge paragraph first but omitted the labelled court-order paragraph from its top five. The complete five IDs remain in the private diagnostic; hybrid had already recovered both. Same-document complementary clauses are therefore tested too.

## Implementation and safety boundaries

`backend/retrieval/evidence.py` wraps an explicitly provided private index; it is not wired into an HTTP endpoint or the production corpus loader.

- **Temporal sufficiency:** deterministic rules distinguish explicit current/later/amendment/as-of requests, archival text inspection, restricted requests and ambiguity. Source publication dates and edition descriptions are read through the validated catalogue. A source's publication year is not certified legal coverage, and an effective date is not used as a currentness guarantee. Unknown time coverage is denied rather than interpreted as absence of amendments.
- **Explicit result:** `insufficient_current_evidence` selects no answer evidence, even if matching historical passages appear in diagnostic ranking. It always retains `legal_currentness=unknown`, `human_approved=false` and `publication_authorized=false`. Missing concepts/instruments produce `insufficient_evidence`; vague source/concept references produce `clarification_required`; failed bindings produce `source_integrity_failed`.
- **Separate ranking and sufficiency:** diagnostic raw rankings are available only to this offline evaluator. `selected` is empty when the claim is denied. No answer or legal conclusion is generated. A successful result is only `historical_evidence_available`, not a verified/current-law answer.
- **Clause retrieval:** explicitly named instruments and conjunction/comparison clauses define independent concept requirements. Existing BM25 and optional FAISS/RRF are reused. Small, inspectable English word-family expansions affect only queries, never source text or legal identifiers. There is no IPC/CrPC-to-new-code mapping.
- **Relevance before diversity:** every candidate must match the clause's source/type and anchors. Act clauses need two matching concept anchors and at least half the IDF-weighted anchor mass. Explicit notification inspection uses validated notification identity plus available content anchors. Existing injection, personal-advice, outside-domain, subsection and hard-QA restrictions remain in force.
- **Complementary coverage:** the selector prioritizes additional matched clauses among relevant candidates, not an unconditional result per document. One passage may cover more than one clause. A comparison is withheld if a required clause/instrument is missing or does not fit the top-five/full-paragraph budget. Single-clause results retain the existing valid ranking before considering query expansion.
- **Integrity:** source/catalogue/QA hashes and read-only review chains are rechecked. Exact candidate/context validation is reused. Altered quotes, mixed document identities, invalid source hashes and excluded/instruction-like candidates fail closed. A misleading no-exception premise is not supported when the original paragraph explicitly contains an exception.

Gold IDs and expected decisions are not inputs to the retrieval/sufficiency component. They are used only by the evaluator. No allowlist, approval state, raw PDF or processed JSON is altered.

## Regression fixes found during this stage

The first measured revision corrected the two original problem types, but its anchor gate also rejected two legitimate frozen historical questions (`bns-court-order`, `bnss-combined-sentences`) and the new `original-bnss-notice` case. The cause was treating question scaffolding such as qualifications/surround/multiple as content anchors and missing concurrently/consecutively/excepted word families. These were fixed in code, not by relabeling. Exact first-iteration results and policy/evaluator snapshots remain in the ignored QA directory as `comparison-v1.json`, `evidence-v1.py` and `stage6c-v1.py`.

The corrected revision also distinguishes a precise but unsupported printed reference from a vague question, bounds query length/evidence budget/clause fanout before scoped searches, and refuses unqualified time-specific legal-position requests even when their year matches a source publication year. A test-only fixture directory collision was corrected without modifying real sources or weakening assertions.

## Evaluation protocol

The frozen 30 questions/labels are retained. A separate `stage6c-benchmark.json`, version `stage6c-provisional-v1`, adds **31 cases** covering historical/current/as-of wording, commencement exceptions, unknown later developments, source ambiguity, complete/incomplete comparisons, unavailable legacy instruments, misleading premises, wrong-document candidates, altered quotes/hashes and identity swaps.

Labels were authored from source text and the original review packets before inspecting new rankings. This is the same agent, **not an independent human/expert reviewer**. Every label awaits human review; no Groq or other model manufactured labels or answer truth. The original fourteen source bindings are reused unchanged. Fault cases perturb in-memory candidate objects/search results only; actual source files are never corrupted for the benchmark. Unit source-byte mutations affect labelled synthetic fixtures only.

Both baseline and revision run on the same index, source bindings and questions, for BM25 and, when available, the existing cached local model. Baseline evidence selection follows the old extractive behavior (any validated hit); it had no explicit temporal classification signal. Its temporal-classification accuracy is therefore reported as unavailable, not invented. Baseline still performs citation integrity checks.

Retrieval metrics score only positive historical cases (21 frozen, 10 new): Recall@3/5, MRR@5, nDCG@5, required-document coverage and complete required-passage coverage. Required documents come from gold bindings **only for evaluation**. Retrieved document presence does not imply that the required passage is present.

Sufficiency metrics include negative cases separately: safe temporal refusal, exact status matches, insufficient-evidence handling and a **false-supported-answer-rate proxy**. No answers are generated: the proxy counts supported evidence decisions that disagree with the provisional negative expectation or omit required gold passages, divided by all supported decisions. Numerator/denominator and this limitation are retained. It is not a measured expert legal-answer error rate. Ranking relevance and citation integrity are not merged into sufficiency scores.

The first comparison measured one sweep per dataset/system/mode (244 case workflows). The final comparison reuses its 122 baseline workflows only after checking the unchanged engine/scoring/evaluator, source index, question/judgment and model bindings, and measures 122 corrected-revision workflows. The saved baseline SHA-256 is recorded. Baseline and revised timing windows therefore differ; this is not a randomized paired speed experiment. There are 61 case entries across the two sets, including intentional repeated questions/fault variants, not 61 independent unique questions. Repeated-rank/status determinism is tested separately on synthetic fixtures; this benchmark is not presented as a repeated-load/SLA study. Timings include the respective source validation/search workflow and revised sufficiency work; they exclude index/model build and the evaluator's separate citation loop. OS caching and concurrent local regression tests affect latency; no causal speed claim is made.

## Measured results

| Set | System | Mode | R@3 | R@5 | MRR@5 | nDCG@5 | Required-doc coverage |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Frozen 30 | baseline | bm25 | 0.9286 | 0.9286 | 0.9048 | 0.8950 | 0.9762 |
| Frozen 30 | revised | bm25 | 1.0000 | 1.0000 | 0.9762 | 0.9786 | 1.0000 |
| Stage 6C 31 | baseline | bm25 | 0.7000 | 0.7000 | 0.8000 | 0.7226 | 0.9000 |
| Stage 6C 31 | revised | bm25 | 1.0000 | 1.0000 | 1.0000 | 0.9920 | 1.0000 |
| Frozen 30 | baseline | hybrid | 0.9524 | 0.9524 | 0.9286 | 0.9310 | 0.9762 |
| Frozen 30 | revised | hybrid | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Stage 6C 31 | baseline | hybrid | 0.6500 | 0.7500 | 0.7250 | 0.7044 | 0.9000 |
| Stage 6C 31 | revised | hybrid | 1.0000 | 1.0000 | 0.9500 | 0.9631 | 1.0000 |

| Set | System | Mode | False support / supported decisions | Insufficient handling | Temporal safe refusal | Temporal class accuracy |
| --- | --- | --- | --- | ---: | ---: | --- |
| Frozen 30 | baseline | bm25 | 3/22 | 0.8889 | 0.5000 | not available |
| Frozen 30 | revised | bm25 | 0/21 | 1.0000 | 1.0000 | 1.0000 |
| Stage 6C 31 | baseline | bm25 | 15/21 | 0.4762 | 0.2500 | not available |
| Stage 6C 31 | revised | bm25 | 0/10 | 1.0000 | 1.0000 | 1.0000 |
| Frozen 30 | baseline | hybrid | 2/22 | 0.8889 | 0.5000 | not available |
| Frozen 30 | revised | hybrid | 0/21 | 1.0000 | 1.0000 | 1.0000 |
| Stage 6C 31 | baseline | hybrid | 14/21 | 0.4762 | 0.2500 | not available |
| Stage 6C 31 | revised | hybrid | 0/10 | 1.0000 | 1.0000 | 1.0000 |

Temporal-safe refusal denominators are the two frozen currentness cases and eight new current/later cases. Temporal-class accuracy covers the 23 frozen and 18 new historical/current-labelled cases; ambiguity/scope/fault cases are excluded from that classification denominator. All nine frozen negative cases and all 21 new negative/fault cases are withheld by the corrected revision. All 21 frozen and ten new positive cases retain their required evidence. Exact expected statuses match in every revised case in these finite sets.

| Set | System | Mode | Median ms | p95 ms | Candidate document diversity | Cross-doc coverage | Complete cross-doc passages |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Frozen 30 | baseline | bm25 | 589.58 | 1546.13 | 1.1429 | 0.8333 | 0.6667 |
| Frozen 30 | revised | bm25 | 3936.15 | 9527.59 | 1.1905 | 1.0000 | 1.0000 |
| Stage 6C 31 | baseline | bm25 | 497.96 | 1480.65 | 1.2000 | 0.6667 | 0.3333 |
| Stage 6C 31 | revised | bm25 | 3187.77 | 6695.65 | 1.4000 | 1.0000 | 1.0000 |
| Frozen 30 | baseline | hybrid | 570.52 | 1418.76 | 1.1429 | 0.8333 | 0.6667 |
| Frozen 30 | revised | hybrid | 3203.25 | 7051.90 | 1.1905 | 1.0000 | 1.0000 |
| Stage 6C 31 | baseline | hybrid | 456.53 | 1490.78 | 1.2000 | 0.6667 | 0.3333 |
| Stage 6C 31 | revised | hybrid | 2656.88 | 6447.14 | 1.4000 | 1.0000 | 1.0000 |

Document diversity is the mean number of retrieved source documents per historical positive case, not a relevance score. Cross-document coverage uses the three multi-document positive cases in each set; complete-passage coverage also requires all labelled passage IDs, not merely their documents. No unrelated result is admitted to meet a quota.

Revised local workflow medians are approximately 2.66-3.94 seconds, with p95 approximately 6.45-9.53 seconds. These costs are materially higher than baseline and remain a limitation for any future interactive integration. Full six-source checks, query fanout, OS caching and concurrent regressions contribute; no controlled causal attribution or production latency claim is made. Optimizing verification without weakening freshness requires separate engineering/measurement.

- Frozen 30, baseline bm25: 72 valid citation occurrences; 0 source-integrity rejections.
- Frozen 30, revised bm25: 45 valid citation occurrences; 0 source-integrity rejections.
- Stage 6C 31, baseline bm25: 52 valid citation occurrences; 3 source-integrity rejections.
- Stage 6C 31, revised bm25: 27 valid citation occurrences; 3 source-integrity rejections.
- Frozen 30, baseline hybrid: 72 valid citation occurrences; 0 source-integrity rejections.
- Frozen 30, revised hybrid: 43 valid citation occurrences; 0 source-integrity rejections.
- Stage 6C 31, baseline hybrid: 52 valid citation occurrences; 3 source-integrity rejections.
- Stage 6C 31, revised hybrid: 27 valid citation occurrences; 3 source-integrity rejections.

The three deliberate integrity faults (altered quote, invalid hash, swapped document) are rejected per mode. No invalid citation was accepted. Legitimate citations are checked separately from sufficiency, and raw ranked IDs can remain diagnostic-only when currentness is refused.

BM25 build in the final run: 9.817 seconds. Cached-model build: 69.079 seconds; actual model fingerprint `203a93edf7735ba9b7f73ca1f617b1e1ceaf8bf840e26ce9b73abf6456a15314`. Baseline reuse SHA-256: `16282a87ecb1f35ef1b5310eb1628c966c7ccea25d58841755d63a77f23482da`. No provider request or model download occurred.

The two original failures and the extra BM25 related-concept miss now recover all required passages or refuse the unsupported temporal claim as appropriate. Remaining ranking imperfections (all still have full required-passage recall) are retained below; labels have not been changed:

- frozen_stage6_30 / bm25 / `bns-compelled-movement`: MRR@5 0.5000, nDCG@5 0.6309.
- frozen_stage6_30 / bm25 / `judicial-acts-versus-orders`: MRR@5 1.0000, nDCG@5 0.9197.
- stage6c_31 / bm25 / `compare-judicial-concepts`: MRR@5 1.0000, nDCG@5 0.9197.
- stage6c_31 / hybrid / `historical-language`: MRR@5 0.5000, nDCG@5 0.6309.

Private machine-readable comparison: `backend/data/qa/stage6c-20261128/comparison-v2.json`. Source/evaluator/dataset pins are recorded in the report; it refuses to write if implementations or labels change during evaluation. Old Stage 6A/6B results are preserved rather than overwritten.

## Human review: separate decisions, no automatic promotion

An actionable, **unchecked** workbook is at `backend/data/qa/stage6c-20261128/human-review-workbook.md`. It binds each original notification packet, raw PDF, processed record, candidate and selected text to exact hashes. It contains no human identity, decision, signature, key or receipt.

| Notification | Original physical page / normalized lines | Mandatory distinction |
| --- | --- | --- |
| BNS S.O. 850(E) | 2 / 8-11 | Provision in BNS section 106(2) is excepted in the original paragraph. |
| BNSS S.O. 848(E) | 2 / 8-11 | First Schedule entry relating to that BNS provision is excepted; not BNSS section 106(2). |
| BSA S.O. 849(E) | 2 / 8-10 | No corresponding carve-out is stated in the original paragraph. |

For each notification, a human must independently:

- [ ] Verify raw, processed, packet and render hashes, source URL, authority and instrument number.
- [ ] Compare the complete English paragraph and surrounding context with the ORIGINAL PDF, including punctuation, dates, qualifiers, file reference and signatory. Normalized lines are extraction coordinates, not verified provision identifiers.
- [ ] Keep the 23 February 2024 notification heading separate from 24 February publication; retain the qualified original appointed date without inferring current applicability.
- [ ] Inspect unresolved Hindi extraction and reading-order issues; previous agent images are not bilingual, cryptographic-signature or human evidence certification.
- [ ] Resolve the existing source-specific rights, website conditions, hosting/cache/commercial/download questions. Government origin and ELIGIBLE_FOR_HUMAN_APPROVAL are not publication permission; Act-specific conditions remain separate.
- [ ] Independently investigate later official instruments and applicability; failure to find one is not proof none exists.
- [ ] Keep legal-evidence approval pending until a separately authorized human workflow records the required evidence/attestations. This checklist does not create an allowlist entry.
- [ ] Keep publication authorization separately pending; any later external human authorization must bind the exact source subset/manifest through existing signature/pin controls. No signer credential or receipt is created here.
- [ ] Review the fourteen original relevance bindings and all new expectations. Propose label corrections separately; do not silently alter frozen labels.

Full legal excerpts/renders remain in ignored local storage. See [Stage 6A/6B](stage6-legal-rag-evaluation.md), the [rights dossier](publication-review.md), [public corpus controls](public-corpus-deployment.md) and [V1/V2 binding guide](evidence-migration.md).

## Regression, preservation and publication isolation

**Final backend suite: 624 passed, one existing Starlette/HTTPX TestClient deprecation warning, in 396.32 seconds.** Includes 49 Stage 6C tests plus all 575 prior tests. Initial v1 focused checks passed 38 tests; a later expanded run had 48 passes and one synthetic fixture setup collision, which was fixed and rerun successfully before this final complete suite. No assertion or source-exclusion policy was weakened.

The original five Stage 6A/6B files and all 27 earlier artifacts remain byte-exact. All 179 protected hashes, six original PDFs, six processed records and 404 pages are checked against existing bindings. Both real audit chains PASS at sequence 0 with zero events and empty allowlists; the final verification summary is at `backend/data/qa/stage6c-20261128/final-verification.json`. No real reviewer, legal-evidence decision, signing material or publication receipt was created.

Existing AI/demo/backend/security regressions and public-runtime isolation tests pass. The unchanged runtime inventory excludes these offline tools and every private source/report/index; production research remains publication-gated. No frontend or production implementation/configuration file changed, so frontend checks were not rerun. Read-only TLS-verified hosted checks on 28 November returned health 200 and research readiness 503 (`publication_pending`, `research_ready=false`, `legal_currentness=unknown`); no question or provider request was sent. No cloud mutation was performed. Human labels, source correctness/rights/currentness and independent publication authorization remain unresolved.

## Reproduction

Requires the existing exact private PDF/processed bundle for real-source measurements. A public checkout can run synthetic tests, but missing private bytes must block the real benchmark rather than fabricate empty-success results. No installation, download or provider key is required for BM25.

```powershell
$tag = [guid]::NewGuid().ToString('N').Substring(0,8)
$env:PYTHONDONTWRITEBYTECODE = '1'
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6c --output "backend/data/qa/stage6c-bm25-$tag.json"

# Optional existing local data-only model; never download a replacement:
$modelPath = Read-Host 'Existing local embedding model snapshot directory'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6c --model-path $modelPath --output "backend/data/qa/stage6c-comparison-$tag.json"

$testTmp = Join-Path $env:TEMP ('bcai-stage6c-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp $testTmp
.\.venv\Scripts\python.exe -B -m backend.review verify
.\.venv\Scripts\python.exe -B -m backend.publication verify
.\.venv\Scripts\python.exe -B -m backend.review allowlist
.\.venv\Scripts\python.exe -B -m backend.publication allowlist
```

Optional reuse of a prior locally measured baseline is available with `--baseline-report backend/data/qa/stage6c-20261128/comparison-v1.json`; source/code/question/model mismatches block reuse and the prior file is never rewritten. A recorded report hash is a reproducibility reference, not an authenticated legal approval. Existing destinations are rejected; choose new report names. Do not run the offline fixture/tools as a web service or copy candidate-v3 into the public runtime.

## Remaining uncertainty and next steps

Temporal and anchor matching are conservative English heuristics, not a complete temporal parser, legal ontology, contradiction/entailment prover or legal-currentness authority. Unrecognized phrasing, negation and subtle comparisons can still fail. A matching original clause does not prove that all external qualifications, definitions, amendments or jurisdictional conditions are present. New unjudged hits are not expert relevance judgments. No source has been independently cleared for publication by this work.

Human review of labels, original paragraphs, rights and currentness is the next practical step. Inspect residual failures before considering any policy tuning, and evaluate separately versioned held-out human labels. The wrapper is intentionally offline-only; integration into a private answer path would require separate review and fresh citation checks. Public integration additionally requires genuine legal-evidence and publication authorization. No public RAG activation, automatic approval or deployment follows from these metrics.

New Stage 6C files: `backend/retrieval/evidence.py`, `backend/retrieval/stage6c.py`, `backend/retrieval/stage6c-benchmark.json`, `backend/tests/test_stage6c_evidence.py` and this document. The previous five uncommitted Stage 6A/6B files are unchanged.
