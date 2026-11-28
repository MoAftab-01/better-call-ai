"""Offline QA tests: SYNTHETIC sources only, no real approval or provider calls."""
from dataclasses import replace
import json
import math
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.chat.api import create_app
from backend.chat.provider import GroqProvider
from backend.retrieval import offline
from backend.retrieval.offline import Dataset, ranking_metrics, validate_dataset, make_citation, validate_citation, run, new_output
from backend.tests.chat_fixtures import index, mvp_seed


@pytest.fixture
def labels(index):
    p=next(p for p in index.passages if p.instrument=='S.O. 850(E)')
    c=p.candidate
    return dict(schema_version=1,label_status=offline.LABEL_STATUS,human_approved=False,
        scope='SYNTHETIC software relevance fixture only, NOT LAW; no real approvals.',
        catalog_sha256=index.catalog.digest,qa_sha256=index.catalog.qa_hash,index_version=index.version,
        references={'synthetic':dict(candidate_id=c.candidate_id,document_id=c.document_id,
            raw_sha256=c.raw_sha256,processed_sha256=c.processed_sha256,span=c.spans[0].model_dump(),
            rationale='SYNTHETIC source independently chosen by fixture identity, not ranked results.')},
        cases=[dict(id='synthetic-supported',category='synthetic',question='BNS commencement notification',
            insufficient=False,rationale='SYNTHETIC matching notification fixture only.',relevant=[dict(reference='synthetic',grade=2)]),
            dict(id='synthetic-outside',category='synthetic-outside',question='consumer rights',insufficient=True,
                rationale='The synthetic index cannot support consumer rights.',relevant=[])])


def test_metrics_are_rank_sensitive_and_graded():
    result=ranking_metrics(['unjudged','a','other','b'],{'a':2,'b':1})
    assert result['recall_at_3']==.5 and result['recall_at_5']==1 and result['mrr']==.5
    assert result['ndcg_at_5']==pytest.approx((3/math.log2(3)+1/math.log2(5))/(3+1/math.log2(3)))
    assert ranking_metrics([],{'a':1})==dict(recall_at_3=0,recall_at_5=0,mrr=0,ndcg_at_5=0)


@pytest.mark.parametrize('ranking,grades',[(['a','a'],{'a':1}),([],{ }),([] ,{'a':True}),([] ,{'a':3})])
def test_invalid_metric_inputs_rejected(ranking,grades):
    with pytest.raises(ValueError):ranking_metrics(ranking,grades)


def test_reproducible_offline_run_never_calls_provider(index,labels,monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Provider called by offline evaluation')
    monkeypatch.setattr(GroqProvider,'select',forbidden)
    class Clock:
        value=0
        def __call__(self):self.value+=.125;return self.value
    result=run(index,labels,repetitions=3,clock=Clock())
    assert result['cases']==2 and result['supported_cases']==1 and result['insufficient_cases']==1
    assert all(v==1 for v in result['metrics'].values())
    assert result['insufficient_evidence_rate']==1 and result['citation_checks_total']==1
    assert result['latency']['samples']==6 and result['latency']['median_ms']==125
    assert result['deterministic_rankings'] and result['mrr_cutoff']==5
    encoded=json.dumps(result)
    assert all(p.text not in encoded for p in index.passages)


@pytest.mark.parametrize('key',['catalog_sha256','qa_sha256','index_version'])
def test_stale_dataset_version_rejected(index,labels,key):
    labels[key]='a'*64
    with pytest.raises(ValueError):validate_dataset(index,labels)


@pytest.mark.parametrize('field,value',[
    ('candidate_id','passage_'+'a'*64),('document_id','doc_'+'a'*64),
    ('raw_sha256','a'*64),('processed_sha256','a'*64)])
def test_altered_gold_binding_rejected(index,labels,field,value):
    labels['references']['synthetic'][field]=value
    with pytest.raises(ValueError):validate_dataset(index,labels)


@pytest.mark.parametrize('field,value',[('physical_page',2),('start_line',1),('end_line',999),('page_id','unrelated'),('text_sha256','a'*64)])
def test_exact_gold_page_line_hash_binding(index,labels,field,value):
    labels['references']['synthetic']['span'][field]=value
    with pytest.raises(ValueError):validate_dataset(index,labels)


@pytest.mark.parametrize('change',['human','status','duplicate-case','unknown-ref','duplicate-ref','empty-supported','nonempty-insufficient'])
def test_labels_cannot_manufacture_approval_or_ambiguous_judgments(labels,change):
    if change=='human':labels['human_approved']=True
    if change=='status':labels['label_status']='legally_verified'
    if change=='duplicate-case':labels['cases'].append(labels['cases'][0])
    if change=='unknown-ref':labels['cases'][0]['relevant'][0]['reference']='missing'
    if change=='duplicate-ref':labels['cases'][0]['relevant']*=2
    if change=='empty-supported':labels['cases'][0]['relevant']=[]
    if change=='nonempty-insufficient':labels['cases'][1]['relevant']=labels['cases'][0]['relevant']
    with pytest.raises(ValueError):Dataset.model_validate(labels)


@pytest.mark.parametrize('field,value',[
    ('id','E9'),('candidate_id','passage_'+'a'*64),('document_id','doc_'+'a'*64),
    ('quote','SYNTHETIC fabricated quote - NOT LAW'),('context_text','SYNTHETIC altered context'),
    ('context_text_sha256','a'*64),('source_url','https://example.invalid/wrong-source'),
    ('issuing_authority','SYNTHETIC WRONG AUTHORITY'),('publication_date','2000-01-01'),
    ('raw_sha256','a'*64),('processed_sha256','a'*64),('catalog_sha256','a'*64),('qa_sha256','a'*64),
    ('text_sha256','a'*64),('pdf_page',2),('page_id','unrelated'),('start_line',99),('end_line',999),
    ('title','SYNTHETIC Wrong title'),('instrument','S.O. 999(E)'),('printed_number_unverified','999'),
    ('attribution','printed_label'),('evidence_status','VERIFIED_REVIEWED'),('version_description','current law verified')])
def test_citation_tampering_rejected(index,field,value):
    p=index.passages[0];citation=make_citation(index,p,1).model_copy(update={field:value})
    with pytest.raises(ValueError):validate_citation(index,citation,1,{p.identifier})


def test_supported_identifier_required_and_document_only_preserved(index):
    p=index.passages[0];citation=make_citation(index,p,1)
    assert validate_citation(index,citation,1,{p.identifier})
    assert citation.attribution=='document_only' and citation.evidence_status=='ARCHIVAL_UNVERIFIED'
    with pytest.raises(ValueError):validate_citation(index,citation,1,set())
    with pytest.raises(ValueError):validate_citation(index,citation,0,{p.identifier})


@pytest.mark.parametrize('claim,currentness',[('VERIFIED_REVIEWED','unknown'),('ARCHIVAL_UNVERIFIED','current')])
def test_historical_text_never_becomes_verified_or_current_claim(index,claim,currentness):
    p=index.passages[0]
    with pytest.raises(ValueError):validate_citation(index,make_citation(index,p,1),1,{p.identifier},evidence_claim=claim,legal_currentness=currentness)


@pytest.mark.parametrize('kind',['raw','processed'])
def test_source_version_change_rejected(index,labels,kind):
    p=index.passages[0];citation=make_citation(index,p,1)
    path=index.root/(p.candidate.raw_path if kind=='raw' else p.candidate.processed_path)
    path.chmod(0o600);path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError):validate_citation(index,citation,1,{p.identifier})
    with pytest.raises(ValueError):validate_dataset(index,labels)


def test_cached_text_and_qa_exclusions_cannot_escape(index,monkeypatch):
    p=index.passages[0];citation=make_citation(index,p,1)
    index.passages[0]=replace(p,text='SYNTHETIC altered cached source, NOT LAW')
    with pytest.raises(ValueError):validate_citation(index,citation,1,{p.identifier})
    index.passages[0]=p
    monkeypatch.setattr(offline,'exclusion_reasons',lambda *args:['SYNTHETIC_EXCLUSION'])
    with pytest.raises(ValueError):validate_citation(index,citation,1,{p.identifier})


def test_missing_source_does_not_count_as_successful_empty_evaluation(index,labels):
    path=index.root/index.passages[0].candidate.raw_path
    path.chmod(0o600);path.unlink()
    with pytest.raises(ValueError):run(index,labels)


def test_negative_case_failure_is_reported_without_relabelling(index,labels):
    labels['cases'][1]['question']='BNSS commencement notification'
    result=run(index,labels,repetitions=1)
    assert result['insufficient_evidence_rate']==0
    assert result['rows'][1]['result']=='unexpected_archival_hits'
    assert result['metrics']['recall_at_5']==1  # Negative cases do not dilute the relevance denominator.


def test_hybrid_and_repeat_limits_fail_explicitly(index,labels):
    with pytest.raises(ValueError):run(index,labels,mode='hybrid')
    for n in [0,6,True]:
        with pytest.raises(ValueError):run(index,labels,repetitions=n)


def test_changed_rankings_are_not_silently_averaged(index,labels,monkeypatch):
    original=index.search;calls=0
    def unstable(*args,**kwargs):
        nonlocal calls
        calls+=1;return original(*args,**kwargs) if calls%2 else []
    monkeypatch.setattr(index,'search',unstable)
    with pytest.raises(ValueError,match='Nondeterministic'):run(index,labels,repetitions=2)


def test_cli_output_is_private_new_and_has_no_source_excerpts(index,labels,monkeypatch):
    dataset=index.root/'docs/synthetic-evaluation.json';dataset.write_text(json.dumps(labels),encoding='utf-8')
    target=index.root/'backend/data/qa/synthetic-result.json'
    monkeypatch.setattr(offline,'ROOT',index.root)
    monkeypatch.setattr(offline,'ArchivalIndex',lambda **kwargs:index)
    assert offline.main(['--dataset',str(dataset),'--output',str(target),'--repetitions','1'])==0
    result=json.loads(target.read_bytes())
    assert result['provider_calls']==0 and result['human_approved'] is False and result['publication_authorized'] is False
    assert result['semantic']['status']=='NOT_MEASURED'
    assert all(p.text not in target.read_text() for p in index.passages)
    before=target.read_bytes()
    with pytest.raises(SystemExit) as exc:offline.main(['--dataset',str(dataset),'--output',str(target)])
    assert exc.value.code==2 and target.read_bytes()==before
    with pytest.raises(ValueError):new_output(index.root,index.root/'docs/forbidden.json')
    with pytest.raises(ValueError):new_output(index.root,index.root/'backend/data/qa/../forbidden.json')


def test_cli_missing_bundle_is_blocked_without_creating_success(index,labels,monkeypatch):
    dataset=index.root/'docs/synthetic-evaluation.json';dataset.write_text(json.dumps(labels),encoding='utf-8')
    target=index.root/'backend/data/qa/missing-result.json'
    monkeypatch.setattr(offline,'ROOT',index.root)
    monkeypatch.setattr(offline,'ArchivalIndex',lambda **kwargs:type('Missing',(),{'catalog':None})())
    with pytest.raises(SystemExit) as exc:offline.main(['--dataset',str(dataset),'--output',str(target)])
    assert exc.value.code==2 and not target.exists()


def test_public_runtime_remains_pending_and_never_loads_offline_corpus(monkeypatch,tmp_path):
    import backend.retrieval.engine as engine
    monkeypatch.setattr(engine,'ArchivalIndex',lambda *args,**kwargs:(_ for _ in ()).throw(AssertionError('Private archive loaded')))
    for name,value in dict(KANOON_ENV='production',CORPUS_KIND='public',RETRIEVAL_MODE='bm25',
            PUBLIC_CORPUS_DIR=str(tmp_path/'ABSENT'),KANOON_ACCESS_TOKEN='SYNTHETIC_RESEARCH_TOKEN_NOT_REAL_2026',
            DEMO_ENABLED='true',DEMO_PROVIDER='deterministic',AI_ASSISTANT_ENABLED='false').items():monkeypatch.setenv(name,value)
    for name in ['PUBLIC_CORPUS_MANIFEST_SHA256','PUBLIC_CORPUS_APPROVAL_FILE','PUBLIC_CORPUS_APPROVAL_SHA256','PUBLIC_CORPUS_SIGNER_PUBLIC_KEY','KANOON_OPS_TOKEN']:monkeypatch.delenv(name,raising=False)
    client=TestClient(create_app())
    assert client.get('/api/health').status_code==200
    ready=client.get('/api/ready');assert ready.status_code==503 and ready.json()['research_state']=='publication_pending'
    assert client.post('/api/demo/chat',json={'message':'SYNTHETIC example'}).status_code==200
    assert client.post('/api/chat',json={'message':'SYNTHETIC question'}).status_code==401
    assert client.get('/api/ops/metrics').status_code==404
    inventory=json.loads((Path(__file__).resolve().parents[2]/'docs/deployment-publication.json').read_bytes())
    assert not any('offline.py' in name or 'notification_review.py' in name or 'stage6-benchmark' in name for name in inventory['runtime_files'])


@pytest.mark.parametrize('change',['none','missing','duplicate','instrument','url','date'])
def test_dossier_namespace_join_requires_exact_source_identity(index,change):
    from backend.retrieval.notification_review import rights_binding
    c=index.passages[0].candidate
    row=dict(document_id='doc_'+c.raw_sha256,raw_sha256=c.raw_sha256,
        instrument=c.original_identifiers['notification_number'],official_source_url=c.source_metadata.source_url,
        publication_date=str(c.source_metadata.publication_date) if c.source_metadata.publication_date else None)
    assert row['document_id']!=c.document_id  # Public-source and ingestion IDs are distinct namespaces.
    rows=[row]
    if change=='missing':rows=[]
    if change=='duplicate':rows=[row,row]
    if change=='instrument':row['instrument']='S.O. 999(E)'
    if change=='url':row['official_source_url']='https://example.invalid/wrong-source'
    if change=='date':row['publication_date']='2000-01-01'
    if change=='none':assert rights_binding(rows,c)==row
    else:
        with pytest.raises(ValueError):rights_binding(rows,c)


@pytest.mark.parametrize('payload',['{"schema_version":1,"schema_version":1}','{"schema_version":NaN}'])
def test_dataset_json_ambiguity_rejected(tmp_path,payload):
    path=tmp_path/'ambiguous-synthetic.json';path.write_text(payload,encoding='utf-8')
    with pytest.raises(ValueError):offline.load_dataset(path)


def test_dataset_hash_is_same_bounded_snapshot(index,labels,tmp_path,monkeypatch):
    import hashlib
    path=tmp_path/'synthetic-labels.json';payload=json.dumps(labels).encode();path.write_bytes(payload)
    original=offline.read_bounded;calls=[]
    def bounded(p,limit):calls.append(limit);return original(p,limit)
    monkeypatch.setattr(offline,'read_bounded',bounded)
    data,digest=offline.load_dataset(path)
    assert digest==hashlib.sha256(payload).hexdigest() and data.cases[0].id=='synthetic-supported'
    assert calls==[8*1024*1024]
