import os

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_root_returns_html() -> None:
    client = TestClient(create_app())
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Frontend build not found" in response.text


def test_hello_api_returns_message() -> None:
    client = TestClient(create_app())
    response = client.get("/api/hello")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello from FastAPI"}


def test_ai_check_returns_reply_with_mocked_openrouter(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(create_app())
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "backend.app.ai_client.request_openrouter_completion",
        lambda api_key, prompt: {"choices": [{"message": {"content": "4"}}]},
    )

    response = client.post("/api/ai/check")

    assert response.status_code == 200
    assert response.json() == {"reply": "4"}


def test_ai_check_returns_502_when_openrouter_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TestClient(create_app())
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    response = client.post("/api/ai/check")

    assert response.status_code == 502
    assert response.json() == {"detail": "OpenRouter request failed."}


@pytest.mark.skipif(
    os.getenv("RUN_OPENROUTER_SMOKE_TEST") != "1",
    reason="Set RUN_OPENROUTER_SMOKE_TEST=1 to enable live OpenRouter smoke test.",
)
def test_ai_check_live_openrouter_smoke() -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        pytest.skip("OPENROUTER_API_KEY is required for live smoke test.")

    client = TestClient(create_app())
    response = client.post("/api/ai/check")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("reply"), str)
    assert payload["reply"].strip()
