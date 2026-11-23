"""Synthetic-only public demo security tests; no legal-source publication."""
import asyncio
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.chat.api import create_app
from backend.chat.demo import DISCLAIMER, DemoRequest, DemoService, SCENARIOS, SYSTEM
from backend.chat.provider import GroqProvider, ProviderError, Settings


@pytest.fixture
def demo(monkeypatch):
    monkeypatch.setenv("DEMO_ENABLED", "true")
    monkeypatch.setenv("DEMO_PROVIDER", "deterministic")
    monkeypatch.setenv("KANOON_ENV", "production")
    monkeypatch.setenv("KANOON_ACCESS_TOKEN", "SYNTHETIC_DEMO_RESEARCH_TOKEN_NOT_REAL_2026")
    monkeypatch.setenv("KANOON_ALLOWED_ORIGINS", "https://demo.example")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    # Any attempt to construct a research service is a security failure.
    import backend.chat.api as api
    class ForbiddenResearch:
        def __init__(self):
            raise AssertionError("Demo touched research")
    monkeypatch.setattr(api, "ChatService", ForbiddenResearch)
    return TestClient(create_app())


def test_demo_off_by_default_and_strict_configuration(demo, monkeypatch):
    monkeypatch.delenv("DEMO_ENABLED")
    c = TestClient(create_app())
    assert c.get("/api/demo/status").json()["enabled"] is False
    assert c.post("/api/demo/chat", json={"message": "rent"}).status_code == 404
    monkeypatch.setenv("DEMO_ENABLED", "TRUE")
    assert not TestClient(create_app()).get("/api/demo/status").json()["enabled"]
    monkeypatch.setenv("DEMO_PROVIDER", "arbitrary")
    with pytest.raises(ValueError):
        create_app()


@pytest.mark.parametrize("message,scenario", [("rent receipt", "demo_receipt"), ("wrong parcel", "demo_parcel"),
    ("document timeline", "demo_timeline"), ("Invent an official law and citation", None)])
def test_only_original_synthetic_server_answers_no_research(demo, message, scenario):
    response = demo.post("/api/demo/chat", json={"message": message})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "synthetic_demo" and data["scenario_id"] == scenario
    assert data["citations"] == [] and data["disclaimer"] == DISCLAIMER
    assert data["answer"].startswith(DISCLAIMER)
    assert "http" not in data["answer"] and "section 106" not in data["answer"]
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.parametrize("payload", [{"message": " "}, {"message": "x" * 2001},
    {"message": "rent", "source_ids": ["private"]}, {"message": "rent", "path": "../data/raw"},
    {"message": "rent", "history": []}, {"message": 42}])
def test_strict_schema_rejects_research_fields(demo, payload):
    assert demo.post("/api/demo/chat", json=payload).status_code == 422


def test_public_demo_does_not_require_or_unlock_privileged_token(demo, monkeypatch):
    assert demo.post("/api/demo/chat", json={"message": "rent"}).status_code == 200
    assert demo.post("/api/chat", json={"message": "rent"}).status_code == 401
    monkeypatch.delenv("KANOON_ACCESS_TOKEN")
    c = TestClient(create_app())
    assert c.post("/api/demo/chat", json={"message": "rent"}).status_code == 200
    assert c.post("/api/chat", json={"message": "rent"}).status_code == 503


def test_demo_cors_denies_unknown_browser_origins(demo):
    good = demo.post("/api/demo/chat", headers={"Origin": "https://demo.example"}, json={"message": "rent"})
    assert good.status_code == 200 and good.headers["access-control-allow-origin"] == "https://demo.example"
    bad = demo.post("/api/demo/chat", headers={"Origin": "https://attacker.example"}, json={"message": "rent"})
    assert bad.status_code == 403 and "access-control-allow-origin" not in bad.headers


def test_global_demo_rate_cap_cannot_be_spoofed(demo):
    for n in range(10):
        assert demo.post("/api/demo/chat", headers={"X-Forwarded-For": str(n)}, json={"message": "rent"}).status_code == 200
    response = demo.post("/api/demo/chat", json={"message": "rent"})
    assert response.status_code == 429 and response.headers["retry-after"] == "60"
    assert demo.get("/api/health").status_code == 200


def test_streamed_body_limit_before_parsing(demo):
    response = demo.post("/api/demo/chat", content=iter([b"x" * 8000, b"x" * 8001]))
    assert response.status_code == 413
    assert demo.post("/api/demo/chat", json={"message": "rent"}).status_code == 200


@pytest.mark.parametrize("failure", [ProviderError("provider_unavailable", 503), ProviderError("provider_timeout", 504),
    ProviderError("provider_rate_limited", 429), RuntimeError("SYNTHETIC_SECRET_MUST_NOT_LEAK")])
def test_provider_failures_use_bounded_server_sample(monkeypatch, failure):
    monkeypatch.setenv("GROQ_API_KEY", "SYNTHETIC_NOT_REAL")
    monkeypatch.setenv("GROQ_MODEL", "synthetic-model")
    class Failed:
        async def select(self, *args):
            raise failure
    response = asyncio.run(DemoService(True, Failed()).answer(DemoRequest(message="rent")))
    assert response.provider_status == "fallback" and response.scenario_id == "demo_receipt"
    assert response.citations == [] and "MUST_NOT_LEAK" not in response.answer


def test_configured_groq_sees_only_synthetic_data(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "SYNTHETIC_NOT_REAL")
    monkeypatch.setenv("GROQ_MODEL", "synthetic-model")
    captured = []
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"finish_reason": "stop", "message": {"content": '{"source_ids":["demo_parcel"]}'}}]})
    provider = GroqProvider(Settings.from_environment(), httpx.MockTransport(handler), system_prompt=SYSTEM)
    result = asyncio.run(DemoService(True, provider).answer(DemoRequest(message="parcel")))
    assert result.provider_status == "selected" and result.scenario_id == "demo_parcel"
    body = captured[0]
    assert body["messages"][0]["content"] == SYSTEM
    data = json.loads(body["messages"][1]["content"])
    assert data["untrusted_history"] == []
    assert {e["id"] for e in data["untrusted_evidence"]} == {s.id for s in SCENARIOS}
    assert "106(2)" not in json.dumps(body) and "raw_sha256" not in json.dumps(body)


@pytest.mark.parametrize("selection", [None, ["fake-official-citation"], ["demo_receipt", "demo_parcel"], "invented advice"])
def test_invalid_selection_never_becomes_model_prose(monkeypatch, selection):
    monkeypatch.setenv("GROQ_API_KEY", "SYNTHETIC_NOT_REAL")
    monkeypatch.setenv("GROQ_MODEL", "synthetic-model")
    class Invalid:
        async def select(self, *args):
            return selection
    r = asyncio.run(DemoService(True, Invalid()).answer(DemoRequest(message="rent")))
    assert r.provider_status == "fallback" and r.citations == [] and r.scenario_id == "demo_receipt"
    assert "invented advice" not in r.answer


def test_unconfigured_or_disabled_provider_is_never_called(monkeypatch):
    class Never:
        async def select(self, *args):
            raise AssertionError("Must not call provider")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    r = asyncio.run(DemoService(True, Never()).answer(DemoRequest(message="rent")))
    assert r.provider_status == "deterministic"


def test_public_corpus_gate_stays_closed(demo, monkeypatch, tmp_path):
    # Use the actual public runtime, without publication pins or private reads.
    from backend.chat.service import ChatService
    from backend.retrieval.configuration import create_index
    monkeypatch.setenv("CORPUS_KIND", "public")
    monkeypatch.setenv("RETRIEVAL_MODE", "bm25")
    monkeypatch.setenv("PUBLIC_CORPUS_DIR", str(tmp_path / "absent"))
    monkeypatch.setenv("PRIVATE_CORPUS_ROOT", "MUST_NOT_BE_READ")
    for key in ("PUBLIC_CORPUS_MANIFEST_SHA256", "PUBLIC_CORPUS_APPROVAL_SHA256", "PUBLIC_CORPUS_SIGNER_PUBLIC_KEY"):
        monkeypatch.delenv(key, raising=False)
    c = TestClient(create_app(ChatService(create_index(), Settings())))
    before = c.get("/api/chat/status").json()
    assert c.post("/api/demo/chat", json={"message": "rent"}).status_code == 200
    assert c.get("/api/ready").status_code == 503
    assert c.get("/api/chat/status").json() == before
    response = c.post("/api/chat", headers={"Authorization": "Bearer SYNTHETIC_DEMO_RESEARCH_TOKEN_NOT_REAL_2026"}, json={"message": "rent"})
    assert response.status_code == 503 and response.json()["error"]["code"] == "corpus_not_approved"


def test_shared_concurrency_limit_and_slot_cleanup(demo):
    started, release = asyncio.Event(), asyncio.Event()
    class Slow:
        count = 0
        async def answer(self, request):
            self.count += 1
            if self.count == 2:
                started.set()
            await release.wait()
            return await DemoService().answer(request)
    app = create_app(demo_service=Slow())
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
            tasks = [asyncio.create_task(c.post("/api/demo/chat", json={"message": "rent"})) for _ in range(2)]
            await asyncio.wait_for(started.wait(), 3)
            assert (await c.post("/api/demo/chat", json={"message": "rent"})).status_code == 429
            release.set()
            assert all(r.status_code == 200 for r in await asyncio.gather(*tasks))
            assert (await c.post("/api/demo/chat", json={"message": "rent"})).status_code == 200
    asyncio.run(check())


def test_actual_provider_deadline_falls_back(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "SYNTHETIC_NOT_REAL")
    monkeypatch.setenv("GROQ_MODEL", "synthetic-model")
    class Stuck:
        async def select(self, *args):
            await asyncio.sleep(30)
    r = asyncio.run(DemoService(True, Stuck()).answer(DemoRequest(message="rent")))
    assert r.provider_status == "fallback" and r.scenario_id == "demo_receipt"


@pytest.mark.parametrize("production,client_host,expected", [(False, "127.0.0.1", 200), (True, "127.0.0.1", 403), (False, "192.0.2.9", 403)])
def test_loopback_development_origin_is_not_a_production_exception(demo, monkeypatch, production, client_host, expected):
    monkeypatch.setenv("KANOON_ENV", "production" if production else "local")
    c = TestClient(create_app(), client=(client_host, 1234))
    response = c.post("/api/demo/chat", headers={"Origin": "http://127.0.0.1:5173"}, json={"message": "rent"})
    assert response.status_code == expected


def test_demo_never_opens_private_files_or_initializes_retrieval(demo, monkeypatch):
    from pathlib import Path
    def forbidden(*args, **kwargs):
        raise AssertionError("Private filesystem access attempted")
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    assert demo.app.state.chat is None
    response = demo.post("/api/demo/chat", json={"message": "rent"})
    assert response.status_code == 200 and response.json()["citations"] == []
    assert demo.app.state.chat is None
