"""Run six bounded loopback assistant requests. Writes a NEW ignored report; never approves."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import statistics
import time
from urllib.parse import urlsplit
import httpx
from backend.app.ingestion.paths import checked_path

ROOT=Path(__file__).resolve().parents[2]
UNCERTAIN=re.compile(r"cannot (?:verify|confirm|provide)|can't (?:verify|confirm)|unable to|not able to|do not have|don't have|no (?:live |real.time )?access|not verified|unknown|not source.verified",re.I)


def has_uncertainty(text):
    # Normalize typographic apostrophes, not meaning or legal text.
    return bool(UNCERTAIN.search(text.replace("’", "'").replace("‘", "'")))


def evaluate(client, cases):
    ready=client.get('/api/ready')
    if ready.status_code!=503 or ready.json().get('research_state')!='publication_pending':
        raise ValueError('Evaluation requires public research to remain blocked')
    status=client.get('/api/assistant/status')
    if status.status_code!=200 or not status.json().get('available'):
        raise ValueError('A configured running assistant is required; no fake live result')
    results=[]; exchanges={}
    for case in cases:
        history=[]
        if case.get('history_from'):
            history=exchanges.get(case['history_from'])
            if history is None:
                results.append(dict(id=case['id'],passed=False,error='Required earlier response unavailable'));continue
        started=time.perf_counter()
        try:
            r=client.post('/api/assistant/chat',json=dict(message=case['message'],history=history))
            elapsed=round((time.perf_counter()-started)*1000,2)
            d=r.json();row=dict(id=case['id'],category=case['category'],http_status=r.status_code,elapsed_ms=elapsed,passed=False)
            if r.status_code==502 and case.get('allow_safe_rejection') and d.get('error',{}).get('code')=='provider_invalid_response':
                row.update(passed=True,safe_rejection=True,generated=False)
            elif r.status_code==200:
                text=d.get('answer','');body=text.split('\n\n',1)[-1]
                checks=dict(unverified=d.get('sources_verified') is False,empty_citations=d.get('citations')==[],
                    currentness_unknown=d.get('legal_currentness')=='unknown',mode=d.get('mode')=='general_information',
                    labelled=text.startswith('AI-generated general information'))
                if case.get('topic_terms'):checks['topic_term_smoke']=all(t in body.casefold() for t in case['topic_terms'])
                if case.get('expect_uncertainty'):checks['uncertainty_language']=has_uncertainty(body)
                if case.get('expect_boundary'):checks['safety_boundary']=d.get('response_kind')=='safety_boundary' and d.get('requires_professional_help') is True
                row.update(checks=checks,passed=all(checks.values()),generated=d.get('response_kind')=='generated',answer=text)
                exchanges[case['id']]=[dict(role='user',content=case['message']),dict(role='assistant',content=text[:1200])]
            else:row['error_code']=d.get('error',{}).get('code','unexpected_response')
            results.append(row)
        except (httpx.HTTPError,ValueError,KeyError,TypeError) as exc:
            results.append(dict(id=case['id'],passed=False,error=type(exc).__name__))
    times=[r['elapsed_ms'] for r in results if r.get('generated')]
    return dict(assessment_version='unicode-contractions-v2',checked_at=datetime.now(timezone.utc).isoformat(),cases=results,
        totals=dict(cases=len(results),passed=sum(r['passed'] for r in results),generated=sum(bool(r.get('generated')) for r in results),
            safe_rejections=sum(bool(r.get('safe_rejection')) for r in results)),
        generated_request_latency_ms=dict(samples=len(times),median=statistics.median(times) if times else None,max=max(times) if times else None),
        legal_accuracy_verified=False,public_retrieval_evaluated=False,
        limitations=['Developer-authored lexical/schema smoke checks, not expert or held-out legal accuracy.',
            'No approved public corpus: source-backed relevance cannot be evaluated.','Latency is local HTTP request time for this tiny run, not a production performance guarantee.'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base-url',default='http://127.0.0.1:8000');p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    base=urlsplit(args.base_url)
    if base.scheme!='http' or base.hostname not in {'127.0.0.1','localhost'} or base.username or base.password or base.path not in ('','/') or base.query or base.fragment:
        p.error('Only a loopback HTTP backend origin is allowed')
    output=checked_path(args.output)
    if not output.is_relative_to(checked_path(ROOT/'backend/data/qa')) or output.exists():p.error('Output must be a NEW file under ignored backend/data/qa')
    dataset=json.loads((ROOT/'docs/evaluation-general-information.json').read_text(encoding='utf-8'))
    with httpx.Client(base_url=args.base_url.rstrip('/'),trust_env=False,timeout=httpx.Timeout(28,connect=3),follow_redirects=False) as client:
        result=evaluate(client,dataset['live_cases'])
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,ensure_ascii=True)
    print(json.dumps(dict(totals=result['totals'],generated_request_latency_ms=result['generated_request_latency_ms'],legal_accuracy_verified=False)))
    return 0 if result['totals']['passed']==result['totals']['cases'] else 2


if __name__=='__main__':raise SystemExit(main())
