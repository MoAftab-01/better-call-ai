# Stage 6A + 6B: Legal source review and offline RAG evaluation

27 November 2026 (Asia/Kolkata). Base: `547c32f821aa55d251044006c6d86679eccbe87e`, branch `feat/working-legal-chat-mvp`.

**NOT HUMAN APPROVED**  
**NOT PUBLICATION AUTHORIZED**  
**CURRENT LEGAL POSITION NOT VERIFIED**

Local implementation and measurement are complete. Source review remains **PARTIAL** and public research remains **BLOCKED**. This evaluates archival retrieval and exact record bindings, not generated-answer quality, current law, legal advice or comprehensive coverage. No Groq request, source download, model download, new dependency, approval event, commit, push or deployment was made.

## Reused implementation and publication boundary

- `backend/retrieval/engine.py`, `archival.py` and `scoring.py`: existing 555-selection index, BM25, lexical/topic safety filters, reciprocal rank fusion and live source revalidation. No scoring/filter changes were made.
- `semantic.py`: existing data-only, local-files-only Sentence Transformers + FAISS support. No embedding model or persistent index was copied into this repository.
- `backend/publication/bindings.py` and `backend/review/service.py`: existing V2 catalogue/pin verification, V1-to-V2 mapping, proposal regeneration, exclusion gates, exact span/context checks and read-only ledger replay.
- `backend/chat/service.py`: existing server citation formatter. New validation compares its complete citation record with the exact candidate, source and context. No privileged endpoint is repurposed.
- `backend/retrieval/evaluate.py`: existing developer regression benchmark remains unchanged. The new evaluator adds explicitly authored passage-ID judgments, Recall@3, precise denominators, per-query timings and negative-case reporting; it does not replace the index or its policies.
- Existing source publication manifests, signatures, pins, approval formats and both review ledgers are untouched. The unchanged 47-file runtime inventory excludes the new offline tools, datasets and all private QA/source directories. No public corpus is delivered.

The old [product readiness report](product-readiness.md), [publication dossier](publication-review.md), [public corpus guide](public-corpus-deployment.md) and [evidence migration guide](evidence-migration.md) remain available. Historical measurements in those documents are not replaced by these measurements.

## Source inventory and provenance

All six local raw PDF hashes and all six processed-record hashes matched the existing catalogue/audits; all **404 physical pages** remain accounted for. Full hashes, source identities and line bindings are retained in the new benchmark reference records and unchanged [acquisition audit](evidence/v2/legal-source-acquisition-stage2c.json), [ingestion audit](evidence/v2/legal-document-ingestion-stage2d.json) and [QA findings](evidence/v2/legal-text-quality-stage2e.json).

| Original source | Identifier | Recorded publication | Pages | Recorded official URL |
| --- | --- | --- | ---: | --- |
| The Bharatiya Nyaya Sanhita, 2023 | Act 45/2023 | 2023-12-25 | 102 | [250883.pdf](https://egazette.gov.in/WriteReadData/2023/250883.pdf) |
| The Bharatiya Nagarik Suraksha Sanhita, 2023 | Act 46/2023 | 2023-12-25 | 249 | [250884.pdf](https://egazette.gov.in/WriteReadData/2023/250884.pdf) |
| The Bharatiya Sakshya Adhiniyam, 2023 | Act 47/2023 | 2023-12-25 | 47 | [250882.pdf](https://egazette.gov.in/WriteReadData/2023/250882.pdf) |
| NOTIFICATION: BNS commencement | S.O. 850(E) | 2024-02-24 | 2 | [252353.pdf](https://egazette.gov.in/WriteReadData/2024/252353.pdf) |
| NOTIFICATION: BNSS commencement | S.O. 848(E) | 2024-02-24 | 2 | [252354.pdf](https://egazette.gov.in/WriteReadData/2024/252354.pdf) |
| NOTIFICATION: BSA commencement | S.O. 849(E) | 2024-02-24 | 2 | [252352.pdf](https://egazette.gov.in/WriteReadData/2024/252352.pdf) |

These are previously acquired official-origin URLs, not newly checked availability or proof of authenticity/current legal status. Acts are original Gazette editions, not amended consolidations. Recorded Act issuer: Ministry of Law and Justice (Legislative Department), Government of India. Notification issuer: Government of India, Ministry of Home Affairs. Existing provenance stays `user_supplied` / `not_independently_verified`; byte equality and document-content observations do not silently promote it.

The three notification heading dates are **23 February 2024**; the Gazette mastheads give **24 February 2024** publication. The original operative paragraphs appoint **1 July 2024**, with the separate exceptions below. Neither that date nor an Act alone establishes present commencement or case-specific applicability.

## Three notification review packets

Private packets/renders are under `backend/data/qa/stage6-notifications-20261127-final/`. Each contains the unchanged original V2 proposal, source/processed hashes, exact passage and full same-page context, QA flags, source metadata, linked rights-dossier row and hashed renders. These private files contain source text and are intentionally ignored, not publication artifacts.

| Notification | Physical page | Normalized lines | Observation about original paragraph | Status |
| --- | ---: | --- | --- | --- |
| BNS S.O. 850(E) | 2 | 8-11 | Excepts the provision in BNS section 106(2). This is not the BNSS Schedule exception. | PARTIAL |
| BNSS S.O. 848(E) | 2 | 8-11 | Excepts the First Schedule entry relating to BNS section 106(2); it does not except BNSS section 106(2). | PARTIAL |
| BSA S.O. 849(E) | 2 | 8-10 | No corresponding carve-out is stated in this original notification. | PARTIAL |

Line numbers are 1-based normalized extraction lines, not printed legal provision identifiers. The full English operative paragraph and its adjacent heading/date/file-reference/signatory context are retained. All seven automatic packet checks passed for each notification, including exact normalization equality for both PDF pages, identifier, Ministry heading, notification date, publication masthead and the existing complete-paragraph gate.

**Agent visual observations:** inspected six rendered original PDF pages at 2x resolution: the three English page-2 paragraphs and their surroundings, plus the three page-1 publication mastheads. No observed English wording, date, identifier, punctuation or qualifier discrepancy against the exact selected text. Styling and spatial layout are not represented by normalized text. Hindi translation/glyph mapping, tiny signature details and cryptographic signature validity were not certified. Same-engine extraction equality alone is not visual correctness.

`agent-visual-observations.json` separately binds those observations to source, processed, span and render hashes; it is not a human decision or ledger event. Packet generation explicitly says it performs no visual review. Regeneration into a different directory reproduced all ten generated artifacts (three packets, six PNGs and one inventory) byte-for-byte. The observation record was preserved separately.

The [rights dossier](publication-review.md) distinguishes Gazette matter other than Acts from Act-specific reproduction conditions; it does not establish an open licence or public-domain status. Its three notifications are only `ELIGIBLE_FOR_HUMAN_APPROVAL`, while Acts remain `REQUIRES_LEGAL_REVIEW`. Hosting, commercial/public web use, caching, downloadable distribution, applicable website conditions and adequacy of Act commentary remain unresolved. These are existing dossier findings, not a new legal opinion or refreshed rights/currentness review. Public-source IDs in that dossier differ from ingestion IDs; the new tool joins only by exact raw hash, URL, instrument and recorded publication date.

## Explicit relevance methodology

[stage6-benchmark.json](../backend/retrieval/stage6-benchmark.json) contains **30 questions: 21 provisionally supported and 9 insufficient-evidence cases**, bound to **14 explicitly specified existing candidate IDs**.

Coverage: BNS concepts, BNSS concepts, BSA concepts, all three commencement notifications, distinct exceptions, related judicial/burden concepts, three cross-document comparisons, out-of-scope topics, ambiguity, unavailable/subsection attribution, personal advice, injection and a later-development question.

The IDs and judgments were selected from direct inspection of the archival text **before running any benchmark query**. Existing regression topics informed the selection; this is not a held-out dataset. No gold label was inferred from a system top result. Three notification labels also received the agent image comparison above; the eleven Act labels received text inspection, not new visual certification. All labels remain `agent_text_checked_human_review_required`, `human_approved=false`. Human expert relevance, completeness and legal correctness remain unverified.

Bindings include exact raw/processed SHA-256, document ID, page ID, physical page, normalized line range and exact text hash, plus catalogue/QA/index pins. Missing, excluded or stale bindings block evaluation; there is no automatic regeneration/relabeling from ranked hits. The evaluator parses one bounded JSON snapshot, rejects duplicate keys/non-finite constants, and checks dataset/implementation stability before writing a new report.

Recall@3/5, MRR and nDCG@5 are macro-averaged over the **21 supported cases only**. MRR is explicitly truncated at **five**. nDCG uses `2**grade - 1` gain and ideal top-five ordering; actual source judgments here all use grade 2. Unjudged hits receive zero gain for this benchmark, not a finding of legal irrelevance. Insufficient-evidence rate is the fraction of the **nine negative cases** returning no hits. These cases are not mixed into relevance denominators. Search rank stability is checked across three repetitions.

## Final measured retrieval results

| Mode | Recall@3 | Recall@5 | MRR@5 | nDCG@5 | Insufficient evidence | Median ms | p95 ms | Max ms |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| bm25 | 0.9286 | 0.9286 | 0.9048 | 0.8950 | 8/9 | 435.41 | 929.66 | 1071.35 |
| hybrid | 0.9524 | 0.9524 | 0.9286 | 0.9310 | 8/9 | 373.67 | 795.17 | 879.66 |

Each mode measured **90 search calls** (30 questions x 3 repetitions); all repeated rankings were identical. Both modes had zero supported-case empty-result abstentions. This does not mean every supported question obtained its required evidence.

Each mode passed **72/72 returned citation-occurrence checks**, covering 50 distinct BM25 candidates and 48 distinct hybrid candidates. This is not an exhaustive visual/citation review of all 555 selections. The existing index still conservatively selects 552 Act passages plus three notifications on 194 pages and retains 152 hard-quarantined pages.

BM25 construction: **2.426 seconds**. Additional local semantic construction: **21.930 seconds**. Existing cached `all-MiniLM-L6-v2`, CPU Sentence Transformers and FAISS were reused, with local-only loading and Hugging Face/Transformers networking disabled. Model data fingerprint: `203a93edf7735ba9b7f73ca1f617b1e1ceaf8bf840e26ce9b73abf6456a15314`. No weights/index were published and no provider was called. Peak memory and hosted capacity were not measured.

Timings include live source revalidation and, for hybrid, local query encoding/ranking; they exclude index construction and the separate citation-validation loop. Rejected questions are included. This was a small sequential local run with BM25 preceding hybrid, ordinary OS caching and uncontrolled background load. The lower observed hybrid median is not proof that hybrid is inherently faster, nor a production/cold-start SLA or Render capacity result.

Machine-readable private report: `backend/data/qa/stage6-final-comparison-20261127.json`. Dataset SHA-256: `f4fd962a805a41cd7b642c7f05a2c1dd45deff5ac1aeb264cd225eeeeb3693f1`; evaluator SHA-256: `01b3eea2f2b86a65648283fcbfc9a864a548aca4d4f0b3866591b65e11d22fbc`. Earlier exploratory runs are separate ignored reports and were not overwritten. No source excerpts are copied into this public-facing summary.

## Failure examples and citation integrity

- `judicial-acts-versus-orders`: BM25 found only one of the two labelled passages in the first five (Recall@5 0.5). Hybrid recovered both. Labels were not changed to improve the score.
- `evidence-language-versus-confidence`: both modes missed both labelled passages for the cross-document comparison, although an unjudged passage was returned. Recall@5 and MRR were zero for this case.
- `later-amendment-2026`: both modes returned related original text for a question requiring a later amendment. That text cannot establish the requested development. Both therefore failed this negative expectation (overall 8/9). This is a retrieval sufficiency failure, not a fabricated-answer observation: no LLM or answer generator was run, and citation integrity still passed.

New citation validation reuses the server formatter and checks exact identifier/position, document attribution, source URL/title/authority/date, raw/processed/catalogue/QA hashes, page ID/page/lines, quote, context and hashes, version description and `ARCHIVAL_UNVERIFIED` status. Unsupported candidate IDs, modified text/context, mixed document references, stale source versions, exclusion violations, promoted printed labels and verified/current-law claims are rejected. Printed starts remain unverified hints with document-only attribution.

This validates explicit records and claims, not the semantic truth of arbitrary prose. A valid hash-bound citation does not prove relevance to a newer-development question, full legal context, visual extraction correctness, rights clearance or current law. The later-amendment failure demonstrates why these dimensions remain separate.

## Regression and preservation

**Full backend suite: 575 passed, one existing Starlette/HTTPX TestClient deprecation warning, in 167.31 seconds.** This includes 71 new Stage 6 tests (62 initially exercised, then nine added parsing/rights-join cases verified in the full suite). No test was weakened. The final log is under ignored `backend/data/test-runs/stage6-regression-28bab553/pytest.log`.

New synthetic tests cover metric arithmetic/denominators, deterministic ranks, bounded dataset parsing and hashing, duplicate/ambiguous labels, stale catalogue/index/source bindings, page/line/quote/context/document tampering, unsupported evidence/currentness claims, missing sources, exclusions, no-provider execution, no-overwrite/output boundaries, rights-ID namespace matching and production public-runtime isolation. Synthetic fixture edits do not touch real legal sources.

All **179 protected hashes** matched before and after evaluation. Six original PDFs/six processed records and all 404 pages remain unchanged. Both audit chains pass, sequence 0, with zero real events/eligible entries; no human approval, signer credential, publication receipt or source promotion was created. Production configuration still selects the gated public runtime: tests confirm health 200, research readiness 503 (`publication_pending`), unauthenticated research 401 and operations closed without its token. AI/demo/observability behavior is retained by existing backend regressions. Bounded TLS-verified, read-only hosted GET checks on 27 November returned health 200, readiness 503 with `publication_pending`, AI Assistant status 200 (`enabled=true`, `available=true`) and demo status 200 (`enabled=true`, `research_enabled_by_demo=false`). No question, authorization credential or legal source was sent; these status checks do not establish live answer quality.

No frontend files, production modules, environment templates, deployment inventory or cloud settings changed. Frontend checks were not rerun because the frontend is untouched. Stage 5 manual voice/product acceptance is not reclassified as human legal evidence review.

## Reproduction and manual review

A public clone can run the synthetic tests, but real-source benchmark/packet generation requires the separately acquired, exact private PDF/processed bundle described in [the migration guide](evidence-migration.md). Missing/changed bytes are an explicit nonzero blocker, not a successful empty benchmark. Raw/processed records are never repaired, re-ingested or downloaded by these commands. Use NEW output names; existing reports/directories are rejected.

From repository root in PowerShell:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
$qaTag = [guid]::NewGuid().ToString('N').Substring(0,8)
.\.venv\Scripts\python.exe -B -m backend.retrieval.notification_review --output "backend/data/qa/stage6-notifications-$qaTag"
.\.venv\Scripts\python.exe -B -m backend.retrieval.offline --repetitions 3 --output "backend/data/qa/stage6-bm25-$qaTag.json"

# Optional comparison ONLY with an already available, reviewed data-only local model:
$modelPath = Read-Host 'Existing local embedding model snapshot directory'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
.\.venv\Scripts\python.exe -B -m backend.retrieval.offline --repetitions 3 --model-path $modelPath --output "backend/data/qa/stage6-comparison-$qaTag.json"

$testTmp = Join-Path $env:TEMP ('bcai-stage6-' + [guid]::NewGuid().ToString('N'))
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp $testTmp
.\.venv\Scripts\python.exe -B -m backend.review verify
.\.venv\Scripts\python.exe -B -m backend.publication verify
```

Inspect the actual local artifacts without submitting a review:

```powershell
$packets = 'backend/data/qa/stage6-notifications-20261127-final'
Get-ChildItem $packets -Filter '*.png' | Get-FileHash -Algorithm SHA256
$packet = Get-Content "$packets/bns-so-850-e.json" -Raw | ConvertFrom-Json
$packet.original_identifiers
$packet.unchanged_original_proposal.candidate.spans
$packet.unchanged_original_proposal.exact_passage
Start-Process "$packets/bns-so-850-e-page-2.png"
# Repeat separately for bnss-so-848-e and bsa-so-849-e, including page-1 mastheads.

$evaluation = Get-Content 'backend/data/qa/stage6-final-comparison-20261127.json' -Raw | ConvertFrom-Json
$evaluation.results | Select-Object mode, cases, supported_cases, insufficient_cases, metrics, latency
$evaluation.results | ForEach-Object { $_.rows | Where-Object result -ne 'expectation_met' }
```

Manually compare every selected character/qualifier with the originals, check each render/source hash, keep publication and notification dates separate, and review the retained context/QA warnings. Independently review all fourteen relevance labels, especially Act passages and cross-document judgments. Do not treat opening a PNG, a passing hash check or this report as approval.

## Stage 6C recommendation and unresolved decisions

Before any public RAG activation: obtain actual authorized human evidence review; resolve source-specific rights/hosting/cache/download conditions through the existing dossier and external authorization workflow; separately check currentness/subsequent instruments; and improve/evaluate temporal sufficiency and cross-document recall using held-out, human-reviewed labels. Any future guard/retrieval changes require a separate implementation review; none were applied to hide these failures.

The three notifications are a small review target, not an approved corpus. No approved publication subset exists here, and no signing/approval action is authorized by this report. Stage 6A/6B tooling is ready for local manual review; source clearance and public research remain blocked.

New files only: `backend/retrieval/offline.py`, `backend/retrieval/notification_review.py`, `backend/retrieval/stage6-benchmark.json`, `backend/tests/test_stage6_offline.py`, and this report. No commit or push was performed.
