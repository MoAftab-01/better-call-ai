"""Stage 6C offline baseline/revision comparison. No answers, providers or approvals."""
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

from pydantic import Field, model_validator
from backend.app.ingestion.pipeline import canonical_json, read_bounded, _unique_object, _reject_constant
from .engine import ArchivalIndex, ROOT
from .evidence import EvidenceRetriever, EvidenceResult
from .offline import (Dataset, Record, Binding, LABEL_STATUS, WARNINGS, load_dataset,
    validate_dataset, ranking_metrics, make_citation, validate_citation, new_output)

STATUSES=Literal['historical_evidence_available','insufficient_current_evidence','clarification_required',
    'insufficient_evidence','misleading_premise','source_integrity_failed']


class ReviewCase(Record):
    id: str = Field(pattern=r'^[a-z0-9-]{1,80}$')
    question: str = Field(min_length=1,max_length=2000)
    expected_status: STATUSES
    required_references: list[str] = Field(max_length=10)
    fault: Literal['wrong_document','missing_required','altered_quote','invalid_hash','swapped_document'] | None
    label_status: Literal['agent_text_checked_human_review_required']


class ReviewSet(Record):
    schema_version: Literal[1]
    evaluation_version: Literal['stage6c-provisional-v1']
    human_approved: Literal[False]
    label_method: str
    frozen_stage6_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    references: dict[str,Binding]
    catalog_sha256: str
    qa_sha256: str
    index_version: str
    cases: list[ReviewCase] = Field(min_length=1,max_length=100)

    @model_validator(mode='after')
    def explicit(self):
        if len({c.id for c in self.cases})!=len(self.cases):raise ValueError('Duplicate case')
        for c in self.cases:
            if len(c.required_references)!=len(set(c.required_references)) or any(r not in self.references for r in c.required_references):raise ValueError('Ambiguous reference')
            if c.expected_status=='historical_evidence_available' and not c.required_references:raise ValueError('Support requires judged evidence')
        return self


def load_review(path,index,frozen_hash):
    payload=read_bounded(path,8*1024*1024)
    spec=ReviewSet.model_validate(json.loads(payload.decode('utf-8-sig'),object_pairs_hook=_unique_object,parse_constant=_reject_constant))
    if spec.frozen_stage6_sha256!=frozen_hash:raise ValueError('Original benchmark changed')
    binding_spec=Dataset.model_validate(dict(schema_version=1,label_status=LABEL_STATUS,human_approved=False,
        scope='Stage 6C provisional source-binding checks; no legal approval.',
        catalog_sha256=spec.catalog_sha256,qa_sha256=spec.qa_sha256,index_version=spec.index_version,
        references={k:v.model_dump() for k,v in spec.references.items()},
        cases=[dict(id=c.id,category='stage6c',question=c.question,insufficient=not c.required_references,
            rationale='Explicit source bindings, separate from sufficiency expectations.',
            relevant=[dict(reference=r,grade=2) for r in c.required_references]) for c in spec.cases]))
    validate_dataset(index,binding_spec)
    return spec,hashlib.sha256(payload).hexdigest()


def original_cases(dataset):
    rows=[]
    for c in dataset.cases:
        status='historical_evidence_available' if not c.insufficient else 'insufficient_current_evidence' if c.category in {'currentness','newer-development'} else 'clarification_required' if c.category=='ambiguous' else 'insufficient_evidence'
        rows.append(ReviewCase(id=c.id,question=c.question,expected_status=status,
            required_references=[r.reference for r in c.relevant],fault=None,label_status=LABEL_STATUS))
    return rows


class FaultIndex:
    """Evaluation-only in-memory faults. Never edits a source, packet or real index."""
    def __init__(self,index,case,refs):self.index=index;self.case=case;self.refs=refs
    def __getattr__(self,name):return getattr(self.index,name)
    def search(self,*args,**kwargs):
        hits=self.index.search(*args,**kwargs);fault=self.case.fault
        wanted=[self.refs[k].candidate_id for k in self.case.required_references]
        if fault=='missing_required':return [p for p in hits if p.identifier!=wanted[-1]]
        if fault=='wrong_document':return [next(p for p in self.index.passages if p.identifier==self.refs['bns-accident'].candidate_id)]
        target=next(p for p in self.index.passages if p.identifier==wanted[0])
        if fault=='altered_quote':target=replace(target,text='SYNTHETIC FAULT IN MEMORY ONLY - NOT SOURCE TEXT')
        if fault=='invalid_hash':target=replace(target,candidate=target.candidate.model_copy(update={'raw_sha256':'0'*64}))
        if fault=='swapped_document':target=replace(target,candidate=target.candidate.model_copy(update={'document_id':self.refs['bsa-marriage'].document_id}))
        return [target]+[p for p in hits if p.identifier!=target.identifier]


def measure(index,cases,refs,system,mode,repetitions=1):
    if system not in {'baseline','revised'} or repetitions not in {1,2,3}:raise ValueError('Unsupported comparison')
    rows=[];timings=[];metrics=[];doc_coverage=[];passage_coverage=[];diversity=[];cross_coverage=[];cross_passages=[];wrong_support=0;support_count=0;negative=[];cite_count=0;detected_faults=0
    temporal=[];classes=[]
    for case in cases:
        active=FaultIndex(index,case,refs) if case.fault else index
        retriever=EvidenceRetriever(active);runs=[];latency=[]
        for _ in range(repetitions):
            started=time.perf_counter()
            if system=='revised':result=retriever.assess(case.question,mode=mode,diagnostic_retrieval=True)
            else:
                hits=active.search(case.question,limit=5,max_characters=24000,mode=mode)
                result=EvidenceResult('historical_evidence_available' if hits else 'insufficient_evidence','unclassified',
                    'Baseline extractive behavior: any validated hit; no explicit temporal/comparison sufficiency classifier.',ranked=hits,selected=hits)
            elapsed=(time.perf_counter()-started)*1000
            latency.append(elapsed);timings.append(elapsed);runs.append(result)
        if any([p.identifier for p in r.ranked]!=[p.identifier for p in runs[0].ranked] or r.status!=runs[0].status for r in runs):raise ValueError('Nondeterministic comparison')
        result=runs[0];integrity=True
        try:
            for number,p in enumerate(result.ranked,1):
                validate_citation(active,make_citation(active,p,number),number,{x.identifier for x in result.ranked})
                cite_count+=1
        except (ValueError,OSError,KeyError,TypeError):
            integrity=False
            result=EvidenceResult('source_integrity_failed','unverified','Citation source validation rejected the injected candidate.')
        if result.status=='source_integrity_failed':detected_faults+=1
        ranking=[p.identifier for p in result.ranked];selected={p.identifier for p in result.selected}
        needed={refs[key].candidate_id for key in case.required_references}
        needed_docs={refs[key].document_id for key in case.required_references}
        found_docs={p.candidate.document_id for p in result.ranked}
        scored=case.expected_status=='historical_evidence_available'
        scores=ranking_metrics(ranking,{p:2 for p in needed}) if scored else None
        coverage=len(needed_docs & found_docs)/len(needed_docs) if needed_docs else None
        if scored:
            metrics.append(scores);doc_coverage.append(coverage);passage_coverage.append(needed<=set(ranking));diversity.append(len(found_docs))
            if len(needed_docs)>1:cross_coverage.append(coverage);cross_passages.append(needed<=set(ranking))
        supported=result.status=='historical_evidence_available'
        false_support=supported and (not scored or not needed<=selected)
        if supported:support_count+=1
        if false_support:wrong_support+=1
        if not scored:negative.append(not supported)
        if case.expected_status=='insufficient_current_evidence':temporal.append(not supported)
        if case.expected_status in {'insufficient_current_evidence','historical_evidence_available'}:
            expected_class='current_or_later' if case.expected_status=='insufficient_current_evidence' else 'historical_text'
            classes.append(result.temporal_class==expected_class)
        rows.append(dict(id=case.id,question=case.question,fault=case.fault,expected_status=case.expected_status,
            required_ids=sorted(needed),required_documents=sorted(needed_docs),raw_ranking=ranking,assessment=result.metadata(),
            metrics=scores,required_document_coverage=coverage,retrieved_documents=sorted(found_docs),candidate_document_diversity=len(found_docs),all_required_passages_found=needed<=set(ranking) if needed else None,
            false_supported_decision=false_support,exact_status_match=result.status==case.expected_status,
            latency_ms=latency,citation_integrity=integrity))
    return dict(system=system,mode=mode,cases=len(rows),scored_retrieval_cases=len(metrics),
        retrieval_metrics={k:statistics.mean(r[k] for r in metrics) if metrics else None for k in ['recall_at_3','recall_at_5','mrr','ndcg_at_5']},
        required_document_coverage=statistics.mean(doc_coverage) if doc_coverage else None,
        all_required_passages_rate=statistics.mean(passage_coverage) if passage_coverage else None,
        candidate_document_diversity_mean=statistics.mean(diversity) if diversity else None,
        cross_document_cases=len(cross_coverage),cross_document_coverage=statistics.mean(cross_coverage) if cross_coverage else None,
        cross_document_complete_passages_rate=statistics.mean(cross_passages) if cross_passages else None,
        decision_metrics=dict(supported_decisions=support_count,false_supported_decisions=wrong_support,
            false_supported_answer_rate_proxy=wrong_support/support_count if support_count else 0,
            proxy_denominator='supported evidence decisions, not generated answers or expert legal truth',
            insufficient_evidence_handling=statistics.mean(negative) if negative else None,
            temporal_safe_refusal_rate=statistics.mean(temporal) if temporal else None,
            temporal_classification_accuracy=statistics.mean(classes) if system=='revised' and classes else None,
            exact_status_accuracy=statistics.mean(row['exact_status_match'] for row in rows)),
        citation_occurrences_validated=cite_count,source_integrity_rejections=detected_faults,
        latency=dict(samples=len(timings),median_ms=statistics.median(timings),p95_ms=sorted(timings)[math.ceil(.95*len(timings))-1],
            includes='search workflow, source checks and revised sufficiency; excludes index/model build and evaluation citation validation'),
        repetitions=repetitions,rows=rows)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--model-path',type=Path)
    parser.add_argument('--baseline-report',type=Path,help='Reuse unchanged measured baseline rows after source/code/question binding checks')
    parser.add_argument('--repetitions',type=int,choices=[1,2,3],default=1)
    args=parser.parse_args(argv)
    try:
        target=new_output(ROOT,args.output)
        paths=['backend/retrieval/engine.py','backend/retrieval/scoring.py','backend/retrieval/offline.py','backend/retrieval/evidence.py','backend/retrieval/stage6c.py','backend/retrieval/stage6c-benchmark.json']
        pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
        started=time.perf_counter();index=ArchivalIndex(retrieval_mode='bm25');build=time.perf_counter()-started
        frozen,frozen_hash=load_dataset(ROOT/'backend/retrieval/stage6-benchmark.json');validate_dataset(index,frozen)
        spec,spec_hash=load_review(ROOT/'backend/retrieval/stage6c-benchmark.json',index,frozen_hash)
        sets=[('frozen_stage6_30',original_cases(frozen),frozen.references),('stage6c_31',spec.cases,spec.references)]
        results=[];semantic={'status':'NOT_MEASURED'};prior=None;prior_hash=None
        if args.baseline_report:
            payload=read_bounded(args.baseline_report,8*1024*1024);prior=json.loads(payload.decode('utf-8-sig'),object_pairs_hook=_unique_object,parse_constant=_reject_constant);prior_hash=hashlib.sha256(payload).hexdigest()
            if prior['frozen_dataset_sha256']!=frozen_hash or prior['stage6c_dataset_sha256']!=spec_hash or prior['index_version']!=index.version:raise ValueError('Stale saved baseline bindings')
            for name in ['backend/retrieval/engine.py','backend/retrieval/scoring.py','backend/retrieval/offline.py']:
                if prior['implementation_pins'][name]!=pins[name]:raise ValueError('Baseline implementation changed')
        def baseline(name,cases,refs,mode):
            if prior is None:return measure(index,cases,refs,'baseline',mode,args.repetitions)
            matches=[r for r in prior['results'] if r['dataset']==name and r['system']=='baseline' and r['mode']==mode]
            if len(matches)!=1:raise ValueError('Missing/duplicate saved baseline')
            old=matches[0]
            if [(r['id'],r['question'],r['expected_status'],r['required_ids']) for r in old['rows']]!=[(c.id,c.question,c.expected_status,sorted(refs[k].candidate_id for k in c.required_references)) for c in cases]:raise ValueError('Saved baseline questions/judgments differ')
            old=dict(old);old.pop('dataset',None);old['reused_from_sha256']=prior_hash
            by_id={p.identifier:p for p in index.passages};positive=[r for r in old['rows'] if r['metrics'] is not None];cross=[]
            for row in old['rows']:
                docs=sorted({by_id[p].candidate.document_id for p in row['raw_ranking']});row['retrieved_documents']=docs;row['candidate_document_diversity']=len(docs)
                if row['metrics'] is not None and len(row['required_documents'])>1:cross.append(row)
            old['candidate_document_diversity_mean']=statistics.mean(r['candidate_document_diversity'] for r in positive) if positive else None
            old['cross_document_cases']=len(cross);old['cross_document_coverage']=statistics.mean(r['required_document_coverage'] for r in cross) if cross else None
            old['cross_document_complete_passages_rate']=statistics.mean(r['all_required_passages_found'] for r in cross) if cross else None
            return old
        for name,cases,refs in sets:
            results.append(dict(dataset=name,**baseline(name,cases,refs,'bm25')))
            results.append(dict(dataset=name,**measure(index,cases,refs,'revised','bm25',args.repetitions)))
        if args.model_path:
            os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
            from .semantic import LocalSemantic
            started=time.perf_counter();index.semantic=LocalSemantic(args.model_path,index.passages)
            semantic=dict(status='MEASURED',build_seconds=time.perf_counter()-started,model_sha256=index.semantic.version)
            if prior is not None and prior['semantic'].get('model_sha256')!=index.semantic.version:raise ValueError('Saved baseline model differs')
            for name,cases,refs in sets:
                results.append(dict(dataset=name,**baseline(name,cases,refs,'hybrid')))
                results.append(dict(dataset=name,**measure(index,cases,refs,'revised','hybrid',args.repetitions)))
        validate_dataset(index,frozen)
        if load_dataset(ROOT/'backend/retrieval/stage6-benchmark.json')[1]!=frozen_hash or load_review(ROOT/'backend/retrieval/stage6c-benchmark.json',index,frozen_hash)[1]!=spec_hash:raise ValueError('Datasets changed during evaluation')
        if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise ValueError('Evaluation implementation changed')
        report=dict(schema_version=1,evaluation_version='stage6c-provisional-v1',policy_revision='stage6c-evidence-v2',baseline_reused_from_sha256=prior_hash,warnings=WARNINGS,human_approved=False,
            publication_authorized=False,legal_currentness='unknown',provider_calls=0,frozen_dataset_sha256=frozen_hash,
            stage6c_dataset_sha256=spec_hash,implementation_pins=pins,index_version=index.version,bm25_build_seconds=build,
            semantic=semantic,results=results,limitations=['Same-agent provisional labels, not independent human truth.',
                'No answers generated; false-supported-answer is a label-relative evidence-decision proxy.',
                'Retrieval metrics and document coverage score historical positive cases; sufficiency metrics also include negatives.',
                'Faults are in-memory evaluator-only perturbations; source files remain unchanged.',
                'Temporal/lexical rules are conservative heuristics, not proof of legal completeness or semantic entailment.'])
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(canonical_json(report))
        print(json.dumps({**{k:v for k,v in report.items() if k!='results'},'results':[{k:v for k,v in r.items() if k!='rows'} for r in results]},indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError,RuntimeError,ImportError) as exc:parser.exit(2,'Stage 6C blocked: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
