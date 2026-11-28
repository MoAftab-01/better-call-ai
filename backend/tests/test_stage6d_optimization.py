"""Offline optimization tests; all writable sources are SYNTHETIC, NOT LAW."""
from dataclasses import replace
import hashlib
import os

import pytest

from backend.retrieval.evidence import EvidenceRetriever
from backend.retrieval.optimized import OptimizedEvidenceRetriever, RequestSources
from backend.tests.chat_fixtures import index, mvp_seed
from backend.tests.test_stage6c_evidence import mixed, mixed_seed


@pytest.mark.parametrize('question', [
    'What does the original BNS commencement notification state?',
    'Compare original BNSS evidence interpretation and BSA marital communications.',
    'Which 2026 amendment changed BNS accident care?',
    'Compare the two laws.',
    'Compare original BNS Judge acting judicially and acts following a Court order.',
    'Compare BNSS evidence interpretation and BSA facial recognition standards.',
    'Confirm the original BNS notification commenced every provision without exceptions.',
    'Explain IPC abduction by force.',
])
def test_policy_and_rankings_unchanged(mixed, question):
    before = EvidenceRetriever(mixed).assess(question, diagnostic_retrieval=True)
    after = OptimizedEvidenceRetriever(mixed).assess(question, diagnostic_retrieval=True)
    assert before.metadata() == after.metadata()


def test_sources_are_reused_only_inside_request_and_expire(index):
    view = RequestSources(index)
    identifier = next(iter(view.documents))
    assert view.document(identifier) is view.document(identifier)
    view.close()
    assert view.documents_cache == {}
    with pytest.raises(ValueError, match='Expired'):
        view.document(identifier)
    with pytest.raises(ValueError, match='Expired'):
        view.refresh_trust()


@pytest.mark.parametrize('kind', ['raw', 'processed'])
def test_cache_never_hides_same_size_mtime_preserving_tamper(index, kind):
    view = RequestSources(index)
    p = index.passages[0].candidate
    path = index.root / (p.raw_path if kind == 'raw' else p.processed_path)
    stamp = path.stat()
    payload = path.read_bytes()
    changed = bytes([payload[0] ^ 1]) + payload[1:]
    assert len(changed) == len(payload)
    path.chmod(0o600)
    path.write_bytes(changed)
    os.utime(path, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    with pytest.raises(ValueError, match='Source changed'):
        view.refresh_sources()
    view.close()
    assert OptimizedEvidenceRetriever(index).assess('BNS original notification').status == 'source_integrity_failed'


@pytest.mark.parametrize('kind', ['quote', 'hash', 'source_url', 'qualifier'])
def test_candidates_and_provenance_still_validated(index, monkeypatch, kind):
    p = next(p for p in index.passages if p.instrument == 'S.O. 848(E)')
    if kind == 'quote':
        bad = replace(p, text='SYNTHETIC altered quote NOT LAW')
    elif kind == 'hash':
        bad = replace(p, candidate=p.candidate.model_copy(update={'raw_sha256': '0'*64}))
    elif kind == 'source_url':
        bad = replace(p, candidate=p.candidate.model_copy(update={'source_metadata':
            p.candidate.source_metadata.model_copy(update={'source_url': 'https://example.invalid/wrong'})}))
    else:
        bad = replace(p, text=p.text.split('except')[0])
    monkeypatch.setattr(index, 'search', lambda *args, **kwargs: [bad])
    result = OptimizedEvidenceRetriever(index).assess('BNSS original notification')
    assert result.status == 'source_integrity_failed' and not result.selected


def test_qa_change_rejects_request_snapshot(index):
    from backend.review.service import QA
    view = RequestSources(index)
    path = index.root / QA
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(ValueError):
        view.refresh_trust()
    view.close()


def test_revocation_boundary_is_never_cached(index, monkeypatch):
    # Synthetic checkpoint changes model revocation/tail changes, not real events.
    import backend.retrieval.optimized as opt
    sequence = [()]
    monkeypatch.setattr(opt, 'checkpoint', lambda catalog: sequence[0])
    view = RequestSources(index)
    sequence[0] = ('SYNTHETIC-REVOCATION-CHECKPOINT',)
    with pytest.raises(ValueError, match='Review state changed'):
        view.refresh_trust()
    view.close()


def test_source_edit_during_retrieval_rejected_at_handoff(index, monkeypatch):
    p = index.passages[0].candidate
    path = index.root / p.raw_path
    original = EvidenceRetriever.assess
    def changing(retriever, *args, **kwargs):
        result = original(retriever, *args, **kwargs)
        path.chmod(0o600)
        path.write_bytes(path.read_bytes() + b' SYNTHETIC TAMPER')
        return result
    monkeypatch.setattr(EvidenceRetriever, 'assess', changing)
    result = OptimizedEvidenceRetriever(index).assess('BNS original notification')
    assert result.status == 'source_integrity_failed' and not result.selected


@pytest.mark.parametrize('bound,value', [('MAX_DOCUMENTS', 0), ('MAX_SOURCE_BYTES', 1)])
def test_cache_is_bounded_fail_closed(index, monkeypatch, bound, value):
    monkeypatch.setattr(RequestSources, bound, value)
    assert OptimizedEvidenceRetriever(index).assess('BNS original notification').status == 'source_integrity_failed'


def test_no_cross_request_cache_and_missing_source_fails_closed(index):
    runner = OptimizedEvidenceRetriever(index)
    assert runner.assess('BNS original notification').status == 'historical_evidence_available'
    assert vars(runner) == {'index': index}
    # Rename a synthetic fixture only; no real source is ever touched.
    path = index.root / index.passages[0].candidate.raw_path
    path.rename(path.with_suffix('.synthetic-missing'))
    assert runner.assess('BNS original notification').status == 'source_integrity_failed'


def test_fault_wrapper_not_bypassed(index):
    class Fault:
        def __init__(self, index): self.index = index
        def __getattr__(self, key): return getattr(self.index, key)
        def search(self, *args, **kwargs):
            hits = self.index.search(*args, **kwargs)
            return [replace(p, text='SYNTHETIC bad text NOT LAW') for p in hits]
    assert OptimizedEvidenceRetriever(Fault(index)).assess('BNS original notification').status == 'source_integrity_failed'


def test_hybrid_index_reused_without_model_reinitialization(mixed):
    class FakeSemantic:
        def rank(self, question, limit): return list(range(len(mixed.passages)))
    model = FakeSemantic()
    mixed.semantic = model
    query = 'Compare original BNSS evidence interpretation and BSA marital communications.'
    assert OptimizedEvidenceRetriever(mixed).assess(query, mode='hybrid').metadata() == EvidenceRetriever(mixed).assess(query, mode='hybrid').metadata()
    assert mixed.semantic is model


@pytest.mark.parametrize('fault', ['missing_qualifier', 'wrong_source_url'])
def test_new_holdout_faults_rejected_on_synthetic_sources(index, fault):
    from backend.retrieval.stage6d import HeldCase, HeldFault
    from types import SimpleNamespace
    p = next(p for p in index.passages if p.instrument == 'S.O. 848(E)')
    case = HeldCase(id='synthetic-fault', question='BNSS original notification', expected_status='source_integrity_failed',
        required_references=['synthetic'], fault=fault, label_status='agent_text_checked_human_review_required')
    active = HeldFault(index,case,{'synthetic':SimpleNamespace(candidate_id=p.identifier)})
    assert OptimizedEvidenceRetriever(active).assess(case.question).status == 'source_integrity_failed'


def test_latency_summary_and_false_support_denominator_are_explicit():
    from backend.retrieval.stage6d import summarize
    row = dict(metrics=None, expected_status='insufficient_current_evidence',
        assessment=dict(status='historical_evidence_available',temporal_class='historical_text'),
        false_supported_decision=True, exact_status_match=False, citations_validated=0, latency_ms=123.5)
    result = summarize([row])
    assert result['false_supported_decision_rate'] == 1
    assert result['temporal_safe_refusal_rate'] == 0
    assert result['latency'] == dict(samples=1,median_ms=123.5,p95_ms=123.5)
