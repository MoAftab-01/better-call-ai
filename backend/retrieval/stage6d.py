"""Offline paired Stage 6C/6D evaluation; never an answer/publication service."""
import argparse
from dataclasses import replace
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import time
from typing import Literal

from pydantic import Field
from backend.app.ingestion.pipeline import canonical_json, read_bounded, _unique_object, _reject_constant
from .engine import ArchivalIndex, ROOT
from .evidence import EvidenceRetriever, EvidenceResult
from .offline import Dataset, LABEL_STATUS, WARNINGS, load_dataset, validate_dataset, ranking_metrics, make_citation, validate_citation, new_output
from .optimized import OptimizedEvidenceRetriever
from .stage6c import ReviewCase, ReviewSet, FaultIndex, load_review, original_cases


class HeldCase(ReviewCase):
    fault: Literal['wrong_document', 'missing_required', 'altered_quote', 'invalid_hash', 'swapped_document', 'missing_qualifier', 'wrong_source_url'] | None


class HeldSet(ReviewSet):
    evaluation_version: Literal['stage6d-holdout-v1']
    frozen_stage6c_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    cases: list[HeldCase] = Field(min_length=1, max_length=100)


def load_heldout(path, index, frozen_hash, stage6c_hash):
    payload = read_bounded(path, 8*1024*1024)
    data = HeldSet.model_validate(json.loads(payload.decode('utf-8-sig'), object_pairs_hook=_unique_object, parse_constant=_reject_constant))
    if (data.frozen_stage6_sha256, data.frozen_stage6c_sha256) != (frozen_hash, stage6c_hash):
        raise ValueError('Frozen development datasets changed')
    validation = Dataset.model_validate(dict(schema_version=1, label_status=LABEL_STATUS, human_approved=False,
        scope='Source-authored Stage 6D holdout; human verification pending, no legal approval.',
        catalog_sha256=data.catalog_sha256, qa_sha256=data.qa_sha256, index_version=data.index_version,
        references={k:v.model_dump() for k,v in data.references.items()},
        cases=[dict(id=c.id, category='heldout', question=c.question, insufficient=not c.required_references,
            rationale='Source bindings authored before candidate retrieval; human review pending.',
            relevant=[dict(reference=r, grade=2) for r in c.required_references]) for c in data.cases]))
    validate_dataset(index, validation)
    return data, hashlib.sha256(payload).hexdigest()


class HeldFault(FaultIndex):
    def search(self, *args, **kwargs):
        if self.case.fault not in {'missing_qualifier', 'wrong_source_url'}:
            return super().search(*args, **kwargs)
        hits = self.index.search(*args, **kwargs)
        wanted = self.refs[self.case.required_references[0]].candidate_id
        target = next(p for p in self.index.passages if p.identifier == wanted)
        if self.case.fault == 'missing_qualifier':
            if 'except' not in target.text.lower():
                raise ValueError('Fault target has no exception to remove')
            import re
            target = replace(target, text=re.split('except', target.text, maxsplit=1, flags=re.I)[0])
        else:
            metadata = target.candidate.source_metadata.model_copy(update={'source_url':'https://example.invalid/wrong-source'})
            target = replace(target, candidate=target.candidate.model_copy(update={'source_metadata':metadata}))
        return [target] + [p for p in hits if p.identifier != wanted]


def inspect(index, question, system, mode):
    if system == 'stage6d':
        checked = OptimizedEvidenceRetriever(index).inspect(question, mode=mode, diagnostic_retrieval=True)
        return checked.result, checked.citation_count
    result = EvidenceRetriever(index).assess(question, mode=mode, diagnostic_retrieval=True)
    count = 0
    try:
        for n,p in enumerate(result.ranked,1):
            validate_citation(index, make_citation(index,p,n), n, {x.identifier for x in result.ranked})
            count += 1
    except (ValueError, OSError, KeyError, TypeError):
        return EvidenceResult('source_integrity_failed','unverified','Citation handoff rejected.'), 0
    return result,count


def row(index, case, refs, system, mode):
    active = HeldFault(index,case,refs) if case.fault else index
    started = time.perf_counter()
    result, citations = inspect(active,case.question,system,mode)
    elapsed = (time.perf_counter()-started)*1000
    ranking = [p.identifier for p in result.ranked]
    needed = {refs[k].candidate_id for k in case.required_references}
    docs = {refs[k].document_id for k in case.required_references}
    found = {p.candidate.document_id for p in result.ranked}
    positive = case.expected_status == 'historical_evidence_available'
    supported = result.status == 'historical_evidence_available'
    return dict(id=case.id, system=system, mode=mode, expected_status=case.expected_status,
        assessment=result.metadata(), expected_ids=sorted(needed), expected_documents=sorted(docs),
        metrics=ranking_metrics(ranking,{p:2 for p in needed}) if positive else None,
        required_document_coverage=len(docs & found)/len(docs) if docs else None,
        false_supported_decision=supported and (not positive or not needed <= {p.identifier for p in result.selected}),
        exact_status_match=result.status==case.expected_status, citations_validated=citations, latency_ms=elapsed)


def signature(row):
    a=row['assessment']
    return tuple(json.dumps(a[k],sort_keys=True) for k in ('status','temporal_class','ranked_ids','selected_ids','required_groups','covered_groups','required_topics','source_dates','human_approved','publication_authorized'))


def latency(values):
    return dict(samples=len(values),median_ms=statistics.median(values),p95_ms=sorted(values)[math.ceil(.95*len(values))-1])


def summarize(rows):
    positives=[r for r in rows if r['metrics'] is not None]
    negatives=[r for r in rows if r['metrics'] is None]
    supported=[r for r in rows if r['assessment']['status']=='historical_evidence_available']
    temporal=[r for r in rows if r['expected_status']=='insufficient_current_evidence']
    classification=[r for r in rows if r['expected_status'] in {'insufficient_current_evidence','historical_evidence_available'}]
    mean=lambda xs:statistics.mean(xs) if xs else None
    false=sum(r['false_supported_decision'] for r in rows)
    return dict(cases=len(rows),positive_cases=len(positives),
        retrieval_metrics={k:mean([r['metrics'][k] for r in positives]) for k in ('recall_at_3','recall_at_5','mrr','ndcg_at_5')},
        required_document_coverage=mean([r['required_document_coverage'] for r in positives]),
        temporal_classification_accuracy=mean([r['assessment']['temporal_class']==('current_or_later' if r['expected_status']=='insufficient_current_evidence' else 'historical_text') for r in classification]),
        temporal_safe_refusal_rate=mean([r['assessment']['status']!='historical_evidence_available' for r in temporal]),
        insufficient_evidence_handling=mean([r['assessment']['status']!='historical_evidence_available' for r in negatives]),
        exact_status_accuracy=mean([r['exact_status_match'] for r in rows]),
        supported_decisions=len(supported), false_supported_decisions=false,
        false_supported_decision_rate=false/len(supported) if supported else 0,
        citations_validated=sum(r['citations_validated'] for r in rows),
        source_integrity_rejections=sum(r['assessment']['status']=='source_integrity_failed' for r in rows),
        latency=latency([r['latency_ms'] for r in rows]))


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--model-path',type=Path)
    parser.add_argument('--dataset',choices=['frozen','stage6c','heldout','all'],default='all')
    parser.add_argument('--mode',choices=['bm25','hybrid','both'],default='both')
    parser.add_argument('--timing-only',action='store_true',help='Three repeated timings on six frozen DEVELOPMENT questions only')
    parser.add_argument('--cold-system',choices=['stage6c','stage6d'])
    args=parser.parse_args(argv)
    try:
        target=new_output(ROOT,args.output)
        paths=['backend/retrieval/'+p for p in ('engine.py','scoring.py','offline.py','evidence.py','stage6c.py','optimized.py','stage6d.py','stage6-benchmark.json','stage6c-benchmark.json','stage6d-heldout.json')]
        pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
        started=time.perf_counter();index=ArchivalIndex(retrieval_mode='bm25');build=time.perf_counter()-started
        if not index.catalog or not index.passages:raise ValueError('Private archival sources unavailable')
        modes=['bm25','hybrid'] if args.mode=='both' else [args.mode]
        semantic={'status':'NOT_REQUESTED'}
        if 'hybrid' in modes:
            if not args.model_path:raise ValueError('Explicit cached model path required')
            os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
            from .semantic import LocalSemantic
            started=time.perf_counter();index.semantic=LocalSemantic(args.model_path,index.passages)
            semantic=dict(status='MEASURED',build_seconds=time.perf_counter()-started,model_sha256=index.semantic.version)
        if args.cold_system:
            question='Compare the archived BNSS rule about interpreting evidence and the BSA rule about marital communications.'
            started=time.perf_counter();result,count=inspect(index,question,args.cold_system,modes[0]);first=(time.perf_counter()-started)*1000
            report=dict(system=args.cold_system,mode=modes[0],process_fresh=True,os_cache_flushed=False,
                bm25_build_seconds=build,semantic=semantic,first_query_ms=first,status=result.status,citations_validated=count,
                excludes='Python/module import and OS cache flushing',implementation_pins=pins)
        else:
            frozen,frozen_hash=load_dataset(ROOT/'backend/retrieval/stage6-benchmark.json');validate_dataset(index,frozen)
            stage6c,stage6c_hash=load_review(ROOT/'backend/retrieval/stage6c-benchmark.json',index,frozen_hash)
            sets=[('frozen',original_cases(frozen),frozen.references),('stage6c',stage6c.cases,stage6c.references)]
            if args.dataset in {'all','heldout'}:
                heldout,heldout_hash=load_heldout(ROOT/'backend/retrieval/stage6d-heldout.json',index,frozen_hash,stage6c_hash)
                freeze=json.loads((ROOT/'backend/data/qa/stage6d-20261128/holdout-freeze.json').read_bytes())
                if heldout_hash!=freeze['sha256']:raise ValueError('Holdout freeze broken')
                sets.append(('heldout',heldout.cases,heldout.references))
            else:heldout_hash=None
            if args.timing_only:
                # Fixed development IDs chosen before evaluating the heldout.
                chosen={'bns-commencement','bnss-first-schedule','bsa-commencement'}
                examples=sets[0][1]
                picked=[examples[n] for n in (0,3,8,15,21,25)]
                sets=[('development_timing',picked,frozen.references)]
            elif args.dataset!='all':sets=[s for s in sets if s[0]==args.dataset]
            rows=[];parity=[]
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.with_suffix('.progress.jsonl').open('x',encoding='utf-8') as progress:
                for mode in modes:
                    for name,cases,refs in sets:
                        for repetition in range(3 if args.timing_only else 1):
                            for n,case in enumerate(cases):
                                pair=[]
                                order=['stage6c','stage6d'] if (n+repetition)%2==0 else ['stage6d','stage6c']
                                for system in order:
                                    r=dict(dataset=name,repetition=repetition,**row(index,case,refs,system,mode));rows.append(r);pair.append(r)
                                    progress.write(json.dumps(r,ensure_ascii=False)+'\n');progress.flush()
                                same=signature(pair[0])==signature(pair[1]);parity.append(same)
                                if not same:raise ValueError('Optimization changed ranking/sufficiency: '+case.id)
                                if (n+1)%5==0 or n+1==len(cases):print(json.dumps(dict(dataset=name,mode=mode,repetition=repetition,completed=n+1,cases=len(cases))),flush=True)
            summaries=[]
            for name,_,_ in sets:
                for mode in modes:
                    for system in ['stage6c','stage6d']:
                        subset=[r for r in rows if (r['dataset'],r['mode'],r['system'])==(name,mode,system)]
                        summaries.append(dict(dataset=name,mode=mode,system=system,**summarize(subset)))
            report=dict(schema_version=1,evaluation_version='stage6d-offline-v1',warnings=WARNINGS,
                frozen_dataset_sha256=frozen_hash,stage6c_dataset_sha256=stage6c_hash,heldout_sha256=heldout_hash,
                implementation_pins=pins,bm25_build_seconds=build,semantic=semantic,index_version=index.version,
                provider_calls=0,downloads=0,parity_pass=all(parity),paired_cases=len(parity),timing_only=args.timing_only,
                conditions='Same process, shared immutable BM25/semantic index, alternating pair order; citation validation included in BOTH timings. OS file cache not flushed.',
                labels='Same-agent source-authored before retrieval, not independent expert ground truth. No tuning on heldout.',
                human_approved=False,publication_authorized=False,legal_currentness='unknown',summaries=summaries,rows=rows)
        if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise ValueError('Implementation/dataset changed during run')
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(canonical_json(report))
        print(json.dumps({k:v for k,v in report.items() if k not in {'rows','implementation_pins'}},indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError,RuntimeError,ImportError) as exc:parser.exit(2,'Stage 6D blocked: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
