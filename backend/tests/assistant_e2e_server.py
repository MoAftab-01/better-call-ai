"""SYNTHETIC transport fixture for browser automation; never a deployment entry point."""
import json
import os
from pathlib import Path
import httpx
from backend.chat.api import create_app
from backend.chat.general import GeneralService
from backend.chat.provider import Settings
from backend.chat.service import ChatService

missing=Path(__file__).resolve().parents[1]/"data/test-runs/NO-ASSISTANT-CORPUS-DO-NOT-CREATE"
assert not missing.exists()
os.environ.update(KANOON_ENV="local",CORPUS_KIND="public",RETRIEVAL_MODE="bm25",PUBLIC_CORPUS_DIR=str(missing),
    DEMO_ENABLED="true",DEMO_PROVIDER="deterministic",AI_ASSISTANT_ENABLED="true",AI_ASSISTANT_RPM="30",AI_ASSISTANT_DAILY_LIMIT="1000",KANOON_ALLOWED_ORIGINS="")
for key in ("PUBLIC_CORPUS_MANIFEST_SHA256","PUBLIC_CORPUS_APPROVAL_FILE","PUBLIC_CORPUS_APPROVAL_SHA256","PUBLIC_CORPUS_SIGNER_PUBLIC_KEY"):
    os.environ.pop(key,None)
def handler(request):
    body=json.loads(request.content)
    answer="SYNTHETIC transport test explanation: " + body['messages'][-1]['content']
    return httpx.Response(200,json={'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'answer':answer,'requires_professional_help':False})}}]})
app=create_app(ChatService(settings=Settings()),general_service=GeneralService(Settings('SYNTHETIC_NOT_REAL','synthetic-model'),httpx.MockTransport(handler)))
@app.middleware('http')
async def marker(request,call_next):
    response=await call_next(request)
    response.headers['X-Kanoon-Public-Website-Test']='no-corpus'
    response.headers['X-Kanoon-General-Test']='synthetic-transport'
    return response
