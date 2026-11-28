"""Offline Stage 6E evaluation. Exposed Stage 6D data is DEVELOPMENT, not holdout."""
import argparse
import cProfile
import hashlib
import json
import os
from pathlib import Path
import pstats
import statistics
import time
from typing import Literal

from pydantic import Field
from backend.app.ingestion.pipeline import canonical_json, read_bounded, _unique_object, _reject_constant
from .engine import ArchivalIndex, ROOT
from .offline import Dataset, LABEL_STATUS, load_dataset, validate_dataset, ranking_metrics, new_output
from .optimized import OptimizedEvidenceRetriever
from .hardened import HardenedEvidenceRetriever
from .stage6c import ReviewSet, load_review, original_cases
from .stage6d import HeldCase, HeldFault, load_heldout, summarize


class Evaluation(ReviewSet):
    evaluation_version: Literal['stage6e-agent-v1']
    frozen_stage6c_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    frozen_stage6d_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    cases: list[HeldCase] = Field(min_length=1,max_length=100)


def load_new(path,index,hashes):
    payload=read_bounded(path,8*1024*1024)
    spec=Evaluation.model_validate(json.loads(payload.decode('utf-8-sig'),object_pairs_hook=_unique_object,parse_constant=_reject_constant))
    if (spec.frozen_stage6_sha256,spec.frozen_stage6c_sha256,spec.frozen_stage6d_sha256)!=tuple(hashes):raise ValueError('Original frozen data changed')
    binding_data=Dataset.model_validate(dict(schema_version=1,label_status=LABEL_STATUS,human_approved=False,
        scope='New agent-authored Stage 6E source bindings; human-unverified and no publication approval.',
        catalog_sha256=spec.catalog_sha256,qa_sha256=spec.qa_sha256,index_version=spec.index_version,
        references={k:v.model_dump() for k,v in spec.references.items()},
        cases=[dict(id=c.id,category='stage6e-new',question=c.question,insufficient=not c.required_references,
            rationale='Source-authored before retrieval; independent human review pending.',
            relevant=[dict(reference=r,grade=2) for r in c.required_references]) for c in spec.cases]))
    validate_dataset(index,binding_data)
    return spec,hashlib.sha256(payload).hexdigest()


def measure_row(index,case,refs,system,mode):
    active=HeldFault(index,case,refs) if case.fault else index
    runner=OptimizedEvidenceRetriever(active) if system=='stage6d' else HardenedEvidenceRetriever(active)
    started=time.perf_counter();checked=runner.inspect(case.question,mode=mode,diagnostic_retrieval=True)
    elapsed=(time.perf_counter()-started)*1000;result=checked.result
    needed={refs[k].candidate_id for k in case.required_references};docs={refs[k].document_id for k in case.required_references}
    ranking=[p.identifier for p in result.ranked];found={p.candidate.document_id for p in result.ranked}
    positive=case.expected_status=='historical_evidence_available';supported=result.status=='historical_evidence_available'
    return dict(id=case.id,question=case.question,system=system,mode=mode,expected_status=case.expected_status,
        expected_ids=sorted(needed),expected_documents=sorted(docs),assessment=result.metadata(),
        retrieved_documents=sorted(found),metrics=ranking_metrics(ranking,{p:2 for p in needed}) if positive else None,
        required_document_coverage=len(found&docs)/len(docs) if docs else None,
        false_positive_decision=supported and not positive,false_negative_decision=positive and not supported,
        false_supported_decision=supported and (not positive or not needed<={p.identifier for p in result.selected}),
        exact_status_match=result.status==case.expected_status,citations_validated=checked.citation_count,latency_ms=elapsed)


def aggregate(rows):
    summary=summarize(rows)
    summary.update(false_positive_decisions=sum(r.get('false_positive_decision',r['false_supported_decision']) for r in rows),
        false_negative_decisions=sum(r.get('false_negative_decision',r['expected_status']=='historical_evidence_available' and r['assessment']['status']!='historical_evidence_available') for r in rows))
    cross=[r for r in rows if r['metrics'] is not None and len(r['expected_documents'])>1]
    summary['cross_document_cases']=len(cross)
    summary['cross_document_coverage']=statistics.mean(r['required_document_coverage'] for r in cross) if cross else None
    summary['complete_required_passages_rate']=statistics.mean(set(r['expected_ids'])<=set(r['assessment']['ranked_ids']) for r in rows if r['metrics'] is not None) if any(r['metrics'] is not None for r in rows) else None
    return summary


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--model-path',type=Path)
    parser.add_argument('--mode',choices=['bm25','hybrid','both'],default='both')
    parser.add_argument('--new-evaluation',type=Path)
    parser.add_argument('--timing',action='store_true',help='Fresh paired timings, six fixed exposed development cases, twice each')
    parser.add_argument('--profile',action='store_true',help='Profile extra processing; do not combine with ordinary latency claims')
    args=parser.parse_args(argv)
    try:
        target=new_output(ROOT,args.output)
        paths=['backend/retrieval/'+p for p in ['engine.py','scoring.py','evidence.py','offline.py','optimized.py','stage6c.py','stage6d.py','intent.py','hardened.py','stage6e.py','stage6-benchmark.json','stage6c-benchmark.json','stage6d-heldout.json']]
        if args.new_evaluation:paths.append(args.new_evaluation.resolve().relative_to(ROOT).as_posix())
        pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
        original=json.loads((ROOT/'backend/data/qa/stage6e-20261128/baseline-manifest.json').read_bytes())
        if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in original['frozen_files'].items()):raise ValueError('Pre-Stage6E files changed')
        started=time.perf_counter();index=ArchivalIndex(retrieval_mode='bm25');build=time.perf_counter()-started
        frozen,hash0=load_dataset(ROOT/'backend/retrieval/stage6-benchmark.json');validate_dataset(index,frozen)
        c,hash1=load_review(ROOT/'backend/retrieval/stage6c-benchmark.json',index,hash0)
        d,hash2=load_heldout(ROOT/'backend/retrieval/stage6d-heldout.json',index,hash0,hash1)
        sets=[('frozen30',original_cases(frozen),frozen.references),('stage6c31',c.cases,c.references),('exposed_stage6d20',d.cases,d.references)]
        new_hash=None
        if args.new_evaluation:
            spec,new_hash=load_new(args.new_evaluation,index,[hash0,hash1,hash2]);sets=[('new_stage6e',spec.cases,spec.references)]
            freeze=json.loads((ROOT/'backend/data/qa/stage6e-20261128/evaluation-freeze.json').read_bytes())
            if freeze['dataset_sha256']!=new_hash or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in freeze['implementation_pins'].items()):raise ValueError('New evaluation or finalized implementation drifted')
        if args.timing:
            if args.new_evaluation:raise ValueError('Do not select timing samples from new evaluation')
            names={'signed-statement-training-card','time-versus-knowledge-file','conflated-bns-index','superseded-exception','fresh-order-question','missing-photo-standard'}
            sets=[('development_timing',[x for x in d.cases if x.id in names],d.references)]
        modes=['bm25','hybrid'] if args.mode=='both' else [args.mode]
        semantic={'status':'NOT_REQUESTED'}
        if 'hybrid' in modes:
            if not args.model_path:raise ValueError('Explicit existing cached model required')
            os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
            from .semantic import LocalSemantic
            started=time.perf_counter();index.semantic=LocalSemantic(args.model_path,index.passages)
            semantic=dict(status='MEASURED',build_seconds=time.perf_counter()-started,model_sha256=index.semantic.version)
        prior_path=ROOT/'backend/data/qa/stage6d-20261128/paired-comparison.json'
        if hashlib.sha256(prior_path.read_bytes()).hexdigest()!=original['prior_artifacts'][prior_path.relative_to(ROOT).as_posix()]:raise ValueError('Original results changed')
        prior=json.loads(prior_path.read_bytes())
        if (prior['frozen_dataset_sha256'],prior['stage6c_dataset_sha256'],prior['heldout_sha256'],prior['index_version'])!=(hash0,hash1,hash2,index.version):raise ValueError('Baseline question/source bindings differ')
        if 'hybrid' in modes and prior['semantic']['model_sha256']!=semantic['model_sha256']:raise ValueError('Baseline model differs')
        rows=[];baselines=[];profiler=cProfile.Profile() if args.profile else None
        if profiler:profiler.enable()
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.with_suffix('.progress.jsonl').open('x',encoding='utf-8') as progress:
            for mode in modes:
                for name,cases,refs in sets:
                    for repetition in range(2 if args.timing else 1):
                        for n,case in enumerate(cases):
                            paired=args.timing or bool(args.new_evaluation)
                            systems=['stage6d','stage6e'] if paired and (n+repetition)%2==0 else ['stage6e','stage6d'] if paired else ['stage6e']
                            for system in systems:
                                result=dict(dataset=name,repetition=repetition,**measure_row(index,case,refs,system,mode))
                                rows.append(result);progress.write(json.dumps(result,ensure_ascii=True)+'\n');progress.flush()
                            if not args.new_evaluation and not args.timing:
                                prior_name={'frozen30':'frozen','stage6c31':'stage6c','exposed_stage6d20':'heldout'}[name]
                                old=next(r for r in prior['rows'] if r['dataset']==prior_name and r['mode']==mode and r['system']=='stage6d' and r['id']==case.id)
                                if (old['expected_status'],old['expected_ids'])!=(case.expected_status,sorted(refs[k].candidate_id for k in case.required_references)):raise ValueError('Baseline labels differ')
                                baselines.append(dict(old,dataset=name,latency_comparison_permitted=False,quality_reused_from_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest()))
                            if (n+1)%5==0 or n+1==len(cases):print(json.dumps(dict(dataset=name,mode=mode,repetition=repetition,completed=n+1,cases=len(cases))),flush=True)
        profile=None
        if profiler:
            profiler.disable();stats=pstats.Stats(profiler);functions=[]
            for (file,line,func),(primitive,calls,selftime,cumulative,callers) in stats.stats.items():
                if Path(file).name in {'intent.py','hardened.py','optimized.py'}:
                    functions.append(dict(file=Path(file).name,function=func,line=line,calls=calls,self_seconds=selftime,cumulative_seconds=cumulative))
            profile=sorted(functions,key=lambda r:-r['cumulative_seconds'])
        summaries=[]
        for name,_,_ in sets:
            for mode in modes:
                for system in (['stage6d','stage6e'] if args.timing or args.new_evaluation or baselines else ['stage6e']):
                    batch=[r for r in rows+baselines if r['dataset']==name and r['mode']==mode and r['system']==system]
                    summaries.append(dict(dataset=name,mode=mode,system=system,latency_comparison_permitted=bool(args.timing or args.new_evaluation),**aggregate(batch)))
        if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise ValueError('Evaluation inputs changed during run')
        report=dict(schema_version=1,evaluation_version='stage6e-agent-v1',provider_calls=0,downloads=0,human_approved=False,publication_authorized=False,legal_currentness='unknown',
            original_hashes=[hash0,hash1,hash2],new_evaluation_sha256=new_hash,implementation_pins=pins,index_version=index.version,bm25_build_seconds=build,semantic=semantic,
            prior_result_sha256=hashlib.sha256(prior_path.read_bytes()).hexdigest(),baseline_quality_reused=bool(baselines),baseline_latency_reused_for_comparison=False,
            conditions='Explicit offline cached model only; both fresh timing systems reuse Stage 6D request snapshots and validate citations before source/trust handoff. OS caches not flushed.',
            dataset_roles=dict(frozen30='frozen development',stage6c31='frozen development',exposed_stage6d20='previous holdout now exposed development',new_stage6e='source-authored after implementation finalization, human-unverified'),
            labels='Agent authored; no independent human/legal accuracy claim. No tuning permitted on new evaluation results.',
            timing=args.timing,profile=profile,summaries=summaries,rows=rows,baseline_rows=baselines)
        with target.open('xb') as f:f.write(canonical_json(report))
        print(json.dumps({k:v for k,v in report.items() if k not in {'rows','baseline_rows','implementation_pins','profile'}},indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError,RuntimeError,ImportError) as exc:parser.exit(2,'Stage 6E blocked: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
