"""Stage 6E tests: SYNTHETIC software fixtures, never legal approvals."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.retrieval.intent import content_words, plan, scope_text, temporal_class
from backend.retrieval.hardened import HardenedPolicy, HardenedEvidenceRetriever
from backend.tests.chat_fixtures import index, mvp_seed
from backend.tests.test_stage6c_evidence import mixed, mixed_seed

DATES=[dict(publication_date='2023-12-25'),dict(publication_date='2024-02-24')]

@pytest.mark.parametrize('question',[
 'Has anything superseded the BNS commencement exception?',
 'Has a fresh Gazette order removed the BNS commencement exception?',
 'Have any BNSS restrictions been rescinded?',
 'Was the BSA commencement notification replaced?',
 'Does a new order override the BNS exception?',
 'Has the BNSS entry been withdrawn?',
 'Does the BSA govern next month?',
 'Does BNS apply tomorrow?',
 'What was BNSS law last year?',
 'Is BNS section 106(2) in force?',
 'Have there been any later BSA amendments?',
])
def test_unverified_time_and_update_claims_need_more_than_original_text(question):
    assert temporal_class(question,DATES)=='current_or_later'

@pytest.mark.parametrize('question',[
 'Find the original BSA paragraph, without treating it as a statement of present legal position.',
 'Inspect the original BNS text, without claiming current validity.',
 'What does the original BNSS text say about removing property marks?',
 'Quote the original BNS notification paragraph.',
])
def test_narrow_archival_tasks_remain_historical(question):
    assert temporal_class(question,DATES)=='historical_text'

@pytest.mark.parametrize('question',[
 'Find original BSA text, without claiming current validity, but is it in force now?',
 'Find original BNS text, without claiming current validity and has the exception been removed?',
 'Is the BSA currently valid?',
])
def test_meta_disclaimer_cannot_hide_an_actual_current_request(question):
    assert temporal_class(question,DATES)=='current_or_later'

@pytest.mark.parametrize('forms,root',[
 ('refusal refuses refused refusing','refuse'),
 ('required requires requiring','require'),
 ('made makes maker making','make'),
 ('counterfeited counterfeits counterfeiting','counterfeit'),
 ('excluded excluding exclusion','exclude'),
 ('diligence diligently','diligent'),
 ('prosecuting prosecution prosecuted','prosecute'),
 ('contradicting contradicted','contradict'),
 ('corroborating corroborated','corroborate'),
 ('impeaching impeached','impeach'),
 ('confirming confirmed','confirm'),
 ('proved proving proven','prove'),
])
def test_inspectable_english_inflections(forms,root):
    assert content_words(forms)=={root}


def test_framing_removal_does_not_drop_substantive_card_or_material():
    assert 'card' in content_words('credit card')
    assert 'material' in content_words('material evidence')
    assert 'training' not in content_words('a training card')
    assert 'card' not in content_words('a training card')
    assert len(plan('An original BNS study index conflates refusal to sign statements with counterfeit property marks. Locate the two separate archival passages.'))==2

@pytest.mark.parametrize('question',[
 'Locate original BNS material for a training card about a Judge acting judicially with care.',
 'Find original BNSS material for a history exercise about interpreting evidence in a language understood by the accused.',
 'A source-reading seminar needs the original BSA paragraph on communications during marriage.',
 'Compare original BNSS interpreting evidence with original BSA marital communications; provide archival material for each training card.',
])
def test_historical_paraphrases_are_not_blanket_rejected(mixed,question):
    result=HardenedEvidenceRetriever(mixed).assess(question)
    assert result.status=='historical_evidence_available'
    assert result.covered_groups==result.required_groups
    assert not result.human_approved and not result.publication_authorized


def test_current_guard_is_independent_of_matching_historical_hits(index,monkeypatch):
    p=next(p for p in index.passages if p.instrument=='S.O. 850(E)')
    monkeypatch.setattr(HardenedPolicy,'_rank',lambda *a,**k:[p])
    r=HardenedEvidenceRetriever(index).assess('Has anything superseded the BNS commencement exception?',diagnostic_retrieval=True)
    assert r.ranked and not r.selected and r.status=='insufficient_current_evidence'


def test_meta_disclaimer_can_inspect_original_notification(index):
    r=HardenedEvidenceRetriever(index).assess('Find the original BSA commencement paragraph, without treating it as a statement of present legal position.')
    assert r.status=='historical_evidence_available' and len(r.selected)==1

@pytest.mark.parametrize('question',[
 'Compare BNSS evidence interpretation with BSA facial recognition algorithm standards.',
 'Can original BNS judicial action settle civil trademark registration criteria?',
 'An index assumes IPC and BNS have identical numbering. Supply their correspondence.',
 'Compare original BNSS evidence interpretation with IPC abduction by force.',
])
def test_missing_or_inapplicable_required_evidence_is_not_padded(mixed,question):
    r=HardenedEvidenceRetriever(mixed).assess(question)
    assert r.status=='insufficient_evidence' and not r.selected


def test_relevant_one_clause_is_not_complete_comparison(mixed,monkeypatch):
    original=mixed.search
    monkeypatch.setattr(mixed,'search',lambda *a,**k:[p for p in original(*a,**k) if 'Nagarik' in p.title])
    r=HardenedEvidenceRetriever(mixed).assess('Compare BNSS evidence interpretation and BSA marital communications.')
    assert r.status=='insufficient_evidence' and not r.selected

@pytest.mark.parametrize('kind',['quote','qualifier','hash','identifier','url'])
def test_no_tampered_candidate_can_escape(index,monkeypatch,kind):
    p=next(p for p in index.passages if p.instrument=='S.O. 848(E)')
    if kind=='quote':bad=replace(p,text='SYNTHETIC altered quotation NOT LAW')
    elif kind=='qualifier':bad=replace(p,text=p.text.split('except')[0])
    elif kind=='hash':bad=replace(p,candidate=p.candidate.model_copy(update={'raw_sha256':'0'*64}))
    elif kind=='identifier':bad=replace(p,candidate=p.candidate.model_copy(update={'document_id':'doc_'+'0'*64}))
    else:bad=replace(p,candidate=p.candidate.model_copy(update={'source_metadata':p.candidate.source_metadata.model_copy(update={'source_url':'https://example.invalid/wrong'})}))
    monkeypatch.setattr(index,'search',lambda *a,**k:[bad])
    result=HardenedEvidenceRetriever(index).assess('Original BNSS notification')
    assert result.status=='source_integrity_failed' and not result.selected


def test_exclusion_gate_still_runs(index,monkeypatch):
    import backend.retrieval.evidence as original
    monkeypatch.setattr(original,'exclusion_reasons',lambda *a:['SYNTHETIC_EXCLUDED'])
    assert HardenedEvidenceRetriever(index).assess('Original BNS notification').status=='source_integrity_failed'


def test_changed_source_at_handoff_fails_closed(index,monkeypatch):
    original=HardenedPolicy.assess
    path=index.root/index.passages[0].candidate.raw_path
    def mutate(self,*a,**k):
        result=original(self,*a,**k)
        path.chmod(0o600);path.write_bytes(path.read_bytes()+b' SYNTHETIC TAMPER')
        return result
    monkeypatch.setattr(HardenedPolicy,'assess',mutate)
    assert HardenedEvidenceRetriever(index).assess('Original BNS notification').status=='source_integrity_failed'


def test_review_revocation_boundary_not_cached(index,monkeypatch):
    import backend.retrieval.optimized as opt
    state=[()];original=HardenedPolicy.assess
    monkeypatch.setattr(opt,'checkpoint',lambda catalog:state[0])
    def change(self,*a,**k):
        result=original(self,*a,**k);state[0]=('SYNTHETIC_CHANGED_CHECKPOINT',);return result
    monkeypatch.setattr(HardenedPolicy,'assess',change)
    assert HardenedEvidenceRetriever(index).assess('Original BNS notification').status=='source_integrity_failed'


def test_public_runtime_does_not_import_or_use_hardened_retrieval(monkeypatch,tmp_path):
    from backend.chat.api import create_app
    import backend.retrieval.engine as engine
    monkeypatch.setattr(engine,'ArchivalIndex',lambda *a,**k:(_ for _ in ()).throw(AssertionError('Private sources accessed')))
    for k,v in dict(KANOON_ENV='production',CORPUS_KIND='public',RETRIEVAL_MODE='bm25',PUBLIC_CORPUS_DIR=str(tmp_path/'ABSENT'),KANOON_ACCESS_TOKEN='SYNTHETIC_ACCESS_TOKEN_NOT_REAL_STAGE6E',AI_ASSISTANT_ENABLED='false').items():monkeypatch.setenv(k,v)
    for k in ['PUBLIC_CORPUS_MANIFEST_SHA256','PUBLIC_CORPUS_APPROVAL_FILE','PUBLIC_CORPUS_APPROVAL_SHA256','PUBLIC_CORPUS_SIGNER_PUBLIC_KEY']:monkeypatch.delenv(k,raising=False)
    client=TestClient(create_app())
    assert client.get('/api/health').status_code==200
    assert client.get('/api/ready').status_code==503
    assert client.get('/api/ready').json()['research_state']=='publication_pending'
    assert client.post('/api/chat',json={'message':'SYNTHETIC question'}).status_code==401
    paths=json.loads((Path(__file__).resolve().parents[2]/'docs/deployment-publication.json').read_bytes())['runtime_files']
    assert not any(p.endswith(('/intent.py','/hardened.py','/stage6e.py','/stage6e-evaluation.json')) for p in paths)


@pytest.mark.parametrize('question',[
 'Confirm the original BNS commencement notification commenced every provision without exceptions.',
 'Confirm the original BNSS commencement notification has no carve-outs.',
])
def test_exception_guard_retains_original_complete_paragraph(index,question):
    result=HardenedEvidenceRetriever(index).assess(question)
    assert result.status=='misleading_premise' and not result.selected
    assert result.ranked and any('except' in p.text for p in result.ranked)

@pytest.mark.parametrize('change',['human','duplicate','unknown','unlabelled'])
def test_new_evaluation_schema_cannot_forge_gold_or_approval(index,change):
    from backend.retrieval.stage6e import Evaluation
    p=index.passages[0];c=p.candidate
    spec=dict(schema_version=1,evaluation_version='stage6e-agent-v1',human_approved=False,label_method='SYNTHETIC human-unverified data, NOT LAW.',
        frozen_stage6_sha256='0'*64,frozen_stage6c_sha256='0'*64,frozen_stage6d_sha256='0'*64,
        catalog_sha256=index.catalog.digest,qa_sha256=index.catalog.qa_hash,index_version=index.version,
        references={'synthetic':dict(candidate_id=c.candidate_id,document_id=c.document_id,raw_sha256=c.raw_sha256,
            processed_sha256=c.processed_sha256,span=c.spans[0].model_dump(),rationale='SYNTHETIC source binding, no legal approval.')},
        cases=[dict(id='synthetic',question='Original BNS notification',expected_status='historical_evidence_available',required_references=['synthetic'],fault=None,label_status='agent_text_checked_human_review_required')])
    if change=='human':spec['human_approved']=True
    if change=='duplicate':spec['cases']*=2
    if change=='unknown':spec['cases'][0]['required_references']=['missing']
    if change=='unlabelled':spec['cases'][0]['required_references']=[]
    with pytest.raises(ValueError):Evaluation.model_validate(spec)
