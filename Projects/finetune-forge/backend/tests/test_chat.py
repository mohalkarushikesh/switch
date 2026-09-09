"""API tests that run fully offline against the mock provider."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_mock_provider() -> None:
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["provider"] == "mock"
    assert body["model"]


def test_chat_echoes_last_user_message() -> None:
    resp = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "hello forge"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "hello forge" in body["reply"]
    assert body["provider"] == "mock"


def test_chat_rejects_empty_message_list() -> None:
    resp = client.post("/api/chat", json={"messages": []})
    assert resp.status_code == 422


def test_chat_honours_generation_overrides() -> None:
    resp = client.post(
        "/api/chat",
        json={
            "messages": [{"role": "user", "content": "tune me"}],
            "temperature": 0.1,
            "max_tokens": 42,
        },
    )
    assert resp.status_code == 200
    assert "max_tokens=42" in resp.json()["reply"]
