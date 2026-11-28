"""Opt-in OFFLINE Stage 6D request snapshots; not imported by production HTTP.

Only parsed, byte-validated sources are reused within one assessment. Trust pins
and the review ledger are reloaded at every existing loader boundary; all source
bytes are rehashed before handoff. No cross-request result/approval cache exists.
"""
from dataclasses import dataclass
import hashlib

from backend.app.ingestion.paths import source_path
from backend.app.ingestion.pipeline import read_bounded
from backend.publication.bindings import ReadOnlyReview
from .evidence import EvidenceRetriever, EvidenceResult
from .offline import make_citation, validate_citation


@dataclass(frozen=True)
class Inspection:
    result: EvidenceResult
    citation_count: int


def checkpoint(catalog):
    events, _ = ReadOnlyReview(catalog).replay()
    return tuple(e.event_sha256 for e in events)


class RequestSources:
    """Bounded, private request-local source view. Invalid after close()."""
    MAX_DOCUMENTS = 16
    MAX_SOURCE_BYTES = 64 * 1024 * 1024

    def __init__(self, index):
        self.root = index.root
        self.loader = index.loader
        self.original = index.catalog
        self.closed = False
        self.documents_cache = {}
        live, _ = self.loader(self.root)
        self._same_version(live)
        self.initial_checkpoint = checkpoint(live)
        self.live = live
        if len(live.documents) > self.MAX_DOCUMENTS:
            raise ValueError('Request source bound exceeded')
        size = 0
        for identifier in live.documents:
            item, doc = live.document(identifier)  # Original full validation, once.
            size += len(doc.model_dump_json().encode('utf-8'))
            if size > self.MAX_SOURCE_BYTES:
                raise ValueError('Request parsed-source bound exceeded')
            self.documents_cache[identifier] = (item, doc)
        # The final handoff rehash closes the initial load/retrieval window.

    def _same_version(self, live):
        if not self.original or (live.digest, live.qa_hash) != (self.original.digest, self.original.qa_hash):
            raise ValueError('Stale source/QA catalogue')

    def _open(self):
        if self.closed:
            raise ValueError('Expired request snapshot')

    def __getattr__(self, name):
        self._open()
        return getattr(self.live, name)

    def document(self, identifier):
        self._open()
        if identifier not in self.documents_cache:
            raise ValueError('Document outside request snapshot')
        return self.documents_cache[identifier]

    def refresh_trust(self):
        self._open()
        live, packets = self.loader(self.root)
        self._same_version(live)
        if checkpoint(live) != self.initial_checkpoint:
            raise ValueError('Review state changed during request')
        return live, packets

    def refresh_sources(self):
        live, _ = self.refresh_trust()
        if set(live.documents) != set(self.documents_cache):
            raise ValueError('Source membership changed')
        for identifier, (item, _) in self.documents_cache.items():
            if live.documents[identifier] != item:
                raise ValueError('Source metadata changed')
            for path, expected, bound in (
                (item['raw_path'], item['raw_sha256'], 25 * 1024 * 1024),
                (item['processed_path'], item['processed_sha256'], 128 * 1024 * 1024)):
                payload = read_bounded(source_path(self.root, path), bound)
                if hashlib.sha256(payload).hexdigest() != expected:
                    raise ValueError('Source changed before handoff')
        # Revocation while hashing also invalidates the handoff.
        self.refresh_trust()

    def load(self, root):
        if root != self.root:
            raise ValueError('Unexpected request root')
        _, packets = self.refresh_trust()
        return self, packets

    def close(self):
        self.documents_cache.clear()
        self.closed = True


def request_index(index, snapshot):
    """Retain evaluator fault wrappers; never bypass their search implementation."""
    clone = object.__new__(type(index))
    clone.__dict__.update(vars(index))
    if 'index' in vars(index):
        clone.index = request_index(index.index, snapshot)
    else:
        clone.catalog = snapshot
        clone.loader = snapshot.load
    return clone


class OptimizedEvidenceRetriever:
    """Unchanged Stage 6C policy, request-local validation reuse, fresh handoff."""
    def __init__(self, index):
        self.index = index

    def inspect(self, question, **kwargs):
        snapshot = None
        try:
            snapshot = RequestSources(self.index)
            active = request_index(self.index, snapshot)
            result = EvidenceRetriever(active).assess(question, **kwargs)
            count = 0
            allowed = {p.identifier for p in result.ranked}
            for number, passage in enumerate(result.ranked, 1):
                validate_citation(active, make_citation(active, passage, number), number, allowed)
                count += 1
            snapshot.refresh_sources()  # Fresh bytes + mutable trust, after citations.
            return Inspection(result, count)
        except (ValueError, OSError, KeyError, TypeError):
            return Inspection(EvidenceResult('source_integrity_failed', 'unverified',
                'Fresh source, trust, review or citation validation failed; no evidence selected.'), 0)
        finally:
            if snapshot is not None:
                snapshot.close()

    def assess(self, question, **kwargs):
        return self.inspect(question, **kwargs).result
