# Stage 6E: held-out failure analysis and offline sufficiency hardening

Local/offline only. No public retrieval, source publication, approval, provider call, deployment or production interface change is introduced. All prior Stage 6 code, datasets, reports and the human-review workbook are preserved byte-exact.

## Evaluation roles and preservation

The original 30-question and 31-case datasets remain frozen development references. The 20-question Stage 6D set was a first-run holdout in Stage 6D; **it is now exposed development data**. Fixes in this stage were informed by those failures. Improved scores on it are regression measurements, not untouched-holdout generalization. Any new evaluation is authored only after policy and test conditions are finalized, labelled agent-authored/human-unverified, and hash-frozen before candidate retrieval. Small agent-authored sets do not establish independent legal accuracy or statistical generalization.

The pre-work manifest records all 15 prior uncommitted Stage 6 files and 52 prior QA artifacts. All 179 protected hashes matched before implementation verification. Neither original relevance labels nor original result rows were edited. Full private forensic bindings and source-reading notes: `backend/data/qa/stage6e-20261128/forensic-stage6d.json`. Exact legal source passages stay private; this document contains benchmark questions and source identifiers, not a newly published corpus.

## Every original held-out failure

There were 12 exact-status failures among 20 cases in each mode, including the two false-supported decisions. Raw unfiltered BM25 put every missed required positive passage at rank 1 or 2. The ranking engine and metadata mapping were therefore not the primary cause: most losses occurred in downstream interpretation/anchor coverage. ?Retrieved? below means the final diagnostic ranking recorded by Stage 6D, not the unfiltered lexical score list. All labels still require human review.

### signed-statement-training-card

> Locate original BNS material for a training card about someone who makes a statement but refuses to sign when a competent public servant requires it.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `retrieval_filtering`. Gold was raw BM25 rank 1; instructional scaffolding and unmapped make/made forms reduced weighted anchor coverage below 0.5.
- Required passages/documents:
  - `bns-sign`: `passage_00764d536f7cd805042fc8d016602a5ed9ab3929e1dc5274b346469fe540e425`, document `doc_5d290011c13d9f72c4a2e5d98745efa61a195e10bf8b5546f425b9b7851b1574`; physical page 61, normalized lines 17-20; raw BM25 rank 1.
- Actual retrieved bindings (final diagnostic ranking):
  - None (both modes where identical).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### warehouse-mark-history

> An archival BNS worksheet distinguishes a counterfeited property mark from an ordinary label. Find the original paragraph about counterfeit marks.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `query_interpretation_and_filtering`. Gold was raw BM25 rank 1; framing plus a prefatory ordinary-label contrast polluted the explicit final locate-about request. Whether the preface also requests an ordinary-label explanation needs human label review.
- Required passages/documents:
  - `bns-mark`: `passage_02424ad03c8a1cfb8be6e1ee07f10cfe7c9112cf0b397c5ead624df44b845bfc`, document `doc_5d290011c13d9f72c4a2e5d98745efa61a195e10bf8b5546f425b9b7851b1574`; physical page 97, normalized lines 5-13; raw BM25 rank 1.
- Actual retrieved bindings (final diagnostic ranking):
  - None (both modes where identical).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. The final locate request versus its ordinary-label preface needs explicit scope adjudication.

### procedural-clock-audit

> Find the original BNSS passage for a history exercise about excluding time spent diligently prosecuting in a Court unable to entertain the matter.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `retrieval_filtering`. Gold was raw BM25 rank 1; diligence/diligently, exclude/excluding forms and exercise framing depressed coverage.
- Required passages/documents:
  - `bnss-time`: `passage_091e840d5fa636e8c66ad9d6fcad6dd3444daf0b9e233b4e1e1ab1854b99f007`, document `doc_f38bf0b56725d0807173e5b9b633b5d3a98d36c60a16074c34be651b9cd34aa6`; physical page 154, normalized lines 20-43; raw BM25 rank 1.
- Actual retrieved bindings (final diagnostic ranking):
  - None (both modes where identical).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### unavailable-speaker-credit

> A source-reading seminar needs the original BSA paragraph on contradicting or corroborating a proved statement and impeaching or confirming its maker credit.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `retrieval_filtering`. Gold was raw BM25 rank 1; contradict/corroborate/impeach/confirm versus -ing forms and seminar framing were treated as missing evidence terms.
- Required passages/documents:
  - `bsa-credit`: `passage_1e79cee2769b620401fc93a7367e2081b79000b4ac0ff7a0824ee25184b02351`, document `doc_c70eadff021cda5bc6facfc7e764e83caeb7c4d114fe7b984de9a4fdcb19ae81`; physical page 43, normalized lines 22-26; raw BM25 rank 1.
- Actual retrieved bindings (final diagnostic ranking):
  - None (both modes where identical).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### two-unrelated-training-cards

> Separate the original BNS refusal to sign a statement from the original BNSS discharge of an accused; provide archival material for each training card.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `retrieval_filtering`. Raw BM25 ranked gold passages 1 and 2; second clause failed weighted coverage due to training-card/material wording; all-clause safeguard correctly withheld comparison.
- Required passages/documents:
  - `bns-sign`: `passage_00764d536f7cd805042fc8d016602a5ed9ab3929e1dc5274b346469fe540e425`, document `doc_5d290011c13d9f72c4a2e5d98745efa61a195e10bf8b5546f425b9b7851b1574`; physical page 61, normalized lines 17-20; raw BM25 rank 1.
  - `bnss-discharge`: `passage_025b5650c3dfad53a44d8e1d167c751562d3a845065613293da2ba08237e91f8`, document `doc_f38bf0b56725d0807173e5b9b633b5d3a98d36c60a16074c34be651b9cd34aa6`; physical page 82, normalized lines 32-37; raw BM25 rank 2.
- Actual retrieved bindings (final diagnostic ranking):
  - `passage_00764d536f7cd805042fc8d016602a5ed9ab3929e1dc5274b346469fe540e425`, document `doc_5d290011c13d9f72c4a2e5d98745efa61a195e10bf8b5546f425b9b7851b1574` (The Bharatiya Nyaya Sanhita, 2023).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### time-versus-knowledge-file

> The original BNSS discusses excluded limitation time, while the original BSA discusses facts especially within knowledge. Locate material for these distinct archival tasks.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `retrieval_filtering`. Raw BM25 ranked gold passages 1 and 2; second clause contained discourse/framing terms; coverage safeguard correctly withheld incomplete comparison.
- Required passages/documents:
  - `bnss-time`: `passage_091e840d5fa636e8c66ad9d6fcad6dd3444daf0b9e233b4e1e1ab1854b99f007`, document `doc_f38bf0b56725d0807173e5b9b633b5d3a98d36c60a16074c34be651b9cd34aa6`; physical page 154, normalized lines 20-43; raw BM25 rank 1.
  - `bsa-knowledge`: `passage_0ee5d0c62e70d0e0369087a0684f343f8ae24141b9d574b5d409fadfa73f224c`, document `doc_c70eadff021cda5bc6facfc7e764e83caeb7c4d114fe7b984de9a4fdcb19ae81`; physical page 33, normalized lines 11-17; raw BM25 rank 2.
- Actual retrieved bindings (final diagnostic ranking):
  - `passage_091e840d5fa636e8c66ad9d6fcad6dd3444daf0b9e233b4e1e1ab1854b99f007`, document `doc_f38bf0b56725d0807173e5b9b633b5d3a98d36c60a16074c34be651b9cd34aa6` (The Bharatiya Nagarik Suraksha Sanhita, 2023).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### conflated-bns-index

> An original BNS study index conflates refusal to sign statements with counterfeit property marks. Locate the two separate archival passages.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `query_decomposition`. Raw BM25 ranked gold passages 2 and 1; two distinct requested concepts were merged into one anchor set, so neither paragraph met the merged coverage threshold.
- Required passages/documents:
  - `bns-sign`: `passage_00764d536f7cd805042fc8d016602a5ed9ab3929e1dc5274b346469fe540e425`, document `doc_5d290011c13d9f72c4a2e5d98745efa61a195e10bf8b5546f425b9b7851b1574`; physical page 61, normalized lines 17-20; raw BM25 rank 2.
  - `bns-mark`: `passage_02424ad03c8a1cfb8be6e1ee07f10cfe7c9112cf0b397c5ead624df44b845bfc`, document `doc_5d290011c13d9f72c4a2e5d98745efa61a195e10bf8b5546f425b9b7851b1574`; physical page 97, normalized lines 5-13; raw BM25 rank 1.
- Actual retrieved bindings (final diagnostic ranking):
  - None (both modes where identical).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### bsa-museum-card

> A museum card is labelled BSA S.O. 849(E). Find its original commencement paragraph, without treating it as a statement of present legal position.

- Requested scope: original archival text, not current applicability.
- Expected: `historical_evidence_available`; actual: `insufficient_current_evidence` in BM25 and hybrid.
- Failure layer: `query_interpretation`. Gold was retrieved; a trailing disclaimer about NOT asserting present legal position triggered currentness vocabulary without scoped negation handling.
- Required passages/documents:
  - `bsa-notice`: `passage_6c55f9a7fca605a78983e9cae28fa49712e5973bfc42a4a44e4435ad599de08f`, document `doc_648cf108a59bf5aad7e457f713d25da80c3e86c1cefbca84e419a48d1349a776`; physical page 2, normalized lines 8-10; raw BM25 rank 1.
- Actual retrieved bindings (final diagnostic ranking):
  - `passage_6c55f9a7fca605a78983e9cae28fa49712e5973bfc42a4a44e4435ad599de08f`, document `doc_648cf108a59bf5aad7e457f713d25da80c3e86c1cefbca84e419a48d1349a776` (NOTIFICATION).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### superseded-exception

> Has anything superseded the BNS commencement exception?

- Requested scope: current/later/future applicability.
- Expected: `insufficient_current_evidence`; actual: `historical_evidence_available` in BM25 and hybrid.
- Failure layer: `temporal_sufficiency`. A complete original BNS paragraph matched, but supersession asks for later evidence. Existing temporal vocabulary missed superseded; matching the historical exception did not establish requested later status.
- Required passages/documents:
  - No gold archival passage is labelled sufficient. The later-status cases need independently established later/current coverage; the legacy case needs an instrument not in this archive. Neither requirement can be inferred from absence.
- Actual retrieved bindings (final diagnostic ranking):
  - `passage_667c29888c46581982215e00f1d6a49502dd25cc486efc572473d9cd759d2611`, document `doc_aff29a301e21598f7fe2e72f0a8bbc2e3bdf923b014480e5bb3e76564fd47654` (NOTIFICATION).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### fresh-order-question

> Has a fresh Gazette order removed the BNS commencement exception?

- Requested scope: current/later/future applicability.
- Expected: `insufficient_current_evidence`; actual: `historical_evidence_available` in BM25 and hybrid.
- Failure layer: `temporal_sufficiency`. A complete original BNS paragraph matched, but a fresh order removing the exception requires additional later evidence. Fresh/order/removed status intent was not recognized.
- Required passages/documents:
  - No gold archival passage is labelled sufficient. The later-status cases need independently established later/current coverage; the legacy case needs an instrument not in this archive. Neither requirement can be inferred from absence.
- Actual retrieved bindings (final diagnostic ranking):
  - `passage_667c29888c46581982215e00f1d6a49502dd25cc486efc572473d9cd759d2611`, document `doc_aff29a301e21598f7fe2e72f0a8bbc2e3bdf923b014480e5bb3e76564fd47654` (NOTIFICATION).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### next-month-burden

> May a training appendix treat original BSA facts especially within knowledge as governing next month?

- Requested scope: current/later/future applicability.
- Expected: `insufficient_current_evidence`; actual: `insufficient_evidence` in BM25 and hybrid.
- Failure layer: `query_interpretation`. The archive correctly withheld support, but next-month applicability was classified as historical retrieval failure rather than insufficient current/future evidence.
- Required passages/documents:
  - No gold archival passage is labelled sufficient. The later-status cases need independently established later/current coverage; the legacy case needs an instrument not in this archive. Neither requirement can be inferred from absence.
- Actual retrieved bindings (final diagnostic ranking):
  - None (both modes where identical).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. No correction is asserted or approved.

### legacy-numbering-shortcut

> An index assumes IPC and BNS use identical numbering. Supply that correspondence from the archive.

- Requested scope: missing legacy-instrument correspondence.
- Expected: `insufficient_evidence`; actual: `clarification_required` in BM25 and hybrid.
- Failure layer: `decision_precedence`. No unavailable IPC source was selected. Empty anchors for one required topic triggered clarification before the absent-legacy-instrument guard; gold status taxonomy requires human confirmation.
- Required passages/documents:
  - No gold archival passage is labelled sufficient. The later-status cases need independently established later/current coverage; the legacy case needs an instrument not in this archive. Neither requirement can be inferred from absence.
- Actual retrieved bindings (final diagnostic ranking):
  - None (both modes where identical).
- Evidence validation/source confusion: no binding failure or wrong-instrument association was found in these failed cases. Source integrity is separate from relevance and sufficiency.
- Gold review: Agent-authored provisional labels require human review; no original label changed. Clarification versus insufficient-evidence taxonomy is debatable here; keep the original label and propose corrections separately.

## Two release-blocking false-supported decisions

The superseded-exception and fresh-order questions require evidence beyond the original 2024 notification. The complete original English BNS operative paragraph and qualifier were retained; these were **not** missing-quote, hash, citation or source-confusion failures. The old temporal vocabulary did not recognize the requested supersession/removal event, and notification matching accepted a shared exception anchor. That produced `historical_evidence_available` for a request whose later legal status the archive cannot establish. No negative inference from ?no later document in this archive? is valid.

Both outputs still declared unknown currentness and no approval, and no answers were generated. Nonetheless the evidence-sufficiency decision was wrong relative to the frozen expectations and remains release-blocking until verified. Fixing these cases does not independently verify the underlying current legal position.

## Implementation and safety boundaries

- `backend/retrieval/intent.py` adds bounded intent handling: later-change events with legal-status context, plural forms and relative dates; a narrow trailing historical meta-disclaimer rule; source-reading framing removal; ordinary English inflection families; explicit same-instrument comparison/conflation decomposition. Unknown substantive concepts and numbers are retained, rather than dropping every out-of-vocabulary term.
- `backend/retrieval/hardened.py` reuses the existing BM25/hybrid candidate collection, topic/instrument filters, all-group coverage, exact source/candidate/context/quote checks and QA exclusions. Act matches still require at least two content anchors and half the weighted coverage. Notification matches also require weighted coverage, instead of accepting any shared substantive word.
- A concrete final locate-about request may narrow a teaching preface; this does not authorize an answer to every claim in the preface. The original question remains in evaluation records. English word normalization changes retrieval features only; it never rewrites source text, quoted paragraphs, identifiers or legal-code mappings.
- Raw scope/injection/personal-advice restrictions run before any disclaimer narrowing. A real currentness question appended with ?but/and/is/has?? cannot be hidden by the trailing-disclaimer rule. Missing instruments are rejected before empty-anchor clarification can imply a legacy-code mapping.
- For an explicit no-exception premise, candidate collection retrieves the original paragraph to test the premise; the raw claim is retained for the mandatory misleading-premise guard. This prevents stronger relevance filtering from hiding the very qualifier needed to refuse an unsupported assertion.
- All Stage 6D optimization code remains unchanged. The new wrapper reuses `RequestSources`, request-index cloning, current trust reloads/review replay, original citation validators and the final raw/processed SHA-256 handoff check. There is no persistent approval/result cache and no model download or provider dependency.
- The new path is not imported into HTTP services and is absent from the runtime publication inventory. Evidence and publication approvals remain separate, absent prerequisites. No uncertainty in Hindi extraction, context association, legal currentness or rights is repaired or promoted by word matching.

These are inspectable heuristics, not a general semantic entailment or legal-currentness proof. Novel event wording, negation, ambiguous cross-references and missing external definitions can still fail. Showing a complete archival paragraph is not proof of every applicable legal qualification or present applicability.

## Human-review actions

The existing `backend/data/qa/stage6d-20261128/human-review-workbook-v2.md` and JSON companion remain untouched. Before any evidence/publication promotion:

1. Resolve source-specific rights for Acts separately from Gazette notifications: exact excerpts/context, portal/contract conditions, persistent caching, commercial hosting and downloads. Government provenance, commentary or ELIGIBLE recommendations are not permission.
2. Hash and visually inspect original selected paragraphs and full context. Preserve BNS section 106(2) versus the distinct BNSS First Schedule entry exception; do not import either into BSA. Original printed numbers remain unverified attribution unless the existing review workflow explicitly establishes them.
3. Review Hindi glyph mapping and bilingual completeness separately. English matching and PDF extraction equivalence do not certify visual correctness.
4. Investigate later official instruments, corrigenda, amendments and applicability independently. Original publication dates and acquisition timestamps cannot establish current law or prove absence of later changes.
5. Independently review all relevance/sufficiency labels, including the warehouse preface and legacy-status taxonomy. Record proposed corrections in new versions; do not retroactively change frozen labels or describe exposed data as untouched.
6. Perform genuine legal-evidence review and separate exact-payload publication authorization only through existing controlled workflows after explicit authorization. No reviewer identity, approval, signing key, receipt or event is created here.

Related documentation: [Stage 6A/6B](stage6-legal-rag-evaluation.md), [Stage 6C](stage6c-evidence-sufficiency.md), [Stage 6D](stage6d-optimization-review.md), [rights review](publication-review.md), [publication controls](public-corpus-deployment.md), [evidence binding](evidence-migration.md).

Measured regression, fresh evaluation and latency results follow after verification.

## Development-set before/after results

Stage 6D baseline quality rows are reused from the preserved, hash-bound prior report after checking original questions/labels, code, source catalogue/index and cached-model fingerprints. The revised Stage 6E rows were freshly executed. **Historical baseline timings are not used for latency comparisons**; fresh paired timings are reported separately. Both use Stage 6C-style equal-grade required passages; the original graded 30-question dataset is not edited and its original CLI is rerun separately.

| Dataset | Mode | System | Recall@3 / @5 | MRR@5 | nDCG@5 | Required-doc coverage | Complete gold-passage rate | FP / FN decisions | False-supported / supported |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| frozen30 | bm25 | stage6d | 1.0000 / 1.0000 | 0.9762 | 0.9786 | 1.0000 | 1.0000 | 0 / 0 | 0 / 21 |
| frozen30 | bm25 | stage6e | 1.0000 / 1.0000 | 0.9762 | 0.9786 | 1.0000 | 1.0000 | 0 / 0 | 0 / 21 |
| frozen30 | hybrid | stage6d | 1.0000 / 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 / 0 | 0 / 21 |
| frozen30 | hybrid | stage6e | 1.0000 / 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 / 0 | 0 / 21 |
| stage6c31 | bm25 | stage6d | 1.0000 / 1.0000 | 1.0000 | 0.9920 | 1.0000 | 1.0000 | 0 / 0 | 0 / 10 |
| stage6c31 | bm25 | stage6e | 1.0000 / 1.0000 | 1.0000 | 0.9920 | 1.0000 | 1.0000 | 0 / 0 | 0 / 10 |
| stage6c31 | hybrid | stage6d | 1.0000 / 1.0000 | 0.9500 | 0.9631 | 1.0000 | 1.0000 | 0 / 0 | 0 / 10 |
| stage6c31 | hybrid | stage6e | 1.0000 / 1.0000 | 0.9500 | 0.9631 | 1.0000 | 1.0000 | 0 / 0 | 0 / 10 |
| exposed_stage6d20 | bm25 | stage6d | 0.2500 / 0.2500 | 0.3750 | 0.2783 | 0.2500 | 0.1250 | 2 / 8 | 2 / 2 |
| exposed_stage6d20 | bm25 | stage6e | 1.0000 / 1.0000 | 0.9375 | 0.9539 | 1.0000 | 1.0000 | 0 / 0 | 0 / 8 |
| exposed_stage6d20 | hybrid | stage6d | 0.2500 / 0.2500 | 0.3750 | 0.2783 | 0.2500 | 0.1250 | 2 / 8 | 2 / 2 |
| exposed_stage6d20 | hybrid | stage6e | 0.9375 / 0.9375 | 0.9375 | 0.9055 | 1.0000 | 0.8750 | 0 / 0 | 1 / 8 |

FP means a supported decision for a negative-labelled case. FN means withholding support from a positive-labelled case. The separate false-supported proxy ALSO counts a positive decision missing any required gold passage. All are provisional-label-relative evidence decisions, not measured generated-answer hallucination rates. Unjudged alternate hits require human adjudication.

The two original temporal false positives are removed in both modes. On the exposed 20-case set, temporal classification, safe refusal and exact status all reach 1.0; BM25 Recall@5 reaches 1.0. Hybrid Recall@5 is **0.9375**, with **one remaining false-supported decision out of eight supported decisions (12.5%)**, even though binary FP/FN are zero, status accuracy is 1.0 and required-document coverage is 1.0. These are development gains, not an untouched-holdout claim.

### Remaining hybrid development error

`time-versus-knowledge-file` retrieves the BNSS limitation passage but substitutes BSA candidate `passage_f2a493982077fd91b42dffb6dc767ff3d09706f9c2e86e1d34527682adbe092c` (knowledge/intention and similar occurrences) for required candidate `passage_0ee5d0c62e70d0e0369087a0684f343f8ae24141b9d574b5d409fadfa73f224c` (facts especially within knowledge). Correct document identity is not correct concept coverage. Shared ?fact? and ?knowledge? terms can satisfy partial weighted overlap without the distinguishing ?especially/special? concept. This remains release-blocking; no label is changed or evidence approved. A private candidate-pool trace documents the exact fusion/filtering positions.

## First-use new evaluation (no post-result tuning)

After policy/test-condition finalization and the 707-test pass, 20 new questions were source-authored: eight provisional positives, twelve negatives. Six new source topics were read directly without query ranking; source bindings were validated and the dataset hash frozen before querying. Two English parent passages were visually sampled against original PDF renders (BNS physical page 56 and BSA page 43); the remaining four were text-only. Agent observations and render hashes are private; no human, bilingual, whole-corpus, legal-currentness or cryptographic-signature verification is claimed.

New dataset SHA-256: `d11db3e1b4c0d23abb5e9ffca306d050ccd78400985a68f4cceb1275494ee68d`. Questions/labels and finalized implementation pins still match their pre-query freeze. All source labels remain agent-authored/human-unverified. Baseline and revised systems were both freshly run, alternating pair order, once per question/mode, on the same cached-model/index conditions. No implementation change was made after seeing new results.

| Mode | System | Recall@3 / @5 | MRR@5 | nDCG@5 | Required-doc coverage | FP / FN decisions | False-supported / supported | Temporal class accuracy | Safe temporal refusal | Exact status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| bm25 | stage6d | 0.6250 / 0.6250 | 0.6250 | 0.6250 | 0.6250 | 1 / 3 | 1 / 6 | 0.6154 | 0.8000 | 0.6000 |
| bm25 | stage6e | 0.6250 / 0.6250 | 0.6250 | 0.6250 | 0.6250 | 0 / 3 | 0 / 5 | 0.8462 | 1.0000 | 0.7500 |
| hybrid | stage6d | 0.6250 / 0.6250 | 0.6250 | 0.6250 | 0.6250 | 1 / 3 | 1 / 6 | 0.6154 | 0.8000 | 0.6000 |
| hybrid | stage6e | 0.6250 / 0.6250 | 0.6250 | 0.6250 | 0.6250 | 0 / 3 | 0 / 5 | 0.8462 | 1.0000 | 0.7500 |

Revised first-use results: **0/12 negative cases supported, 0/5 supported decisions missing required gold, 3/8 positive cases refused**, in both modes. Recall@5 remains 0.625 rather than improving over the new-set baseline. Temporal class accuracy is 11/13 and exact status 15/20: safe abstention is not the same as correct classification. Required-document coverage of the one different-document positive comparison is 1.0; the same-document two-concept case is a separate failure. This small set supplies no statistical or independent legal-accuracy certification.

### Untuned new-set failures

| Case (both modes) | Expected | Actual | Remaining issue |
| --- | --- | --- | --- |
| `document-destruction-file` | `historical_evidence_available` | `insufficient_evidence` | Unseen English verb forms/framing still defeat lexical coverage; no blanket historical rejection or label change is introduced. |
| `leading-question-reading` | `historical_evidence_available` | `insufficient_evidence` | Question-definition/objection phrasing does not map robustly to the source wording; exact anchor diagnostics are private. |
| `two-evidence-topics` | `historical_evidence_available` | `insufficient_evidence` | A same-instrument comparison with ?with? is not reliably decomposed into two complete evidence requirements; support is withheld in this new case. |
| `displaced-exception-claim` | `insufficient_current_evidence` | `insufficient_evidence` | The unseen later-event wording ?displaced? is not classified as current/later; unrelated/insufficient source matching still safely abstains. |
| `accounting-year-procedure` | `insufficient_current_evidence` | `insufficient_evidence` | The expanded relative-time phrase ?next accounting year? misses the contiguous relative-date pattern; matching still safely abstains. |

These failures are retained without adjusting labels, query handling or thresholds after the freeze. They are regression candidates for a future version that must be measured on a different new evaluation set. A finite English ruleset and weighted overlap are not complete temporal parsing or semantic entailment.

### Citation and tampering outcomes

Revised development runs validated 194 citation occurrences. The new paired runs validated 44 occurrences across both systems/modes; the revised system contributed 21. No invalid citation binding was accepted. Three injected new-set provenance/hash/qualifier faults fail closed in each system/mode, as do the original frozen tamper cases. Binding integrity does not certify that a correctly quoted paragraph answers the requested legal concept.

Private full rows: `development-results.json` and `new-evaluation-results.json` under `backend/data/qa/stage6e-20261128/`. The original 30/31/20 datasets and all original result files remain untouched.

## Exact residual diagnostics

The hybrid development trace confirms that the required BSA passage is **lexical rank 1**, semantic rank **48** and fused rank **9** for its scoped clause query. The existing search returns only five candidates, so that gold passage never reaches the final sufficiency filter. The substituted paragraph matches `fact` and `knowledge`, misses `special`, and still passes with weighted overlap **0.6376**. This is a concrete interaction between candidate-pool truncation and permissive partial concept matching, not source tampering or an optimization-cache error. The final source/trust handoff passes. Correct source identity, complete quotations and document coverage are insufficient to establish the requested concept.

No post-freeze fix was made. Future work should separately evaluate bounded lexical/dense candidate preservation and distinguishing-concept coverage, with human-reviewed labels and another untouched set. Do not simply promote the substituted paragraph, drop the gold reference or claim the current hybrid decision is safe.

The new-set anchor trace gives further concrete limits: `document-destruction-file` covers only 0.2757 weighted mass, missing cancellation/destruction/defacement word forms and reading/find framing; `leading-question-reading` covers 0.4559, missing defining/addressing/objection forms. `two-evidence-topics` remains one merged group for a same-instrument ?compare ... with ...? request; its two gold paragraphs cover about 0.3450 and 0.4508 separately, so support is withheld. ?Displaced? and the noncontiguous ?next accounting year? phrase evade the temporal event/date patterns. These are confirmed untreated gaps, not relabelled successes. Full details: `remaining-case-diagnostics.json` and `hybrid-residual-trace.json` in the private Stage 6E directory.

## Equivalent-condition latency and added processing

Six fixed **exposed development** questions were measured twice per system/mode, alternating pair order with one shared cached index/model. Each row contains twelve timings. Both systems include source validation, citation checks and the fresh Stage 6D handoff. OS caches were retained; index/model startup is excluded. Outcomes differ because the policy changed, so timing is not a comparison of identical returned work. With twelve observations, nearest-rank p95 is the maximum.

| Mode | System | Samples | Median ms | p95 ms |
| --- | --- | ---: | ---: | ---: |
| bm25 | stage6d | 12 | 1978.2 | 2331.2 |
| bm25 | stage6e | 12 | 1965.0 | 2275.7 |
| hybrid | stage6d | 12 | 2087.4 | 2733.5 |
| hybrid | stage6e | 12 | 2120.7 | 2361.5 |

BM25 median is essentially flat; hybrid median regresses slightly while measured tails improve in this small sample. No broad speed or production-performance claim is made. The timing subset also reproduces the hybrid missing-special-knowledge evidence error twice; faster or similar latency does not excuse it.

Three exposed development queries were additionally profiled in BM25 mode (profiler overhead included): Stage 6D 6.0426s versus Stage 6E 6.7427s. New canonical feature construction took about 0.4335s across three assessments; `content_words` accounted for 0.4255s nested within that work (1,692 calls). Temporal classification and planning took about 1.5ms and 1.4ms respectively across the three queries. Do not sum nested timers. Source snapshots retain their full initialization and fresh handoff costs. No trust/source cache was weakened to recover this CPU cost.

These are Windows/Python 3.12.10 workstation measurements with the same 555-selection archive and cached model fingerprint `203a93edf7735ba9b7f73ca1f617b1e1ceaf8bf840e26ce9b73abf6456a15314`; the existing semantic implementation uses two threads. No paid provider calls or model downloads occurred. Background workload, power state and filesystem cache were not controlled. Private profiling script/output preserve the exact measurements.

## Complete backend regression and original benchmark

**707 backend tests passed in 265.92 seconds**, including 57 new synthetic Stage 6E tests. One existing Starlette/HTTPX TestClient deprecation warning remains. Tests cover temporal event/relative-date intent, narrow disclaimers and attempts to hide real currentness requests, word forms/framing, historical support, all-required-clause coverage, unknown/legacy instruments, wrong quotes/qualifiers/hashes/IDs/URLs, exclusion checks, source changes during handoff, review-checkpoint changes, schema forgery and production public-runtime isolation. Existing provider/security/backend regressions also pass. No frontend/production implementation was changed; frontend/browser/live Groq checks were not run for this offline-only stage.

Development failures are recorded rather than omitted: initial focused checks had 48 passes/3 failures (plural intent, a new synthetic fixture query requesting absent good-faith wording, and a temporal-independence test that needed a forced valid historical hit). Those were corrected; the next run passed 51 tests. Six more schema/qualifier tests exposed a carve-out synonym diagnostic failure (56 passes/1 failure); the query-side normalization was fixed before the final 707-test pass and new-set authoring. Only a new synthetic fixture question was corrected to match its care-only text; none of the original benchmark labels/tests were changed.

The original Stage 6A/6B CLI was rerun with its original graded labels and one repetition per mode. It measures the older extractive engine, not Stage 6D/6E sufficiency; search-only latency is not compared with full handoff timings.

| Original engine | Recall@3 | Recall@5 | MRR@5 | nDCG@5 | Citation checks |
| --- | ---: | ---: | ---: | ---: | ---: |
| bm25 | 0.9286 | 0.9286 | 0.9048 | 0.8950 | 72 / 72 |
| hybrid | 0.9524 | 0.9524 | 0.9286 | 0.9310 | 72 / 72 |

All original benchmark data/results are preserved; this rerun is a separate private artifact. Successful citation checks establish byte/source/context identity, not legal applicability or semantic correctness.

## Final integrity, publication and Git checks

- Branch `feat/working-legal-chat-mvp`, HEAD `547c32f821aa55d251044006c6d86679eccbe87e` unchanged; no staged changes or tracked modifications. Fifteen prior untracked files are preserved plus six new Stage 6E files.
- All **179 protected hashes** match; all 15 prior Stage 6 files and 52 prior QA artifacts match their pre-work hashes. The original human-review workbook is unchanged. All finalized implementation pins and the new dataset freeze match after evaluation.
- Six original PDFs remain read-only; all six processed records match their expected hashes. Raw/processed page counts match, totaling **404**. The original index remains **555** selections with identical index fingerprint and **152** hard-quarantined Act pages; no previously excluded passage was made eligible.
- Both real audit chains PASS at sequence zero, with **zero submissions, events, approvals or allowlist entries**. No publication decision, signing material or approval state is changed.
- All **47 runtime-file byte baselines** match: 44 exact HEAD blobs plus the three CRLF working-file hashes retained in Stage 6D verification. No line endings were rewritten. None of the new offline files is in the runtime inventory. Public research remains publication-pending; the production-isolation test returns health 200/readiness 503 and rejects unauthenticated research with 401 without initializing private retrieval. No live hosted/provider request or cloud operation was made in Stage 6E.
- New public-path scans found no credentials/private keys or absolute workstation paths; local links resolve and whitespace checks pass. All source-reading images, legal excerpts, raw comparison rows, diagnostics and test fixtures stay under ignored storage. Git warns that the restricted account cannot read the user-global ignore file; repository-local ignore checks pass and no configuration was changed.

### Exact new files

1. `backend/retrieval/intent.py`
2. `backend/retrieval/hardened.py`
3. `backend/retrieval/stage6e.py`
4. `backend/retrieval/stage6e-evaluation.json`
5. `backend/tests/test_stage6e_hardening.py`
6. `docs/stage6e-failure-analysis.md`

Private artifacts under `backend/data/qa/stage6e-20261128/` include baseline/finalization/freeze manifests; all-case forensic records; development and new-set rows; fresh timing and component profiles; residual traces; two original-page renders and agent observations; test results; an unresolved-human-actions list; original benchmark rerun; final verification; and ignored synthetic pytest fixtures. Previous artifacts are not overwritten.

## Reproduction and manual acceptance

Real-source evaluation requires the exact private PDFs, processed records and catalogue inputs, plus the preserved private Stage 6D comparison and Stage 6E baseline/freeze manifests. These local comparison dependencies are deliberate and are not included in the runtime or public corpus. A public clone can run synthetic tests, but must not invent real-source success without the private bundle. No installation, provider key or new production environment variable is needed. Use new output names; existing files are rejected.

```powershell
$tag = [guid]::NewGuid().ToString('N').Substring(0,8)
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q -p no:cacheprovider --basetemp (Join-Path $env:TEMP "bcai-6e-$tag")
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6e --mode bm25 --output "backend/data/qa/stage6e-dev-$tag.json"

$modelPath = Read-Host 'Existing cached embedding snapshot directory'
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:HF_HUB_DISABLE_TELEMETRY = '1'
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6e --mode both --model-path $modelPath --output "backend/data/qa/stage6e-dev-both-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6e --mode both --model-path $modelPath --new-evaluation backend/retrieval/stage6e-evaluation.json --output "backend/data/qa/stage6e-new-recheck-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.stage6e --mode both --model-path $modelPath --timing --output "backend/data/qa/stage6e-timing-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.retrieval.offline --repetitions 1 --model-path $modelPath --output "backend/data/qa/stage6e-original-$tag.json"
.\.venv\Scripts\python.exe -B -m backend.review verify
.\.venv\Scripts\python.exe -B -m backend.publication verify
.\.venv\Scripts\python.exe -B -m backend.review allowlist
.\.venv\Scripts\python.exe -B -m backend.publication allowlist
Get-Content backend/data/qa/stage6e-20261128/human-review-actions.md
```

Re-running this set is a reproducibility check of its recorded first-use results, not a new untouched holdout. Review all original cases, the residual hybrid concept substitution and five new-set failures. Do not change the frozen labels to raise metrics. New normalization/temporal/candidate-pool work needs a separately reviewed version and another post-finalization evaluation. Rights, completeness/cross-references, Hindi, currentness, labels, legal-evidence approval and publication authorization remain independent human blockers.

**Verdict: PARTIAL offline hardening; NO-GO for evidence-backed public RAG.** The two known temporal false positives are fixed and safety/integrity regressions pass, but a hybrid comparison can still assert support without the required concept passage, new positive phrasings remain missed, and some later-time intent is still unrecognized. No commit, push, deployment, source publication or public-RAG activation is performed. Stop for manual review.
