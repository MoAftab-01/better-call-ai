"""Offline, provisional relevance evaluation. No provider, publication or review writes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import time

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.ingestion.paths import checked_path
from backend.app.ingestion.pipeline import canonical_json, read_bounded, _unique_object, _reject_constant
from backend.chat.models import Citation
from backend.chat.service import ChatService
from backend.review.models import CandidateID, DocumentID, Hash, Span
from backend.review.service import exclusion_reasons, span_text, validate_candidate
from .engine import ArchivalIndex, ROOT

LABEL_STATUS = "agent_text_checked_human_review_required"
WARNINGS = ["NOT HUMAN APPROVED", "NOT PUBLICATION AUTHORIZED", "CURRENT LEGAL POSITION NOT VERIFIED"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Binding(Record):
    candidate_id: CandidateID
    document_id: DocumentID
    raw_sha256: Hash
    processed_sha256: Hash
    span: Span
    rationale: str = Field(min_length=10, max_length=1000)


class Relevance(Record):
    reference: str
    grade: int = Field(ge=1, le=2)


class Case(Record):
    id: str = Field(pattern=r"^[a-z0-9-]{1,80}$")
    category: str = Field(min_length=1, max_length=80)
    question: str = Field(min_length=1, max_length=2000)
    insufficient: bool
    rationale: str = Field(min_length=10, max_length=1000)
    relevant: list[Relevance] = Field(max_length=10)

    @model_validator(mode="after")
    def consistent_judgments(self):
        if self.insufficient != (not self.relevant):
            raise ValueError("Insufficient cases need empty judgments; supported cases need explicit judgments")
        if len({r.reference for r in self.relevant}) != len(self.relevant) or not self.question.strip():
            raise ValueError("Duplicate judgment or blank question")
        return self


class Dataset(Record):
    schema_version: int = Field(ge=1, le=1)
    label_status: str
    human_approved: bool
    scope: str = Field(min_length=10, max_length=2000)
    catalog_sha256: Hash
    qa_sha256: Hash
    index_version: Hash
    references: dict[str, Binding] = Field(min_length=1, max_length=100)
    cases: list[Case] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def provisional_only(self):
        if self.label_status != LABEL_STATUS or self.human_approved is not False:
            raise ValueError("Evaluation labels must remain provisional, never legal approval")
        if len({c.id for c in self.cases}) != len(self.cases):
            raise ValueError("Duplicate evaluation case")
        if len({b.candidate_id for b in self.references.values()}) != len(self.references):
            raise ValueError("Duplicate source binding")
        if any(r.reference not in self.references for c in self.cases for r in c.relevant):
            raise ValueError("Unknown gold reference")
        return self


def load_dataset(path):
    # Bind the recorded digest to the exact same bounded byte snapshot we parse.
    payload = read_bounded(checked_path(path), 8 * 1024 * 1024)
    data = json.loads(payload.decode("utf-8-sig"), object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    return Dataset.model_validate(data), hashlib.sha256(payload).hexdigest()


def validate_dataset(index, data):
    """Bind authored labels to source bytes, independently of query rankings."""
    data = data if isinstance(data, Dataset) else Dataset.model_validate(data)
    if not index.catalog or (data.catalog_sha256, data.qa_sha256, data.index_version) != (
            index.catalog.digest, index.catalog.qa_hash, index.version):
        raise ValueError("Stale/missing evaluation catalogue, QA or index version")
    for document_id in index.catalog.documents:
        index.catalog.document(document_id)  # Includes unlabelled documents.
    by_id = {p.identifier: p for p in index.passages}
    if len(by_id) != len(index.passages):
        raise ValueError("Duplicate indexed passage ID")
    for binding in data.references.values():
        p = by_id.get(binding.candidate_id)
        if p is None:
            raise ValueError("Gold passage absent; labels are not inferred from retrieval results")
        c = p.candidate
        if (binding.document_id, binding.raw_sha256, binding.processed_sha256, [binding.span]) != (
                c.document_id, c.raw_sha256, c.processed_sha256, c.spans):
            raise ValueError("Gold source/page/line/hash binding differs")
        item, doc = validate_candidate(index.catalog, c)
        if exclusion_reasons(item, c) or span_text(doc, binding.span) != p.text:
            raise ValueError("Gold passage excluded or source text differs")
    return data


def make_citation(index, passage, number):
    """Reuse the product's citation formatter, with its existing exact context."""
    item, doc = validate_candidate(index.catalog, passage.candidate)
    if exclusion_reasons(item, passage.candidate):
        raise ValueError("Excluded source cannot be cited")
    c = ChatService.citation(passage, number)
    context = passage.candidate.context_spans[0]
    c.context_text = span_text(doc, context)
    c.context_text_sha256 = context.text_sha256
    return c


def validate_citation(index, citation, number, allowed_ids, *,
        evidence_claim="ARCHIVAL_UNVERIFIED", legal_currentness="unknown"):
    """Exact record validation, not a semantic truth/complete-law verifier."""
    if type(number) is not int or not 1 <= number <= 5:
        raise ValueError("Invalid citation position")
    if evidence_claim != "ARCHIVAL_UNVERIFIED" or legal_currentness != "unknown":
        raise ValueError("Historical unapproved evidence cannot assert approval or current law")
    citation = Citation.model_validate(citation)
    p = next((p for p in index.passages if p.identifier == citation.candidate_id), None)
    if p is None or p.identifier not in allowed_ids:
        raise ValueError("Unsupported citation identifier")
    item, doc = validate_candidate(index.catalog, p.candidate)
    if exclusion_reasons(item, p.candidate) or span_text(doc, p.candidate.spans[0]) != p.text:
        raise ValueError("Excluded, stale or altered source")
    expected = make_citation(index, p, number)
    if citation.model_dump() != expected.model_dump():
        raise ValueError("Citation document, quotation, context, provenance or boundary mismatch")
    if p.candidate.attribution.kind == "document_only" and citation.attribution != "document_only":
        raise ValueError("Unverified printed numbers cannot become approved attribution")
    return True


def ranking_metrics(ranking, grades):
    if len(ranking) != len(set(ranking)):
        raise ValueError("Duplicate ranking IDs")
    if not grades or any(type(v) is not int or v not in {1, 2} for v in grades.values()):
        raise ValueError("Positive, explicitly judged relevance required")
    relevant = set(grades)
    first = next((n for n, p in enumerate(ranking[:5], 1) if p in relevant), None)
    gain = lambda grade: 2**grade - 1
    dcg = sum(gain(grades.get(p, 0)) / math.log2(n + 1) for n, p in enumerate(ranking[:5], 1))
    ideal = sum(gain(g) / math.log2(n + 1) for n, g in enumerate(sorted(grades.values(), reverse=True)[:5], 1))
    return dict(recall_at_3=len(set(ranking[:3]) & relevant) / len(relevant),
        recall_at_5=len(set(ranking[:5]) & relevant) / len(relevant),
        mrr=1 / first if first else 0.0, ndcg_at_5=dcg / ideal)


def run(index, dataset, *, mode="bm25", repetitions=3, clock=time.perf_counter):
    if mode not in {"bm25", "hybrid"} or type(repetitions) is not int or not 1 <= repetitions <= 5:
        raise ValueError("Explicit mode and one to five repetitions required")
    if mode == "hybrid" and index.semantic is None:
        raise ValueError("Hybrid not available; no fallback reported as a hybrid result")
    dataset = validate_dataset(index, dataset)
    rows, latencies, metrics, abstentions = [], [], [], []
    citations_checked = 0
    for case in dataset.cases:
        rankings = []; hits = []; case_latencies = []
        for _ in range(repetitions):
            started = clock()
            hits = index.search(case.question, limit=5, max_characters=24000, mode=mode)
            latency = (clock() - started) * 1000
            if not math.isfinite(latency) or latency < 0:
                raise ValueError("Invalid measured latency")
            latencies.append(latency)
            case_latencies.append(latency)
            rankings.append([p.identifier for p in hits])
        if any(r != rankings[0] for r in rankings):
            raise ValueError("Nondeterministic repeated ranking")
        ranking = rankings[0]
        allowed = set(ranking)
        for number, p in enumerate(hits, 1):
            validate_citation(index, make_citation(index, p, number), number, allowed)
            citations_checked += 1
        grades = {dataset.references[r.reference].candidate_id: r.grade for r in case.relevant}
        scores = ranking_metrics(ranking, grades) if grades else None
        if scores is not None: metrics.append(scores)
        else: abstentions.append(not hits)
        rows.append(dict(id=case.id, category=case.category, expected=grades, retrieved=ranking,
            metrics=scores, latency_ms=case_latencies, abstained=not hits, insufficient_expected=case.insufficient,
            result="unexpected_archival_hits" if case.insufficient and hits else
                "missing_gold" if grades and not set(ranking).issuperset(grades) else "expectation_met",
            unjudged_hits=[p for p in ranking if p not in grades]))
    validate_dataset(index, dataset)  # Detect changes during the entire run.
    return dict(mode=mode, cases=len(rows), supported_cases=len(metrics), insufficient_cases=len(abstentions),
        metrics={key:statistics.mean(row[key] for row in metrics) if metrics else None
            for key in ("recall_at_3", "recall_at_5", "mrr", "ndcg_at_5")}, mrr_cutoff=5,
        insufficient_evidence_rate=statistics.mean(abstentions) if abstentions else None,
        supported_false_abstentions=sum(not row['retrieved'] for row in rows if not row['insufficient_expected']),
        citation_checks_passed=citations_checked, citation_checks_total=citations_checked,
        latency=dict(samples=len(latencies), repetitions=repetitions,
            median_ms=statistics.median(latencies),
            p95_ms=sorted(latencies)[math.ceil(.95 * len(latencies)) - 1],
            maximum_ms=max(latencies), includes="search and live source revalidation; excludes index build and citation checks"),
        deterministic_rankings=True, rows=rows)


def new_output(root, output):
    root = checked_path(root); output = checked_path(output)
    if not output.is_relative_to(checked_path(root / "backend/data/qa")):
        raise ValueError("Output must remain under ignored backend/data/qa")
    if output.exists():
        raise ValueError("Output exists; never overwrite a report")
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("stage6-benchmark.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--model-path", type=Path, help="Optional EXISTING local data-only model; no download")
    args = parser.parse_args(argv)
    try:
        target = new_output(ROOT, args.output)
        dataset, dataset_sha256 = load_dataset(args.dataset)
        implementation_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        started = time.perf_counter()
        index = ArchivalIndex(retrieval_mode="bm25")
        build_seconds = time.perf_counter() - started
        results = [run(index, dataset, repetitions=args.repetitions)]
        semantic = dict(status="NOT_MEASURED", reason="No explicit existing model selected; no download attempted")
        if args.model_path:
            from .semantic import LocalSemantic
            started = time.perf_counter()
            index.semantic = LocalSemantic(args.model_path, index.passages)
            index.mode = "hybrid"
            index.semantic_status = "local Sentence Transformers + FAISS; no downloads"
            semantic = dict(status="MEASURED", model_sha256=index.semantic.version,
                build_seconds=time.perf_counter() - started)
            results.append(run(index, dataset, mode="hybrid", repetitions=args.repetitions))
        report = dict(schema_version=1, evaluation_version="stage6-provisional-v1",
            implementation_sha256=implementation_sha256,
            warnings=WARNINGS, human_approved=False, publication_authorized=False,
            legal_currentness="unknown", label_status=dataset.label_status, dataset_sha256=dataset_sha256,
            corpus=index.status(), source_documents=len(index.catalog.documents),
            physical_pages=sum(len(index.catalog.document(d)[1].pages) for d in index.catalog.documents),
            bm25_build_seconds=build_seconds, provider_calls=0, semantic=semantic, results=results,
            limitations=["Provisional agent text judgments, not held out or expert/legal truth labels.",
                "Unjudged hits are treated as zero gain for this benchmark, not proven irrelevant.",
                "MRR is truncated at five; insufficient cases are excluded from relevance means.",
                "Ranking integrity does not prove visual extraction correctness or current legal applicability."])
        if load_dataset(args.dataset)[1] != dataset_sha256 or hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != implementation_sha256:
            raise ValueError("Evaluation dataset or implementation changed during the run")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream: stream.write(canonical_json(report))
        print(json.dumps({**{k:v for k,v in report.items() if k != "results"},
            "results":[{k:v for k,v in r.items() if k != "rows"} for r in results]}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, ImportError, RuntimeError) as exc:
        parser.exit(2, "Offline evaluation blocked: " + str(exc) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
