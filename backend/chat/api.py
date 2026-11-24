import asyncio
from collections import deque
import logging
import os
import secrets
import threading
import time
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from .demo import DemoRequest, DemoResponse, DemoService
from .general import GeneralRequest, GeneralResponse, GeneralService
from .references import reference_directory
from .models import ChatRequest, ChatResponse
from .provider import ProviderError
from .service import ChatService

logger = logging.getLogger("kanoon.chat")
ERRORS = {
    "assistant_disabled": "The AI Assistant is disabled. The synthetic demo may still be available.",
    "assistant_rate_limited": "AI Assistant limit reached. Please retry later or use the synthetic demo.",
    "assistant_origin_denied": "This browser origin is not allowed to use the AI Assistant.",
    "provider_not_configured": "AI Assistant is unavailable: the operator must configure Groq. You can use the synthetic demo.",
    "demo_disabled": "The synthetic demo is not enabled.",
    "demo_origin_denied": "This browser origin is not allowed to use the demo.",
    "demo_rate_limited": "Demo limit reached. Wait one minute before retrying.",
    "demo_timeout": "The demo timed out. Retry shortly.",
    "demo_unavailable": "The synthetic demo is unavailable. Retry shortly.",
    "corpus_not_approved": "The public corpus has not been approved for serving.",
    "access_required": "Enter the private demo access token supplied by the operator.",
    "deployment_not_configured": "Public chat is disabled until the operator configures access protection.",
    "service_busy": "Two research requests are already running. Retry shortly.",
    "local_rate_limited": "Local request limit reached. Wait one minute before retrying.",
    "request_too_large": "The request body exceeds the 16,000-byte limit. Shorten the recent history or question.",
    "provider_timeout": "Groq timed out. Retry shortly; no answer was fabricated.",
    "provider_rate_limited": "Groq rate limit reached. Wait before retrying.",
    "provider_configuration_error": "Check the backend Groq key and model configuration.",
    "provider_unavailable": "Groq is unavailable. Retry shortly.",
    "provider_invalid_response": "Groq returned an invalid response.",
    "source_changed": "Source integrity changed during this request. Restart after checking the evidence bundle.",
}


def create_app(service=None, *, demo_service=None, general_service=None):
    app = FastAPI(title="Better Call AI", description="Archival research workspace; public source publication is required. No current-law certification.")
    app.state.chat = service
    lock, arrivals = threading.Lock(), deque()
    demo_enabled = os.environ.get("DEMO_ENABLED", "false") == "true"
    demo_provider = os.environ.get("DEMO_PROVIDER", "deterministic")
    if demo_provider not in {"deterministic", "groq"}:
        raise ValueError("DEMO_PROVIDER must be deterministic or groq")
    demo = demo_service if demo_service is not None else DemoService(demo_provider == "groq")
    demo_arrivals = deque()
    assistant_enabled = os.environ.get("AI_ASSISTANT_ENABLED", "false") == "true"
    general = general_service if general_service is not None else GeneralService()
    def bounded_setting(name, default, maximum):
        value = int(os.environ.get(name, str(default)))
        if not 1 <= value <= maximum:
            raise ValueError(name + " is outside supported bounds")
        return value
    assistant_rpm = bounded_setting("AI_ASSISTANT_RPM", 6, 30)
    assistant_daily = bounded_setting("AI_ASSISTANT_DAILY_LIMIT", 100, 1000)
    assistant_arrivals = deque()
    environment = os.environ.get("KANOON_ENV", "local")
    if environment not in {"local", "production"}:
        raise ValueError("KANOON_ENV must be local or production")
    production = environment == "production"
    access_token = os.environ.get("KANOON_ACCESS_TOKEN", "")
    auth_ready = len(access_token) >= 32 and access_token != os.environ.get("GROQ_API_KEY", "")
    origins = [s.strip() for s in os.environ.get("KANOON_ALLOWED_ORIGINS", "").split(",") if s.strip()]
    from urllib.parse import urlparse
    if any(urlparse(s).scheme != "https" or not urlparse(s).netloc or urlparse(s).path not in ("", "/") or
           urlparse(s).username or urlparse(s).query or urlparse(s).fragment for s in origins):
        raise ValueError("Production CORS origins must be explicit HTTPS origins")
    origins = [s.rstrip("/") for s in origins]
    active = 0

    def get_service():
        with lock:
            if app.state.chat is None:
                app.state.chat = ChatService()
        return app.state.chat

    def error(code, status, retry=None):
        headers = {"Cache-Control": "no-store"}
        if retry:
            headers["Retry-After"] = str(retry)
        return JSONResponse(status_code=status, content={"error": {"code": code,
            "message": ERRORS.get(code, "Request could not be completed safely.")}}, headers=headers)

    @app.middleware("http")
    async def privacy_headers(request, call_next):
        nonlocal active
        # Bound actual streamed body bytes, including chunked requests, before JSON parsing.
        is_demo = request.url.path == "/api/demo/chat" and request.method == "POST"
        is_general = request.url.path == "/api/assistant/chat" and request.method == "POST"
        is_public = is_demo or is_general
        guarded = (request.url.path == "/api/chat" or is_public) and request.method == "POST"
        if is_general:
            if not assistant_enabled:
                return error("assistant_disabled", 404)
            origin = request.headers.get("Origin")
            local_origin = (not production and origin and urlparse(origin).scheme == "http"
                and urlparse(origin).hostname in {"127.0.0.1", "localhost"}
                and request.client is not None and request.client.host in {"127.0.0.1", "::1"})
            if origin and origin not in origins and not local_origin:
                return error("assistant_origin_denied", 403)
            now = time.monotonic()
            with lock:
                while assistant_arrivals and assistant_arrivals[0] < now - 86400:
                    assistant_arrivals.popleft()
                if len(assistant_arrivals) >= assistant_daily or sum(t >= now - 60 for t in assistant_arrivals) >= assistant_rpm:
                    return error("assistant_rate_limited", 429, 60)
                assistant_arrivals.append(now)
        if is_demo:
            if not demo_enabled:
                return error("demo_disabled", 404)
            origin = request.headers.get("Origin")
            local_origin = (not production and origin and urlparse(origin).scheme == "http"
                and urlparse(origin).hostname in {"127.0.0.1", "localhost"}
                and request.client is not None and request.client.host in {"127.0.0.1", "::1"})
            if origin and origin not in origins and not local_origin:
                return error("demo_origin_denied", 403)
            # Global per-process cap, not spoofable via proxy/IP headers.
            now = time.monotonic()
            with lock:
                while demo_arrivals and demo_arrivals[0] < now - 60:
                    demo_arrivals.popleft()
                if len(demo_arrivals) >= 10:
                    return error("demo_rate_limited", 429, 60)
                demo_arrivals.append(now)
        if guarded:
            if production and not is_public:
                if not auth_ready:
                    return error("deployment_not_configured", 503)
                supplied = request.headers.get("Authorization", "")
                if not secrets.compare_digest(supplied.encode(), ("Bearer " + access_token).encode()):
                    return error("access_required", 401)
            with lock:
                if active >= 2:
                    return error("service_busy", 429, 10)
                active += 1
        try:
            return await bounded_request(request, call_next, guarded)
        finally:
            if guarded:
                with lock:
                    active -= 1

    async def bounded_request(request, call_next, guarded):
        if guarded:
            body = bytearray()
            try:
                async with asyncio.timeout(10):
                    async for chunk in request.stream():
                        body.extend(chunk)
                        if len(body) > 16000:
                            return error("request_too_large", 413)
            except TimeoutError:
                return error("request_body_timeout", 408)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request, _exc):
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_request",
            "message": "Send a nonempty message up to 2,000 characters and at most six recent user/assistant turns (1,200 characters each)."}})

    @app.get("/")
    def welcome():
        return {"message": "Welcome to Better Call AI"}

    @app.get("/api/health")
    def health():
        return {"status": "healthy", "service": "better-call-kanoon"}

    @app.get("/api/ready")
    def ready(chat: ChatService = Depends(get_service)):
        data = chat.status()
        corpus = data["retrieval"]["passages"] > 0
        configured = not production or auth_ready
        ready = configured and (data['available'] or not getattr(chat.index,'public_runtime',False))
        return JSONResponse(status_code=200 if ready else 503, content={
            "status": "ready" if ready else "blocked", "corpus_available": corpus,
            "research_ready": corpus and configured and data['available'], "authentication_required": production,
            "research_state": data['research_state'], "message": data['research_message'],
            "legal_currentness": "unknown"})

    @app.get("/api/chat/status")
    def status(chat: ChatService = Depends(get_service)):
        return dict(**chat.status(), authentication_required=production,
                    deployment_ready=not production or auth_ready)

    @app.get("/api/demo/status")
    def demo_status():
        return {"enabled": demo_enabled, "mode": "synthetic_demo",
            "provider": demo_provider, "research_enabled_by_demo": False}

    @app.post("/api/demo/chat", response_model=DemoResponse)
    async def demo_chat(request: DemoRequest):
        try:
            async with asyncio.timeout(10):
                return await demo.answer(request)
        except TimeoutError:
            return error("demo_timeout", 504)
        except Exception:
            return error("demo_unavailable", 503)

    @app.get("/api/references")
    def references():
        return reference_directory()

    @app.get("/api/assistant/status")
    def assistant_status():
        return {"enabled": assistant_enabled, "available": assistant_enabled and general.configured,
            "mode": "general_information", "sources_verified": False,
            "message": "AI-generated general information — not source-verified legal advice." if general.configured
                else ERRORS["provider_not_configured"]}

    @app.post("/api/assistant/chat", response_model=GeneralResponse)
    async def assistant_chat(request: GeneralRequest):
        try:
            async with asyncio.timeout(22):
                return await general.answer(request)
        except (TimeoutError, ProviderError) as exc:
            return error("provider_timeout" if isinstance(exc, TimeoutError) else exc.code,
                504 if isinstance(exc, TimeoutError) else exc.status,
                getattr(exc, "retry_after", None))
        except Exception:
            return error("provider_unavailable", 503)

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest, chat: ChatService = Depends(get_service)):
        now = time.monotonic()
        with lock:
            while arrivals and arrivals[0] < now - 60:
                arrivals.popleft()
            if len(arrivals) >= 30:
                return error("local_rate_limited", 429, 60)
            arrivals.append(now)
        trace, started = str(uuid4()), time.monotonic()
        try:
            async with asyncio.timeout(25):
                # ChatService offloads hash/search work; provider I/O stays async.
                result = await chat.answer(request)
            logger.info("chat_completed request_id=%s evidence=%s citations=%d elapsed_ms=%d",
                trace, result.evidence_status, len(result.citations), (time.monotonic()-started)*1000)
            return result
        except (TimeoutError, ProviderError) as exc:
            code = "provider_timeout" if isinstance(exc, TimeoutError) else exc.code
            status_code = 504 if isinstance(exc, TimeoutError) else exc.status
            logger.warning("chat_failed request_id=%s code=%s", trace, code)
            return error(code, status_code, getattr(exc, "retry_after", None))
        except Exception:
            logger.error("chat_failed request_id=%s code=internal_error", trace)
            return error("internal_error", 500)

    # Outermost CORS also covers early authentication/size-limit failures.
    if origins:
        app.add_middleware(CORSMiddleware, allow_origins=origins,
            allow_methods=["GET", "POST"], allow_headers=["Content-Type", "Authorization"],
            allow_credentials=False)
    return app
