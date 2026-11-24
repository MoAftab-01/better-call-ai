"""Evaluator behavior tests use synthetic outputs, never spend model credits."""
import json
import httpx
import pytest
from backend.evaluation.__main__ import evaluate, has_uncertainty


@pytest.mark.parametrize('text',["I don't have current information.","I don’t have the ability to verify recent changes.","I’m unable to verify that.","I cannot confirm this."])
def test_uncertainty_recognizes_ascii_and_typographic_contractions(text):
    assert has_uncertainty(text)


@pytest.mark.parametrize('text',["The law definitely changed yesterday.","This is unquestionably current."])
def test_uncertainty_does_not_pass_confident_unsupported_prose(text):
    assert not has_uncertainty(text)


def client_for(handler,ready=503,available=True):
    def transport(r):
        if r.url.path=='/api/ready':return httpx.Response(ready,json={'research_state':'publication_pending'})
        if r.url.path=='/api/assistant/status':return httpx.Response(200,json={'available':available})
        return handler(r)
    return httpx.Client(base_url='http://127.0.0.1:8000',transport=httpx.MockTransport(transport))


def test_evaluation_preserves_actual_followup_and_labels_without_claiming_truth():
    requests=[]
    def handler(r):
        d=json.loads(r.content);requests.append(d)
        text='mediation dispute' if len(requests)==1 else 'mediation arbitration'
        return httpx.Response(200,json={'answer':'AI-generated general information — not source-verified legal advice.\n\n'+text,'sources_verified':False,'citations':[],'legal_currentness':'unknown','mode':'general_information','response_kind':'generated'})
    cases=[dict(id='first',category='concept',message='Explain mediation',topic_terms=['mediat']),dict(id='next',category='followup',history_from='first',message='Compared to arbitration?',topic_terms=['arbitrat'])]
    with client_for(handler) as c:report=evaluate(c,cases)
    assert report['totals']['passed']==2
    assert requests[1]['history'][0]['content']=='Explain mediation'
    assert 'mediation dispute' in requests[1]['history'][1]['content']
    assert report['legal_accuracy_verified'] is False and not report['public_retrieval_evaluated']


@pytest.mark.parametrize('ready,available',[(200,True),(503,False)])
def test_evaluation_requires_blocked_research_and_configured_assistant(ready,available):
    with client_for(lambda r:pytest.fail('must not submit'),ready,available) as c:
        with pytest.raises(ValueError):evaluate(c,[])


def test_safe_rejection_not_counted_as_generated_answer_and_rate_limit_is_failure():
    cases=[dict(id='citation',category='negative',message='Exact citation',allow_safe_rejection=True),dict(id='next',category='concept',message='concept')]
    def handler(r):
        first=json.loads(r.content)['message']=='Exact citation'
        return httpx.Response(502 if first else 429,json={'error':{'code':'provider_invalid_response' if first else 'assistant_rate_limited'}})
    with client_for(handler) as c:report=evaluate(c,cases)
    assert report['totals']==dict(cases=2,passed=1,generated=0,safe_rejections=1)
    assert not report['cases'][1]['passed']


def test_failed_first_question_cannot_fabricate_followup_context():
    cases=[dict(id='first',category='concept',message='concept'),dict(id='next',category='followup',history_from='first',message='followup')]
    with client_for(lambda r:httpx.Response(503,json={'error':{'code':'provider_unavailable'}})) as c:report=evaluate(c,cases)
    assert report['totals']['passed']==0 and report['cases'][1]['error']=='Required earlier response unavailable'
