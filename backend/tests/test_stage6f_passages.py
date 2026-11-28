"""Stage 6F offline regression tests use SYNTHETIC sources only, NOT LAW."""
from dataclasses import replace
from types import SimpleNamespace
import pytest
from backend.retrieval.passage_level import Lexicon,PassagePolicy,PassageEvidenceRetriever,temporal_class
from backend.retrieval.evidence import Group
from backend.tests.chat_fixtures import index,mvp_seed
from backend.tests.test_stage6c_evidence import mixed,mixed_seed

DATES=[dict(publication_date='2023-12-25'),dict(publication_date='2024-02-24')]

@pytest.mark.parametrize('word,expected',[
 ('cancelling','cancel'),('destroying','destroy'),('defacing','deface'),
 ('witnesses','witness'),('refreshing','refresh'),('objections','object'),
 ('refuses','refuse'),('corroborating','corroborate'),
])
def test_unique_source_attested_english_roots(word,expected):
    lex=Lexicon([SimpleNamespace(text='cancel destroy deface witness refresh object')])
    assert lex.canonical(word)==expected


def test_ambiguous_root_and_unknown_technical_words_are_not_guessed():
    lex=Lexicon([SimpleNamespace(text='writ write fact knowledge')])
    assert lex.canonical('writing')=='writing'
    assert 'quantum' in lex.terms('quantum algorithm standards',query=True)
    assert 'algorithm' in lex.terms('quantum algorithm standards',query=True)


@pytest.mark.parametrize('question',[
 'A circular is said to have displaced the BNS exception. Can the original notification alone establish its status?',
 'When the next accounting year starts, will original BNSS tell us which procedural rule is then operative?',
 'Does BSA apply in the next financial year?',
 'Has the BNS exception been annulled?',
 'Was the BNSS notification suspended?',
 'Have BSA rules been revised?',
])
def test_unverified_events_and_bounded_relative_dates(question):
    assert temporal_class(question,DATES)=='current_or_later'


def test_actual_historical_reading_is_preserved():
    assert temporal_class('Inspect original BNS text about destroying property.',DATES)=='historical_text'
    assert temporal_class('Find original BSA text, without claiming current validity.',DATES)=='historical_text'
    assert temporal_class('Find original BSA text, without claiming current validity but is it in force now?',DATES)=='current_or_later'


def test_same_instrument_with_comparison_has_two_requirements(mixed):
    policy=PassagePolicy(mixed)
    groups=policy.lexicon.groups('Compare original BSA witnesses refreshing memory with original BSA leading questions.')
    assert len(groups)==2 and {g.topic for g in groups}=={'bsa'}
    groups=policy.lexicon.groups('Compare original BSA memory with leading questions.')
    assert len(groups)==2


def test_partial_common_anchors_do_not_satisfy_distinguishing_concept(mixed):
    policy=PassagePolicy(mixed)
    original=next(p for p in mixed.passages if 'Sakshya' in p.title and p.printed_number)
    p=replace(original,text='SYNTHETIC fact knowledge intentional act; NOT LAW')
    group=Group('bsa','SYNTHETIC',frozenset({'fact','knowledge','special'}),False)
    assert not policy._matches(p,group)


def test_lexical_candidate_survives_hybrid_pool_cutoff(mixed,monkeypatch):
    gold=next(p for p in mixed.passages if 'Sakshya' in p.title and p.printed_number=='15')
    wrong=next(p for p in mixed.passages if 'Sakshya' in p.title and p.printed_number=='16')
    mixed.semantic=SimpleNamespace(version='SYNTHETIC-NO-MODEL')
    calls=[]
    def search(*a,mode=None,**k):
        calls.append(mode);return [wrong] if mode=='hybrid' else [gold]
    monkeypatch.setattr(mixed,'search',search)
    result=PassageEvidenceRetriever(mixed).assess('Original BSA communications during marriage',mode='hybrid')
    assert result.status=='historical_evidence_available'
    assert gold.identifier in {p.identifier for p in result.selected}
    assert 'bm25' in calls and 'hybrid' in calls

@pytest.mark.parametrize('q',[
 'What does the original BNS commencement notification state?',
 'Compare original BNSS evidence interpretation and BSA marital communications.',
 'Compare original BNS Judge acting judicially and acts following a Court order.',
])
def test_historical_and_complete_comparisons(mixed,q):
    result=PassageEvidenceRetriever(mixed).assess(q)
    assert result.status=='historical_evidence_available'
    assert result.required_groups==result.covered_groups
    assert len(result.ranked)<=5 and not result.human_approved and not result.publication_authorized

@pytest.mark.parametrize('q',[
 'Compare BNSS evidence interpretation with BSA facial recognition algorithm standards.',
 'Compare BNSS evidence interpretation with IPC abduction by force.',
])
def test_missing_evidence_is_not_filled_by_document_quota(mixed,q):
    result=PassageEvidenceRetriever(mixed).assess(q)
    assert result.status=='insufficient_evidence' and not result.selected

@pytest.mark.parametrize('kind',['quote','hash','identifier','qualifier'])
def test_union_candidates_cannot_bypass_source_validation(index,monkeypatch,kind):
    p=next(p for p in index.passages if p.instrument=='S.O. 848(E)')
    if kind=='quote':bad=replace(p,text='SYNTHETIC changed text NOT LAW')
    elif kind=='qualifier':bad=replace(p,text=p.text.split('except')[0])
    elif kind=='hash':bad=replace(p,candidate=p.candidate.model_copy(update={'raw_sha256':'0'*64}))
    else:bad=replace(p,candidate=p.candidate.model_copy(update={'document_id':'doc_'+'0'*64}))
    monkeypatch.setattr(index,'search',lambda *a,**k:[bad])
    assert PassageEvidenceRetriever(index).assess('Original BNSS notification').status=='source_integrity_failed'


def test_existing_exclusions_remain_mandatory(index,monkeypatch):
    import backend.retrieval.passage_level as p
    monkeypatch.setattr(p,'exclusion_reasons',lambda *a:['SYNTHETIC_EXCLUDED'])
    assert PassageEvidenceRetriever(index).assess('Original BNS notification').status=='source_integrity_failed'


def test_source_change_before_final_handoff_fails_closed(index,monkeypatch):
    original=PassagePolicy.assess;path=index.root/index.passages[0].candidate.raw_path
    def mutate(self,*a,**k):
        result=original(self,*a,**k);path.chmod(0o600);path.write_bytes(path.read_bytes()+b' SYNTHETIC CHANGE');return result
    monkeypatch.setattr(PassagePolicy,'assess',mutate)
    assert PassageEvidenceRetriever(index).assess('Original BNS notification').status=='source_integrity_failed'


def test_revocation_boundary_not_cached(index,monkeypatch):
    import backend.retrieval.optimized as opt
    state=[()];original=PassagePolicy.assess
    monkeypatch.setattr(opt,'checkpoint',lambda catalog:state[0])
    def change(self,*a,**k):
        result=original(self,*a,**k);state[0]=('SYNTHETIC_CHECKPOINT_CHANGE',);return result
    monkeypatch.setattr(PassagePolicy,'assess',change)
    assert PassageEvidenceRetriever(index).assess('Original BNS notification').status=='source_integrity_failed'


@pytest.mark.parametrize('change',['human','duplicate','unknown','unlabelled'])
def test_fresh_evaluation_rejects_forged_approval_or_invalid_gold(index,change):
    from backend.retrieval.stage6f import FreshEvaluation
    p=index.passages[0];c=p.candidate
    data=dict(schema_version=1,evaluation_version='stage6f-agent-v1',human_approved=False,label_method='SYNTHETIC source-first provisional labels, NOT LAW.',
        frozen_stage6_sha256='0'*64,frozen_stage6c_sha256='0'*64,frozen_stage6d_sha256='0'*64,frozen_stage6e_sha256='0'*64,
        catalog_sha256=index.catalog.digest,qa_sha256=index.catalog.qa_hash,index_version=index.version,
        references={'synthetic':dict(candidate_id=c.candidate_id,document_id=c.document_id,raw_sha256=c.raw_sha256,processed_sha256=c.processed_sha256,span=c.spans[0].model_dump(),rationale='SYNTHETIC software test data, not evidence approval.')},
        cases=[dict(id='synthetic',question='Original BNS notification',expected_status='historical_evidence_available',required_references=['synthetic'],fault=None,label_status='agent_text_checked_human_review_required')])
    if change=='human':data['human_approved']=True
    if change=='duplicate':data['cases']*=2
    if change=='unknown':data['cases'][0]['required_references']=['absent']
    if change=='unlabelled':data['cases'][0]['required_references']=[]
    with pytest.raises(ValueError):FreshEvaluation.model_validate(data)


def test_pool_bound_is_enforced(index,monkeypatch):
    monkeypatch.setattr(PassagePolicy,'MAX_POOL',0)
    assert PassageEvidenceRetriever(index).assess('Original BNS notification').status=='source_integrity_failed'


def test_fresh_public_runtime_never_imports_offline_stage6(monkeypatch,tmp_path):
    import os,subprocess,sys
    root=__import__('pathlib').Path(__file__).resolve().parents[2]
    env=dict(os.environ,KANOON_ENV='production',CORPUS_KIND='public',RETRIEVAL_MODE='bm25',PUBLIC_CORPUS_DIR=str(tmp_path/'ABSENT'),KANOON_ACCESS_TOKEN='SYNTHETIC_ACCESS_TOKEN_NOT_REAL_STAGE6F',AI_ASSISTANT_ENABLED='false')
    for key in ['PUBLIC_CORPUS_MANIFEST_SHA256','PUBLIC_CORPUS_APPROVAL_FILE','PUBLIC_CORPUS_APPROVAL_SHA256','PUBLIC_CORPUS_SIGNER_PUBLIC_KEY']:env.pop(key,None)
    script="""
import importlib.abc,sys
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in {'backend.retrieval.evidence','backend.retrieval.offline','backend.retrieval.intent','backend.retrieval.hardened','backend.retrieval.optimized','backend.retrieval.passage_level'} or fullname.startswith('backend.retrieval.stage6'):
   raise AssertionError('Offline module entered public runtime: '+fullname)
sys.meta_path.insert(0,Guard())
from fastapi.testclient import TestClient
from backend.chat.api import create_app
from backend import retrieval
import backend.retrieval.engine as engine
engine.ArchivalIndex=lambda *a,**k:(_ for _ in ()).throw(AssertionError('Private index accessed'))
c=TestClient(create_app())
assert c.get('/api/health').status_code==200
r=c.get('/api/ready');assert r.status_code==503 and r.json()['research_state']=='publication_pending'
assert c.post('/api/chat',json={'message':'SYNTHETIC'}).status_code==401
print('PUBLIC_ISOLATION_PASS')
"""
    run=subprocess.run([sys.executable,'-B','-c',script],cwd=root,env=env,capture_output=True,text=True,timeout=45)
    assert run.returncode==0,run.stderr
    assert 'PUBLIC_ISOLATION_PASS' in run.stdout
