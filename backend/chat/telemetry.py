"""Bounded, allowlisted operational metadata. No prompts, credentials or response storage."""
import asyncio
from collections import Counter
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
import json
import logging
import math
import re
import sys
import threading
import time
from uuid import uuid4

from starlette.responses import JSONResponse

MAX_COUNTER = 2**63 - 1
MAX_TOKENS_PER_FIELD = 1_000_000_000
ROUTES = frozenset({'/', '/api/health', '/api/ready', '/api/chat/status', '/api/chat',
    '/api/demo/status', '/api/demo/chat', '/api/assistant/status', '/api/assistant/chat',
    '/api/references', '/api/ops/metrics', '/docs', '/docs/oauth2-redirect', '/openapi.json'})
METHODS = frozenset({'GET','POST','OPTIONS','HEAD','PUT','PATCH','DELETE'})
KINDS = frozenset({'general','demo_selection','research_selection'})
OUTCOMES = frozenset({'success','not_called','configuration_error','timeout','rate_limited',
    'unavailable','invalid_response','cancelled','internal_error'})
REASONS = frozenset({'assistant_disabled','assistant_rate_limited','assistant_origin_denied',
    'provider_not_configured','demo_disabled','demo_origin_denied','demo_rate_limited','demo_timeout',
    'demo_unavailable','corpus_not_approved','access_required','deployment_not_configured',
    'service_busy','local_rate_limited','request_too_large','request_body_timeout','provider_timeout',
    'provider_rate_limited','provider_configuration_error','provider_unavailable','provider_invalid_response',
    'source_changed','invalid_request','research_not_ready','ops_unavailable','ops_access_required','internal_error'})
TOKEN_FIELDS = ('prompt_tokens','completion_tokens','total_tokens')
LOG_FIELDS = {
    'request_completed':frozenset({'status','duration_ms','completion','error_code'}),
    'provider_completed':frozenset({'provider','outcome','duration_ms','http_attempts','last_http_status'}),
    'provider_usage':frozenset({'provider','usage_state','reported_tokens'}),
}
TRACE = ContextVar('bcai_operational_trace', default=None)
SPAN = ContextVar('bcai_provider_span', default=None)
LOGGER = logging.getLogger('better_call_ai.operations')
_HANDLER_LOCK = threading.Lock()


def configure_logging():
    with _HANDLER_LOCK:
        if not any(getattr(h,'bcai_operations',False) for h in LOGGER.handlers):
            h=logging.StreamHandler(sys.__stderr__)
            h.bcai_operations=True
            h.setFormatter(logging.Formatter('%(message)s'))
            LOGGER.addHandler(h)
        LOGGER.setLevel(logging.INFO)
        LOGGER.propagate=False


def safe_enum(value, choices, fallback):
    return value if type(value) is str and value in choices else fallback


def emit(event, trace, **fields):
    # Callers supply only fixed schemas/enumerations/numbers, never arbitrary dicts.
    if type(event) is not str or event not in LOG_FIELDS or trace is None:return
    fields={k:v for k,v in fields.items() if k in LOG_FIELDS[event]}
    elapsed=fields.get('duration_ms',0)
    fields['duration_ms']=(round(max(0,min(elapsed,86_400_000)),3) if type(elapsed) is float and math.isfinite(elapsed)
        else max(0,min(elapsed,86_400_000)) if type(elapsed) is int else 0)
    if event=='request_completed':
        status=fields.get('status')
        fields['status']=status if type(status) is int and 100<=status<=599 else 0
        fields['completion']=safe_enum(fields.get('completion'), {'response','cancelled','internal_error','aborted'}, 'internal_error')
        code=fields.get('error_code');fields['error_code']=None if code is None else safe_enum(code, REASONS, 'internal_error')
    else:
        fields['provider']=safe_enum(fields.get('provider'), KINDS, 'unknown')
        if event=='provider_completed':
            fields['outcome']=safe_enum(fields.get('outcome'), OUTCOMES, 'internal_error')
            status=fields.get('last_http_status');attempts=fields.get('http_attempts')
            fields['last_http_status']=status if type(status) is int and 100<=status<=599 else 0
            fields['http_attempts']=max(0,min(attempts,16)) if type(attempts) is int else 0
        else:
            fields.pop('duration_ms',None)
            fields['usage_state']=safe_enum(fields.get('usage_state'), {'complete','partial','missing','malformed'}, 'malformed')
            tokens=fields.get('reported_tokens')
            fields['reported_tokens']={k:v for k,v in tokens.items() if k in TOKEN_FIELDS and type(v) is int and 0<=v<=MAX_TOKENS_PER_FIELD} if isinstance(tokens,dict) else {}
    record=dict(schema_version=1,event=event,timestamp=datetime.now(timezone.utc).isoformat(),
        request_id=trace.request_id if type(trace.request_id) is str and re.fullmatch('[0-9a-f]{32}',trace.request_id) else 'unavailable',
        route=safe_enum(trace.route, ROUTES, 'unmatched'),method=safe_enum(trace.method, METHODS, 'OTHER'),**fields)
    try:
        LOGGER.info(json.dumps(record,ensure_ascii=True,allow_nan=False,separators=(',',':')))
    except Exception:
        # A broken operator log sink must not change chat behavior or expose an exception.
        pass


def increment(counter, key, amount=1):
    counter[key]=min(MAX_COUNTER,counter.get(key,0)+amount)


def duration_ms(clock, started):
    value=(clock()-started)*1000
    return round(max(0,min(value,86_400_000)),3) if math.isfinite(value) else 0


@dataclass
class Trace:
    metrics: object
    request_id: str
    route: str
    method: str
    started: float
    reason: str | None = None
    providers: list = field(default_factory=list)


class Telemetry:
    def __init__(self, clock=time.perf_counter):
        configure_logging()
        self.clock=clock
        self.started=clock()
        self.lock=threading.Lock()
        self.requests=Counter(); self.request_outcomes=Counter(); self.request_errors=Counter(); self.providers=Counter(); self.http=Counter(); self.usage=Counter()
        self.tokens=Counter(); self.coverage=Counter(); self.latencies={}
        self.active_requests=0; self.active_providers=0; self.provider_events_dropped=0

    def provider_active(self, delta):
        with self.lock:
            self.active_providers=max(0,min(MAX_COUNTER,self.active_providers+delta))

    def request_start(self):
        with self.lock:self.active_requests=min(MAX_COUNTER,self.active_requests+1)

    def complete(self, trace, status, completion):
        elapsed=duration_ms(self.clock,trace.started)
        status_class=str(status//100)+'xx' if 100<=status<=599 else 'other'
        with self.lock:
            self.active_requests=max(0,self.active_requests-1)
            increment(self.requests,(trace.route,trace.method,status_class))
            increment(self.request_outcomes,(trace.route,completion))
            if trace.reason is not None:increment(self.request_errors,(trace.route,trace.reason))
            key=(trace.route,trace.method)
            stats=self.latencies.setdefault(key,dict(count=0,sum_ms=0.0,max_ms=0.0))
            stats['count']=min(MAX_COUNTER,stats['count']+1)
            stats['sum_ms']=min(float(MAX_COUNTER),stats['sum_ms']+elapsed)
            stats['max_ms']=max(stats['max_ms'],elapsed)
        for provider in trace.providers:
            outcome=provider['outcome']
            if outcome=='cancelled' and status==504:outcome='timeout'
            with self.lock:increment(self.providers,(provider['kind'],outcome))
            emit('provider_completed',trace,provider=provider['kind'],outcome=outcome,
                duration_ms=provider['duration_ms'],http_attempts=provider['attempts'],last_http_status=provider['status'])
        emit('request_completed',trace,status=status,duration_ms=elapsed,
            completion=completion,error_code=trace.reason)

    def snapshot(self):
        with self.lock:
            return dict(schema_version=1,scope='application_instance_single_process',durable=False,
                uptime_seconds=round(max(0,self.clock()-self.started),3),
                active_requests=self.active_requests,active_provider_operations=self.active_providers,
                provider_events_dropped=self.provider_events_dropped,
                requests=[dict(route=r,method=m,status_class=s,count=n) for (r,m,s),n in sorted(self.requests.items())],
                request_errors=[dict(route=r,error_code=c,count=n) for (r,c),n in sorted(self.request_errors.items())],
                request_outcomes=[dict(route=r,completion=c,count=n) for (r,c),n in sorted(self.request_outcomes.items())],
                request_duration=[dict(route=r,method=m,**dict(v)) for (r,m),v in sorted(self.latencies.items())],
                provider_operations=[dict(provider=k,outcome=o,count=n) for (k,o),n in sorted(self.providers.items())],
                provider_http=[dict(provider=k,status=s,count=n) for (k,s),n in sorted(self.http.items())],
                usage_observations=[dict(provider=k,state=s,count=n) for (k,s),n in sorted(self.usage.items())],
                reported_tokens=[dict(provider=k,field=f,total=n,observations=self.coverage[(k,f)]) for (k,f),n in sorted(self.tokens.items())],
                accounting='Reported usage only; missing/invalid/unparsed usage is unknown, not zero cost. No price estimate.')


def mark_error(code):
    trace=TRACE.get()
    if trace is not None:trace.reason=safe_enum(code, REASONS, 'internal_error')


def provider_http_attempt():
    span=SPAN.get()
    if span is not None:
        span['attempts']=min(16,span['attempts']+1)
        with span['trace'].metrics.lock:increment(span['trace'].metrics.http,(span['kind'],'attempt'))


def provider_http_response(status):
    span=SPAN.get()
    if span is None:return
    span['status']=status if type(status) is int and 100<=status<=599 else 0
    label=str(status) if status in {200,400,401,403,404,429} else '5xx' if 500<=status<=599 else 'other'
    with span['trace'].metrics.lock:increment(span['trace'].metrics.http,(span['kind'],label))


def provider_usage(value):
    span=SPAN.get()
    if span is None:return
    tokens={};state='missing'
    if value is not None:
        if not isinstance(value,dict):state='malformed'
        else:
            malformed=False
            for name in TOKEN_FIELDS:
                if name not in value:continue
                v=value[name]
                if type(v) is int and 0<=v<=MAX_TOKENS_PER_FIELD:tokens[name]=v
                else:malformed=True
            if len(tokens)==3 and tokens['total_tokens']!=tokens['prompt_tokens']+tokens['completion_tokens']:
                malformed=True;tokens={}
            state='malformed' if malformed else 'complete' if len(tokens)==3 else 'partial' if tokens else 'missing'
    trace=span['trace'];metrics=trace.metrics
    with metrics.lock:
        increment(metrics.usage,(span['kind'],state))
        for name,n in tokens.items():
            increment(metrics.tokens,(span['kind'],name),n)
            increment(metrics.coverage,(span['kind'],name))
    emit('provider_usage',trace,provider=span['kind'],usage_state=state,reported_tokens=tokens)


def mark_provider_deadline():
    trace=TRACE.get()
    if trace is not None:
        for event in reversed(trace.providers):
            if event['outcome']=='cancelled':event['outcome']='timeout';break


def observed_provider(kind):
    def decorate(function):
        @wraps(function)
        async def observed(*args,**kwargs):
            trace=TRACE.get()
            if trace is None:return await function(*args,**kwargs)
            selected=('demo_selection' if trace.route=='/api/demo/chat' else 'research_selection') if kind=='selection' else kind
            if selected not in KINDS:return await function(*args,**kwargs)
            span=dict(trace=trace,kind=selected,attempts=0,status=0)
            token=SPAN.set(span);started=trace.metrics.clock();outcome='internal_error'
            trace.metrics.provider_active(1)
            try:
                result=await function(*args,**kwargs)
                outcome='invalid_response' if result is None else 'not_called' if getattr(result,'response_kind',None)=='safety_boundary' else 'success'
                return result
            except asyncio.CancelledError:
                outcome='cancelled';raise
            except Exception as exc:
                outcome={'provider_timeout':'timeout','provider_rate_limited':'rate_limited',
                    'provider_not_configured':'configuration_error','provider_configuration_error':'configuration_error',
                    'provider_unavailable':'unavailable','provider_invalid_response':'invalid_response'}.get(safe_enum(getattr(exc,'code',None),REASONS,'internal_error'),'internal_error')
                raise
            finally:
                trace.metrics.provider_active(-1)
                if len(trace.providers)<8:
                    trace.providers.append(dict(kind=selected,outcome=outcome,duration_ms=duration_ms(trace.metrics.clock,started),attempts=span['attempts'],status=span['status']))
                else:
                    with trace.metrics.lock:trace.metrics.provider_events_dropped=min(MAX_COUNTER,trace.metrics.provider_events_dropped+1)
                SPAN.reset(token)
        return observed
    return decorate


class OperationalMiddleware:
    """Outermost user middleware: fixed route labels, fresh IDs and safe error metadata."""
    def __init__(self,app,metrics):self.app=app;self.metrics=metrics

    async def __call__(self,scope,receive,send):
        if scope['type']!='http':return await self.app(scope,receive,send)
        path=scope.get('path','');method=scope.get('method','')
        trace=Trace(self.metrics,uuid4().hex,path if path in ROUTES else 'unmatched',method if method in METHODS else 'OTHER',self.metrics.clock())
        token=TRACE.set(trace);status=500;begun=False;completion='response'
        self.metrics.request_start()
        async def traced_send(message):
            nonlocal status,begun
            if message['type']=='http.response.start':
                status=message['status'];begun=True
                headers=[(k,v) for k,v in message.get('headers',[]) if k.lower() not in {b'x-request-id',b'cache-control'}]
                message=dict(message,headers=headers+[(b'x-request-id',trace.request_id.encode('ascii')),(b'cache-control',b'no-store')])
            await send(message)
        try:
            await self.app(scope,receive,traced_send)
        except asyncio.CancelledError:
            completion='cancelled';status=499;raise
        except Exception:
            completion='internal_error';trace.reason='internal_error'
            if not begun:
                status=500
                await JSONResponse(status_code=500,content={'error':{'code':'internal_error','message':'Request could not be completed safely.'}})(scope,receive,traced_send)
            else:
                completion='aborted'
                raise RuntimeError('Request failed after response headers') from None
        finally:
            self.metrics.complete(trace,status,completion)
            TRACE.reset(token)
