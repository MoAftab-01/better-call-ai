"""Privacy-safe operational regressions. All model transports and usage are synthetic."""
import asyncio
from collections import Counter
import json
import logging
import re
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.responses import StreamingResponse

from backend.chat.api import create_app
from backend.chat.demo import DemoService
from backend.chat.general import GeneralService
from backend.chat.provider import GroqProvider, Settings
from backend.chat.telemetry import Telemetry, LOGGER, MAX_COUNTER, TRACE, SPAN, increment, observed_provider, emit, LOG_FIELDS

KEY='SYNTHETIC_PROVIDER_KEY_NOT_REAL_STAGE5'
OPS='SYNTHETIC_OPERATIONS_TOKEN_NOT_REAL_2026'
RESEARCH='SYNTHETIC_RESEARCH_TOKEN_NOT_REAL_2026'
MISSING=object()


def completion(usage=MISSING,answer='SYNTHETIC_PRIVATE_PROVIDER_RESPONSE'):
    body={'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'answer':answer,'requires_professional_help':False})}}]}
    if usage is not MISSING:body['usage']=usage
    return httpx.Response(200,content=json.dumps(body).encode(),headers={'Content-Type':'application/json'})


@pytest.fixture
def config(monkeypatch,tmp_path):
    for key,value in dict(KANOON_ENV='production',KANOON_ALLOWED_ORIGINS='https://app.example',
            KANOON_ACCESS_TOKEN=RESEARCH,GROQ_API_KEY=KEY,GROQ_MODEL='synthetic-model',
            AI_ASSISTANT_ENABLED='true',AI_ASSISTANT_RPM='6',AI_ASSISTANT_DAILY_LIMIT='100',
            DEMO_ENABLED='true',DEMO_PROVIDER='deterministic',CORPUS_KIND='public',RETRIEVAL_MODE='bm25',
            PUBLIC_CORPUS_DIR=str(tmp_path/'ABSENT')).items():monkeypatch.setenv(key,value)
    for key in ('KANOON_OPS_TOKEN','PUBLIC_CORPUS_MANIFEST_SHA256','PUBLIC_CORPUS_APPROVAL_FILE','PUBLIC_CORPUS_APPROVAL_SHA256','PUBLIC_CORPUS_SIGNER_PUBLIC_KEY'):
        monkeypatch.delenv(key,raising=False)


@pytest.fixture
def records():
    items=[]
    class Capture(logging.Handler):
        def emit(self,record):items.append(json.loads(record.getMessage()))
    handler=Capture();LOGGER.addHandler(handler)
    yield items
    LOGGER.removeHandler(handler)


@pytest.fixture
def observed(config,records):
    g=GeneralService(Settings(KEY,'synthetic-model'),httpx.MockTransport(lambda r:completion({'prompt_tokens':32,'completion_tokens':8,'total_tokens':40,'secret':'SYNTHETIC_USAGE_SECRET'})))
    app=create_app(general_service=g)
    return SimpleNamespace(app=app,client=TestClient(app),general=g,metrics=app.state.telemetry,records=records)


def count(snapshot,field,**labels):
    return sum(row['count'] for row in snapshot[field] if all(row.get(k)==v for k,v in labels.items()))


def ask(c,message='Explain mediation',**kwargs):return c.post('/api/assistant/chat',json={'message':message},**kwargs)


def test_correlation_and_strict_log_privacy(observed):
    r=observed.client.post('/api/assistant/chat?private=SYNTHETIC_QUERY_SECRET',
        headers={'Authorization':'Bearer SYNTHETIC_AUTH_SECRET','X-Request-ID':'f'*32},
        json={'message':'SYNTHETIC_PRIVATE_PROMPT','history':[{'role':'user','content':'SYNTHETIC_PRIVATE_HISTORY'},{'role':'assistant','content':'SYNTHETIC_HISTORY_REPLY'}]})
    assert r.status_code==200
    identifier=r.headers['x-request-id']
    assert re.fullmatch('[a-f0-9]{32}',identifier) and identifier!='f'*32
    assert observed.records and all(x['request_id']==identifier for x in observed.records)
    for x in observed.records:
        assert set(x)=={'schema_version','event','timestamp','request_id','route','method'}|LOG_FIELDS[x['event']]
    serialized=json.dumps(observed.records)+json.dumps(observed.metrics.snapshot())
    for secret in (KEY,OPS,RESEARCH,'SYNTHETIC_AUTH_SECRET','SYNTHETIC_PRIVATE_PROMPT','SYNTHETIC_PRIVATE_HISTORY',
            'SYNTHETIC_HISTORY_REPLY','SYNTHETIC_QUERY_SECRET','SYNTHETIC_PRIVATE_PROVIDER_RESPONSE','SYNTHETIC_USAGE_SECRET','f'*32):
        assert secret not in serialized
    assert r.headers['cache-control']=='no-store'
    assert count(observed.metrics.snapshot(),'provider_operations',outcome='success')==1
    assert TRACE.get() is None and SPAN.get() is None


@pytest.mark.parametrize('case,expected',[('invalid',422),('origin',403),('research_auth',401),('disabled',404),('size',413)])
def test_early_responses_are_traced_without_provider_calls(observed,monkeypatch,case,expected):
    c=observed.client
    if case=='invalid':r=ask(c,' ')
    elif case=='origin':r=ask(c,headers={'Origin':'https://evil.example'})
    elif case=='research_auth':r=c.post('/api/chat',json={'message':'SYNTHETIC_SECRET'})
    elif case=='size':r=c.post('/api/assistant/chat',content=b'x'*16001)
    else:
        monkeypatch.setenv('AI_ASSISTANT_ENABLED','false')
        c=TestClient(create_app(general_service=observed.general));r=ask(c)
    assert r.status_code==expected and re.fullmatch('[a-f0-9]{32}',r.headers['x-request-id'])
    assert observed.records[-1]['status']==expected
    assert observed.records[-1]['event']=='request_completed'
    assert not any(x['event']=='provider_completed' for x in observed.records)


def test_latency_measurement_uses_injected_monotonic_clock(config,records):
    class Clock:
        value=10.0
        def __call__(self):return self.value
    clock=Clock();metrics=Telemetry(clock=clock);app=create_app(telemetry=metrics)
    @app.get('/test-latency')
    def route():clock.value+=.125;return {'ok':True}
    assert TestClient(app).get('/test-latency').status_code==200
    row=metrics.snapshot()['request_duration'][0]
    assert row==dict(route='unmatched',method='GET',count=1,sum_ms=125.0,max_ms=125.0)
    assert records[-1]['duration_ms']==125.0


@pytest.mark.parametrize('usage,state,fields',[
    (MISSING,'missing',{}),(None,'missing',{}),({},'missing',{}),
    ({'prompt_tokens':4,'completion_tokens':6,'total_tokens':10},'complete',{'prompt_tokens':4,'completion_tokens':6,'total_tokens':10}),
    ({'prompt_tokens':0},'partial',{'prompt_tokens':0}),
    ({'completion_tokens':6},'partial',{'completion_tokens':6}),
    (['SYNTHETIC_SECRET'],'malformed',{}),('SYNTHETIC_SECRET','malformed',{}),(True,'malformed',{}),
    ({'prompt_tokens':True},'malformed',{}),({'total_tokens':-1},'malformed',{}),
    ({'prompt_tokens':1.5},'malformed',{}),({'prompt_tokens':float('nan')},'malformed',{}),
    ({'prompt_tokens':10**80},'malformed',{}),
    ({'prompt_tokens':4,'completion_tokens':6,'total_tokens':999},'malformed',{}),
    ({'prompt_tokens':4,'completion_tokens':'bad'},'malformed',{'prompt_tokens':4}),
])
def test_optional_usage_never_breaks_answers_or_invents_tokens(observed,usage,state,fields):
    observed.general.transport=httpx.MockTransport(lambda r:completion(usage))
    assert ask(observed.client).status_code==200
    snapshot=observed.metrics.snapshot()
    assert count(snapshot,'usage_observations',state=state)==1
    assert {r['field']:r['total'] for r in snapshot['reported_tokens']}==fields
    assert all(r['observations']==1 for r in snapshot['reported_tokens'])
    assert 'SYNTHETIC_SECRET' not in json.dumps(snapshot)+json.dumps(observed.records)


@pytest.mark.parametrize('status,expected,category',[(400,503,'configuration_error'),(401,503,'configuration_error'),
    (403,503,'configuration_error'),(404,503,'configuration_error'),(429,429,'rate_limited'),(500,503,'unavailable'),(302,503,'unavailable')])
def test_http_provider_failures_are_classified_without_raw_body(observed,status,expected,category):
    observed.general.transport=httpx.MockTransport(lambda r:httpx.Response(status,text='SYNTHETIC_RAW_SECRET',headers={'Location':'https://evil.example'}))
    r=ask(observed.client);assert r.status_code==expected
    snapshot=observed.metrics.snapshot()
    assert count(snapshot,'provider_operations',outcome=category)==1
    assert count(snapshot,'provider_http',status='attempt')==1
    assert not snapshot['reported_tokens']
    assert 'SYNTHETIC_RAW_SECRET' not in json.dumps(observed.records)+r.text


@pytest.mark.parametrize('exception,category,expected',[(httpx.ReadTimeout('SYNTHETIC_TIMEOUT_SECRET'),'timeout',504),
    (httpx.ConnectError('SYNTHETIC_CONNECT_SECRET'),'unavailable',503)])
def test_transport_errors_are_private_and_counted(observed,exception,category,expected):
    def fail(r):raise exception
    observed.general.transport=httpx.MockTransport(fail)
    assert ask(observed.client).status_code==expected
    assert count(observed.metrics.snapshot(),'provider_operations',outcome=category)==1
    assert str(exception) not in json.dumps(observed.records)


def test_output_rejected_after_usage_is_still_accounted(observed):
    observed.general.transport=httpx.MockTransport(lambda r:completion({'prompt_tokens':4,'completion_tokens':6,'total_tokens':10},'See Section 106.'))
    assert ask(observed.client).status_code==502
    snap=observed.metrics.snapshot()
    assert count(snap,'provider_operations',outcome='invalid_response')==1
    assert next(r for r in snap['reported_tokens'] if r['field']=='total_tokens')['total']==10


def test_malformed_json_usage_remains_unknown(observed):
    observed.general.transport=httpx.MockTransport(lambda r:httpx.Response(200,text='SYNTHETIC_NOT_JSON'))
    assert ask(observed.client).status_code==502
    snap=observed.metrics.snapshot()
    assert count(snap,'provider_operations',outcome='invalid_response')==1
    assert count(snap,'provider_http',status='200')==1 and snap['usage_observations']==[] and snap['reported_tokens']==[]


def test_safety_boundary_is_not_counted_as_successful_provider_call(observed):
    assert ask(observed.client,'I was arrested; what should I plead?').status_code==200
    snap=observed.metrics.snapshot()
    assert count(snap,'provider_operations',outcome='not_called')==1
    assert snap['provider_http']==[] and snap['reported_tokens']==[]


def test_missing_provider_is_configuration_failure_not_fake_inference(observed):
    observed.general.settings=Settings()
    assert ask(observed.client).status_code==503
    snap=observed.metrics.snapshot()
    assert count(snap,'provider_operations',outcome='configuration_error')==1
    assert snap['provider_http']==[] and snap['reported_tokens']==[]


def test_metrics_requires_separate_production_secret_even_on_loopback(observed,monkeypatch):
    monkeypatch.setenv('KANOON_OPS_TOKEN',OPS)
    app=create_app(general_service=observed.general);c=TestClient(app,client=('127.0.0.1',1234))
    assert c.get('/api/ops/metrics').status_code==401
    for token in (KEY,RESEARCH,'wrong'):
        assert c.get('/api/ops/metrics',headers={'Authorization':'Bearer '+token}).status_code==401
    r=c.get('/api/ops/metrics',headers={'Authorization':'Bearer '+OPS})
    assert r.status_code==200 and r.headers['cache-control']=='no-store'
    assert r.json()['durable'] is False
    assert OPS not in json.dumps(r.json())+json.dumps(observed.records)
    assert '/api/ops/metrics' not in c.get('/openapi.json').json()['paths']


@pytest.mark.parametrize('token',[None,'short',KEY,RESEARCH,'x'*257,'x '*32])
def test_absent_or_invalid_ops_secret_fails_closed_without_breaking_chat(observed,monkeypatch,token):
    if token is not None:monkeypatch.setenv('KANOON_OPS_TOKEN',token)
    c=TestClient(create_app(general_service=observed.general))
    assert c.get('/api/ops/metrics').status_code==404
    assert c.get('/api/health').status_code==200 and ask(c).status_code==200


@pytest.mark.parametrize('host,headers,expected',[('127.0.0.1',{},200),('::1',{},200),('testclient',{},404),
    ('192.0.2.2',{'X-Forwarded-For':'127.0.0.1'},404),('127.0.0.1',{'X-Forwarded-For':'127.0.0.1'},404),
    ('127.0.0.1',{'Forwarded':'for=127.0.0.1'},404),('127.0.0.1',{'X-Real-IP':'127.0.0.1'},404),
    ('127.0.0.1',{'Origin':'https://app.example'},404)])
def test_local_metrics_bypass_never_trusts_forwarded_headers(observed,monkeypatch,host,headers,expected):
    monkeypatch.setenv('KANOON_ENV','local')
    c=TestClient(create_app(general_service=observed.general),client=(host,1234))
    assert c.get('/api/ops/metrics',headers=headers).status_code==expected


def test_public_status_contracts_do_not_publish_operational_data(observed):
    c=observed.client
    assert c.get('/api/health').json()=={'status':'healthy','service':'better-call-kanoon'}
    assert c.get('/api/ready').status_code==503
    for path in ('/api/health','/api/ready','/api/chat/status','/api/demo/status','/api/assistant/status','/api/references'):
        d=c.get(path).json()
        assert not {'requests','request_duration','reported_tokens','provider_operations','active_requests'} & d.keys()
    assert observed.metrics.snapshot()['provider_operations']==[]


def test_unknown_paths_and_methods_have_bounded_metric_cardinality(observed):
    for i in range(30):assert observed.client.request('UNKNOWN'+str(i),'/SYNTHETIC_SECRET_PATH_'+str(i)+'?token=SYNTHETIC_SECRET').status_code==404
    snap=observed.metrics.snapshot()
    assert len(snap['requests'])==1 and snap['requests'][0]['route']=='unmatched' and snap['requests'][0]['method']=='OTHER'
    assert len(snap['request_duration'])==1
    assert 'SYNTHETIC_SECRET' not in json.dumps(snap)+json.dumps(observed.records)
    c=Counter(k=MAX_COUNTER);increment(c,'k',10**80);assert c['k']==MAX_COUNTER


def test_correlated_concurrent_requests_and_slot_release(observed):
    started=asyncio.Event();release=asyncio.Event();arrivals=0
    async def slow(r):
        nonlocal arrivals
        arrivals+=1
        if arrivals==2:started.set()
        await release.wait();return completion()
    observed.general.transport=httpx.MockTransport(slow)
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=observed.app),base_url='https://test') as c:
            tasks=[asyncio.create_task(ask_async(c)) for _ in range(2)]
            await asyncio.wait_for(started.wait(),2)
            snap=observed.metrics.snapshot();assert snap['active_requests']==2 and snap['active_provider_operations']==2
            busy=await ask_async(c);assert busy.status_code==429
            release.set();responses=await asyncio.gather(*tasks)
            ids={r.headers['x-request-id'] for r in responses+[busy]};assert len(ids)==3
            assert all(r.status_code==200 for r in responses)
            assert {r['request_id'] for r in observed.records}==ids
            assert {r['request_id'] for r in observed.records if r['event']=='provider_completed'}=={r.headers['x-request-id'] for r in responses}
    asyncio.run(check())
    assert observed.metrics.snapshot()['active_requests']==0 and observed.metrics.snapshot()['active_provider_operations']==0
    assert count(observed.metrics.snapshot(),'provider_operations',outcome='success')==2
    assert all(r['request_id'] for r in observed.records)


async def ask_async(c):return await c.post('/api/assistant/chat',json={'message':'SYNTHETIC concurrent concept'})


def test_overall_deadline_and_body_timeout_are_distinct(observed,monkeypatch):
    import backend.chat.api as api
    original=asyncio.timeout
    monkeypatch.setattr(api.asyncio,'timeout',lambda n:original(.02 if n in {10,22} else n))
    async def stuck(r):await asyncio.sleep(1);return completion()
    observed.general.transport=httpx.MockTransport(stuck)
    assert ask(observed.client).status_code==504
    assert count(observed.metrics.snapshot(),'provider_operations',outcome='timeout')==1
    async def slow_body():await asyncio.sleep(1);yield b'{}'
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=observed.app),base_url='https://test') as c:
            r=await c.post('/api/assistant/chat',content=slow_body());assert r.status_code==408
    asyncio.run(check())
    assert observed.metrics.snapshot()['active_requests']==0 and observed.metrics.snapshot()['active_provider_operations']==0
    assert any(r.get('error_code')=='request_body_timeout' for r in observed.records)


def test_daily_retry_after_and_restart_scope_preserve_limits(observed,monkeypatch):
    monkeypatch.setenv('AI_ASSISTANT_DAILY_LIMIT','1')
    first=TestClient(create_app(general_service=observed.general))
    assert ask(first).status_code==200
    limited=ask(first);assert limited.status_code==429 and 86390<=int(limited.headers['retry-after'])<=86400
    assert first.app.state.telemetry.snapshot()['provider_operations']
    second=TestClient(create_app(general_service=observed.general))
    assert second.app.state.telemetry.snapshot()['requests']==[]
    assert ask(second).status_code==200  # App restart also resets the in-memory request budget.


def test_minute_rate_limit_rejections_are_traced_without_more_provider_cost(observed):
    for _ in range(6):assert ask(observed.client).status_code==200
    r=ask(observed.client);assert r.status_code==429 and r.headers['retry-after']=='60'
    assert count(observed.metrics.snapshot(),'provider_http',status='attempt')==6
    assert any(x.get('error_code')=='assistant_rate_limited' for x in observed.records)


def test_demo_selection_retry_usage_and_fallback_are_observed(config,records,monkeypatch):
    monkeypatch.setenv('DEMO_PROVIDER','groq');calls=0
    def handler(r):
        nonlocal calls
        calls+=1
        if calls==1:return httpx.Response(503,text='SYNTHETIC_UPSTREAM_SECRET')
        return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':'{"source_ids":[]}'}}],
            'usage':{'prompt_tokens':7,'completion_tokens':3,'total_tokens':10}})
    provider=GroqProvider(Settings(KEY,'synthetic-model'),httpx.MockTransport(handler))
    c=TestClient(create_app(demo_service=DemoService(True,provider)))
    assert c.post('/api/demo/chat',json={'message':'rent'}).status_code==200
    snap=c.app.state.telemetry.snapshot()
    assert count(snap,'provider_operations',provider='demo_selection',outcome='success')==1
    assert count(snap,'provider_http',status='attempt')==2 and count(snap,'provider_http',status='5xx')==1
    assert next(x for x in snap['reported_tokens'] if x['field']=='total_tokens')['total']==10
    assert 'SYNTHETIC_UPSTREAM_SECRET' not in json.dumps(records)


def test_demo_budget_timeout_is_not_misreported_as_successful_inference(config,records,monkeypatch):
    monkeypatch.setenv('DEMO_PROVIDER','groq');original=asyncio.timeout
    monkeypatch.setattr(asyncio,'timeout',lambda n:original(.02 if n==8 else n))
    async def handler(r):await asyncio.sleep(1);return httpx.Response(200)
    p=GroqProvider(Settings(KEY,'synthetic-model'),httpx.MockTransport(handler))
    c=TestClient(create_app(demo_service=DemoService(True,p)))
    r=c.post('/api/demo/chat',json={'message':'rent'})
    assert r.status_code==200 and r.json()['provider_status']=='fallback'
    assert count(c.app.state.telemetry.snapshot(),'provider_operations',outcome='timeout')==1


def test_unhandled_errors_are_generic_and_never_log_exception_text(observed):
    @observed.app.get('/test-exception')
    def broken():raise RuntimeError('SYNTHETIC_EXCEPTION_SECRET')
    r=observed.client.get('/test-exception');assert r.status_code==500
    assert 'SYNTHETIC_EXCEPTION_SECRET' not in r.text+json.dumps(observed.records)
    assert observed.records[-1]['completion']=='internal_error'


def test_safe_log_schema_drops_unknown_fields_and_snapshot_is_a_copy(observed):
    ask(observed.client)
    one=observed.metrics.snapshot();one['request_duration'][0]['count']=999
    assert observed.metrics.snapshot()['request_duration'][0]['count']==1
    assert not any({'request_id','prompt','history','Authorization'} & r.keys() for r in one['requests'])
    assert TRACE.get() is None and SPAN.get() is None


def test_unknown_log_fields_are_dropped(observed):
    @observed.app.get('/test-log-schema')
    def route():
        emit('request_completed',TRACE.get(),status=200,duration_ms=0,completion='response',error_code=None,
            prompt='SYNTHETIC_DONT_LOG',authorization='SYNTHETIC_DONT_LOG')
        emit('SYNTHETIC_UNAPPROVED_EVENT',TRACE.get(),raw_response='SYNTHETIC_DONT_LOG')
        return {'ok':True}
    assert observed.client.get('/test-log-schema').status_code==200
    assert 'SYNTHETIC_DONT_LOG' not in json.dumps(observed.records)
    assert not any(r['event']=='SYNTHETIC_UNAPPROVED_EVENT' for r in observed.records)


def test_body_limit_checks_before_appending_large_chunk(observed,monkeypatch):
    import backend.chat.api as api
    class GuardedBuffer(bytearray):
        def extend(self,chunk):
            assert len(self)+len(chunk)<=16000,'Oversized chunk was copied before rejection'
            return super().extend(chunk)
    monkeypatch.setattr(api,'bytearray',GuardedBuffer,raising=False)
    assert observed.client.post('/api/assistant/chat',content=b'x'*32000).status_code==413
    assert count(observed.metrics.snapshot(),'request_errors',error_code='request_too_large')==1


def test_provider_event_queue_and_counters_have_explicit_bounds(observed):
    @observed_provider('general')
    async def synthetic_operation():return []
    @observed.app.get('/test-many-events')
    async def route():
        for _ in range(20):await synthetic_operation()
        return {'ok':True}
    assert observed.client.get('/test-many-events').status_code==200
    snap=observed.metrics.snapshot()
    assert snap['provider_events_dropped']==12
    assert count(snap,'provider_operations',outcome='success')==8
    assert snap['active_provider_operations']==0


def test_broken_log_sink_does_not_change_the_answer(observed):
    class Broken(logging.Handler):
        def emit(self,record):raise OSError('SYNTHETIC_LOG_SINK_SECRET')
    handler=Broken();LOGGER.addHandler(handler)
    try:assert ask(observed.client).status_code==200
    finally:LOGGER.removeHandler(handler)
    assert 'SYNTHETIC_LOG_SINK_SECRET' not in json.dumps(observed.records)


def test_post_header_failure_is_reported_without_raw_exception(observed):
    @observed.app.get('/test-broken-stream')
    def route():
        async def broken():
            yield b'SYNTHETIC prefix'
            raise RuntimeError('SYNTHETIC_STREAM_EXCEPTION_SECRET')
        return StreamingResponse(broken())
    with pytest.raises(RuntimeError,match='Request failed after response headers') as exc:
        observed.client.get('/test-broken-stream')
    assert 'SYNTHETIC_STREAM_EXCEPTION_SECRET' not in str(exc.value)+json.dumps(observed.records)
    assert count(observed.metrics.snapshot(),'request_outcomes',completion='aborted')==1


def test_log_schema_rejects_sensitive_values_in_known_field_names(observed):
    @observed.app.get('/test-bad-log-fields')
    def route():
        emit('request_completed',TRACE.get(),status='SYNTHETIC_SCHEMA_SECRET',duration_ms='SYNTHETIC_SCHEMA_SECRET',
            completion='SYNTHETIC_SCHEMA_SECRET',error_code='SYNTHETIC_SCHEMA_SECRET')
        emit('provider_completed',TRACE.get(),provider='SYNTHETIC_SCHEMA_SECRET',outcome='SYNTHETIC_SCHEMA_SECRET',
            duration_ms=float('nan'),http_attempts='SYNTHETIC_SCHEMA_SECRET',last_http_status='SYNTHETIC_SCHEMA_SECRET')
        emit('provider_usage',TRACE.get(),provider='SYNTHETIC_SCHEMA_SECRET',usage_state='SYNTHETIC_SCHEMA_SECRET',
            reported_tokens={'prompt_tokens':'SYNTHETIC_SCHEMA_SECRET','unexpected':'SYNTHETIC_SCHEMA_SECRET'})
        emit('request_completed',TRACE.get(),status={},duration_ms=[],completion=[],error_code={'SYNTHETIC_SCHEMA_SECRET':True})
        return {'ok':True}
    assert observed.client.get('/test-bad-log-fields').status_code==200
    assert 'SYNTHETIC_SCHEMA_SECRET' not in json.dumps(observed.records)
