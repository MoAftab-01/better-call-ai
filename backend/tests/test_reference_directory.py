"""Navigation checks are not evidence or publication approvals."""
from urllib.parse import urlsplit
from datetime import datetime
from fastapi.testclient import TestClient
from backend.chat.api import create_app
from backend.chat.references import reference_directory


def test_reference_directory_is_bounded_navigation_metadata():
    d=reference_directory()
    assert not d['used_in_ai_answers'] and not d['sources_verified_for_answers']
    assert len(d['references'])==3
    assert {urlsplit(r['url']).hostname for r in d['references']}=={'indiacode.gov.in','www.sci.gov.in','nalsa.gov.in'}
    for r in d['references']:
        assert r['http_status']==200 and r['url']==r['final_url']
        assert urlsplit(r['url']).scheme=='https' and not urlsplit(r['url']).username
        assert datetime.fromisoformat(r['checked_at']).tzinfo is not None
        assert not {'quote','passage','citation','source_hash','approval'} & r.keys()


def test_reference_endpoint_never_constructs_research_or_makes_network_calls(monkeypatch):
    import backend.chat.api as api
    import httpx
    def forbidden(*a,**k):raise AssertionError('Unexpected research/network access')
    monkeypatch.setattr(api,'ChatService',forbidden)
    monkeypatch.setattr(httpx.AsyncClient,'send',forbidden)
    c=TestClient(create_app())
    r=c.get('/api/references')
    assert r.status_code==200 and r.json()==reference_directory()
    assert c.app.state.chat is None and r.headers['cache-control']=='no-store'


def test_returned_directory_does_not_mutate_checked_records():
    d=reference_directory();d['references'][0]['url']='https://evil.example/'
    assert reference_directory()['references'][0]['url']=='https://indiacode.gov.in/'
