# Better Call AI roadmap

v1.0 is an isolated synthetic chat and browser voice portfolio demo, not a public legal-research release. This roadmap records completed work and proposed priorities, without promising dates, legal coverage or publication approval.

## Completed — v1.0 portfolio demo

- [x] FastAPI backend and responsive React/TypeScript workspace, deployed on Render and Vercel.
- [x] Explicitly opt-in, deterministic synthetic chat with three original fictional scenarios, disclaimers and no official citations.
- [x] Browser speech recognition and synthesis, consent, stop/cancel, transcript review, and typed fallback.
- [x] Strict demo request schema, request/body/concurrency limits, exact production origins, safe errors and provider fallback.
- [x] Separate optional Groq scenario-ID selector; deterministic production mode makes no model call.
- [x] Public/private runtime isolation and fail-closed research: no approved public corpus, no private-source fallback.
- [x] Separate local engineering pipeline for ingestion, QA, hash-bound review, versioned evidence bindings and archival retrieval. This is not public evidence clearance.
- [x] Backend, frontend, provider-guard and browser automation; maintainer-reported completion of seven manual acceptance checks.
- [x] Portfolio README, actual deployed-UI screenshots, and links to technical and stage documentation.

The demo implementation commit is `fb6f6f8`. The README and this roadmap document the portfolio release; they do not create a Git tag, GitHub Release, publication decision or legal-evidence approval.

## Next — review and operational readiness

- [ ] Complete a separate source-by-source rights and redistribution review, distinguishing Acts from Gazette notifications.
- [ ] Resolve identified extraction and passage-quality issues with visual source evidence; record uncertainty and currentness limits.
- [ ] Obtain explicit human decisions through existing evidence-review and signed publication workflows. Keep publication authorization separate from legal-passage approval.
- [ ] Activate public retrieval only after an authorized, hash-bound package passes manifest, signature, provenance and citation checks. Until then, preserve the publication-pending state.
- [ ] Add shared abuse controls, per-user quotas where appropriate, operational monitoring and provider spending controls before broader exposure.
- [ ] Repeat real-device/mobile accessibility and speech checks across supported browsers; track permissions, cancellation and audio behavior separately from mocks.
- [ ] Choose and document an explicit project license; review third-party notices independently.

## Future — evaluated research capabilities

- [ ] Expand source-bound retrieval only for cleared documents, with regression evaluations and measured refusal/citation behavior.
- [ ] Establish a maintained version/currentness process before making any current-law applicability claims.
- [ ] Evaluate optional model-assisted evidence selection with bounded outputs, safe fallback, and no model-authored official citations.
- [ ] Explore multilingual accessibility and voice improvements after appropriate quality and privacy evaluation.
- [ ] Reassess deployment capacity using measured startup, memory and latency under realistic load; avoid unverified hosting guarantees.

## Documentation and release boundaries

- [Project overview and live links](../README.md)
- [Synthetic demo, configuration and browser acceptance](synthetic-demo.md)
- [Website deployment and rollback](public-website-deployment.md)
- [Public-corpus preparation and isolation](public-corpus-deployment.md)
- [Source publication review](publication-review.md)
- [Local research implementation](completion-sprint.md)
- [Evidence-binding migration](evidence-migration.md)

Roadmap work must preserve original evidence, audit chains and explicit approval boundaries. A demo release, ingestion run, index build, model selection or documentation update never approves legal evidence or authorizes corpus publication.
