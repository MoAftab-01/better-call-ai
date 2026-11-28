"""Offline-only Stage 6F evaluation and release-boundary measurements.
Quality batches share a validated source view; final source/trust validation is
mandatory before accepting the batch. Request latency uses complete wrappers.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Literal
from pydantic import Field

from backend.app.ingestion.pipeline import canonical_json,read_bounded,_unique_object,_reject_constant
from backend.public_corpus.measure import memory
from .engine import ArchivalIndex,ROOT
from .offline import Dataset,LABEL_STATUS,load_dataset,validate_dataset,ranking_metrics,make_citation,validate_citation,new_output
from .optimized import RequestSources,request_index
from .hardened import HardenedPolicy,HardenedEvidenceRetriever
from .passage_level import PassagePolicy,PassageEvidenceRetriever
from .stage6c import load_review,original_cases
from .stage6d import HeldFault
from .stage6e import Evaluation,load_new,aggregate
from .stage6d import load_heldout


class FreshEvaluation(Evaluation):
    evaluation_version: Literal['stage6f-agent-v1']
    frozen_stage6e_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


def load_fresh(path,index,hashes):
    payload=read_bounded(path,8*1024*1024)
    spec=FreshEvaluation.model_validate(json.loads(payload.decode('utf-8-sig'),object_pairs_hook=_unique_object,parse_constant=_reject_constant))
    if [spec.frozen_stage6_sha256,spec.frozen_stage6c_sha256,spec.frozen_stage6d_sha256,spec.frozen_stage6e_sha256]!=hashes:raise ValueError('Prior dataset hashes differ')
    data=Dataset.model_validate(dict(schema_version=1,label_status=LABEL_STATUS,human_approved=False,
        scope='Stage 6F source-first provisional bindings; no human approval.',catalog_sha256=spec.catalog_sha256,qa_sha256=spec.qa_sha256,index_version=spec.index_version,
        references={k:v.model_dump() for k,v in spec.references.items()},cases=[dict(id=c.id,category='stage6f',question=c.question,insufficient=not c.required_references,rationale='Authored from source before query retrieval; human verification pending.',relevant=[dict(reference=r,grade=2) for r in c.required_references]) for c in spec.cases]))
    validate_dataset(index,data)
    return spec,hashlib.sha256(payload).hexdigest()


def record(case,refs,result,citations,system,mode,elapsed):
    need={refs[k].candidate_id for k in case.required_references};docs={refs[k].document_id for k in case.required_references}
    ranking=[p.identifier for p in result.ranked];selected={p.identifier for p in result.selected}
    actual_docs={p.candidate.document_id for p in result.ranked};selected_docs={p.candidate.document_id for p in result.selected}
    positive=case.expected_status=='historical_evidence_available';supported=result.status=='historical_evidence_available'
    return dict(id=case.id,question=case.question,system=system,mode=mode,expected_status=case.expected_status,expected_ids=sorted(need),expected_documents=sorted(docs),
        assessment=result.metadata(),retrieved_documents=sorted(actual_docs),metrics=ranking_metrics(ranking,{p:2 for p in need}) if positive else None,
        required_document_coverage=len(actual_docs&docs)/len(docs) if docs else None,
        selected_document_coverage=len(selected_docs&docs)/len(docs) if positive else None,
        selected_passage_coverage=len(selected&need)/len(need) if positive else None,
        all_required_selected=need<=selected if positive else None,
        false_positive_decision=supported and not positive,false_negative_decision=positive and not supported,
        false_supported_decision=supported and (not positive or not need<=selected),exact_status_match=result.status==case.expected_status,
        citations_validated=citations,latency_ms=elapsed)


def summarize(rows):
    import statistics
    value=aggregate(rows);positives=[r for r in rows if r['metrics'] is not None]
    for key in ['selected_passage_coverage','selected_document_coverage','all_required_selected']:
        value[key]=statistics.mean(r[key] for r in positives) if positives else None
    return value


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=['bm25','hybrid','both'],default='both')
    parser.add_argument('--model-path',type=Path)
    parser.add_argument('--new-evaluation',type=Path)
    parser.add_argument('--timing',action='store_true')
    parser.add_argument('--memory-only',choices=['stage6e','stage6f'])
    args=parser.parse_args(argv)
    try:
        target=new_output(ROOT,args.output);before=memory()
        original=json.loads((ROOT/'backend/data/qa/stage6f-20261128/baseline-manifest.json').read_bytes())
        if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in original['frozen_files'].items()):raise ValueError('Prior Stage 6 file changed')
        paths=list(original['frozen_files'])+['backend/retrieval/passage_level.py','backend/retrieval/stage6f.py','backend/tests/test_stage6f_passages.py']
        if args.new_evaluation:paths.append(args.new_evaluation.resolve().relative_to(ROOT).as_posix())
        pins={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
        started=time.perf_counter();index=ArchivalIndex(retrieval_mode='bm25');build=time.perf_counter()-started
        if not index.catalog:raise ValueError('Exact private source bundle unavailable')
        after_index=memory()
        if args.memory_only:
            started=time.perf_counter();policy=(HardenedPolicy if args.memory_only=='stage6e' else PassagePolicy)(index)
            report=dict(system=args.memory_only,bm25_build_seconds=build,policy_build_seconds=time.perf_counter()-started,
                before=before,after_index=after_index,after_policy=memory(),passages=len(index.passages),semantic_model_loaded=False,
                note='Fresh-process BM25 policy footprint, not a Render/public deployment capacity guarantee')
        else:
            a,h0=load_dataset(ROOT/'backend/retrieval/stage6-benchmark.json');validate_dataset(index,a)
            b,h1=load_review(ROOT/'backend/retrieval/stage6c-benchmark.json',index,h0)
            c,h2=load_heldout(ROOT/'backend/retrieval/stage6d-heldout.json',index,h0,h1)
            d,h3=load_new(ROOT/'backend/retrieval/stage6e-evaluation.json',index,[h0,h1,h2])
            sets=[('frozen30',original_cases(a),a.references),('stage6c31',b.cases,b.references),('exposed_d20',c.cases,c.references),('exposed_e20',d.cases,d.references)]
            fresh_hash=None
            if args.new_evaluation:
                if args.timing:raise ValueError('Timing selection must not use new evaluation')
                spec,fresh_hash=load_fresh(args.new_evaluation,index,[h0,h1,h2,h3])
                freeze=json.loads((ROOT/'backend/data/qa/stage6f-20261128/evaluation-freeze.json').read_bytes())
                if fresh_hash!=freeze['dataset_sha256'] or any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in freeze['implementation_pins'].items()):raise ValueError('Finalized policy/new labels drifted')
                sets=[('new_stage6f',spec.cases,spec.references)]
            if args.timing:
                names={'document-destruction-file','leading-question-reading','two-evidence-topics','displaced-exception-claim','accounting-year-procedure'}
                sets=[('timing_e',[v for v in d.cases if v.id in names],d.references),('timing_d',[v for v in c.cases if v.id=='time-versus-knowledge-file'],c.references)]
            modes=['bm25','hybrid'] if args.mode=='both' else [args.mode];semantic={'status':'NOT_REQUESTED'}
            if 'hybrid' in modes:
                if not args.model_path:raise ValueError('Explicit cached model required; no downloads')
                os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
                from .semantic import LocalSemantic
                started=time.perf_counter();index.semantic=LocalSemantic(args.model_path,index.passages)
                semantic=dict(status='MEASURED',build_seconds=time.perf_counter()-started,model_sha256=index.semantic.version)
            rows=[];target.parent.mkdir(parents=True,exist_ok=True)
            with target.with_suffix('.progress.jsonl').open('x',encoding='utf-8') as progress:
                for mode in modes:
                    view=None
                    try:
                        if not args.timing:
                            view=RequestSources(index);active=request_index(index,view)
                            policies={'stage6e':HardenedPolicy(active),'stage6f':PassagePolicy(active)}
                        for name,cases,refs in sets:
                            for repetition in range(2 if args.timing else 1):
                                for n,case in enumerate(cases):
                                    systems=['stage6e','stage6f'] if (n+repetition)%2==0 else ['stage6f','stage6e']
                                    for system in systems:
                                        use=HeldFault(index if args.timing else active,case,refs) if case.fault else index if args.timing else active
                                        started=time.perf_counter()
                                        if args.timing:
                                            checked=(HardenedEvidenceRetriever if system=='stage6e' else PassageEvidenceRetriever)(use).inspect(case.question,mode=mode,diagnostic_retrieval=True)
                                            result,count=checked.result,checked.citation_count
                                        else:
                                            policy=policies[system];policy.index=use
                                            result=policy.assess(case.question,mode=mode,diagnostic_retrieval=True);count=0
                                            for num,p in enumerate(result.ranked,1):
                                                validate_citation(use,make_citation(use,p,num),num,{x.identifier for x in result.ranked});count+=1
                                        row=dict(dataset=name,repetition=repetition,provisional_until_final_batch_check=not args.timing,**record(case,refs,result,count,system,mode,(time.perf_counter()-started)*1000))
                                        rows.append(row);progress.write(json.dumps(row,ensure_ascii=True)+'\n');progress.flush()
                                    if (n+1)%5==0 or n+1==len(cases):print(json.dumps(dict(dataset=name,mode=mode,repetition=repetition,completed=n+1,cases=len(cases))),flush=True)
                        if view is not None:
                            view.refresh_sources() # Reject the ENTIRE batch on source/trust/review change.
                            for accepted in rows:
                                if accepted['mode']==mode:accepted['provisional_until_final_batch_check']=False
                    finally:
                        if view is not None:view.close()
            summaries=[]
            for name,_,_ in sets:
                for mode in modes:
                    for system in ['stage6e','stage6f']:
                        summaries.append(dict(dataset=name,mode=mode,system=system,**summarize([r for r in rows if (r['dataset'],r['mode'],r['system'])==(name,mode,system)])))
            report=dict(schema_version=1,evaluation_version='stage6f-agent-v1',human_approved=False,publication_authorized=False,legal_currentness='unknown',provider_calls=0,downloads=0,
                original_dataset_hashes=[h0,h1,h2,h3],new_dataset_sha256=fresh_hash,implementation_pins=pins,index_version=index.version,
                bm25_build_seconds=build,semantic=semantic,memory_before=before,memory_after_index=after_index,memory_end=memory(),
                timing=args.timing,latency_scope='Full per-request source/citation/final-handoff validation' if args.timing else 'Quality batch policy timing only; shared source preflight/final validation excluded; NOT request latency',
                final_batch_source_check='PASS' if not args.timing else 'PER_REQUEST',
                dataset_roles='30/31 frozen development; Stage6D/6E exposed diagnostic development; new Stage6F source-authored after finalization, provisional agent labels',
                labels='Not independent expert/legal truth. No tuning after new evaluation.',summaries=summaries,rows=rows)
        if any(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise ValueError('Inputs changed during run')
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(canonical_json(report))
        print(json.dumps({k:v for k,v in report.items() if k not in {'rows','implementation_pins'}},indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError,RuntimeError,ImportError) as exc:parser.exit(2,'Stage 6F blocked: '+str(exc)+'\n')


if __name__=='__main__':raise SystemExit(main())
