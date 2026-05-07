import os
import json

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app

AUTH_HEADERS = {
    "X-Username": "user",
    "X-Password": "password",
}


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


def test_ai_chat_returns_reply_without_board_mutation(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "pm.db"))
    board = client.get("/api/board", headers=AUTH_HEADERS).json()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "backend.app.ai_chat_service.request_openrouter_chat",
        lambda api_key, messages: {
            "choices": [
                {
                    "message": {
                        "content": '{"assistantReply":"No board update needed.","board":null}'
                    }
                }
            ]
        },
    )

    response = client.post(
        "/api/ai/chat",
        headers=AUTH_HEADERS,
        json={
            "conversation": [{"role": "assistant", "content": "What would you like to change?"}],
            "board": board,
            "userMessage": "Just summarize my board.",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "reply": "No board update needed.",
        "mutationApplied": False,
        "board": None,
    }


def test_ai_chat_applies_valid_board_mutation(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "pm.db"))
    board = client.get("/api/board", headers=AUTH_HEADERS).json()
    board["columns"][0]["title"] = "AI Backlog"

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "backend.app.ai_chat_service.request_openrouter_chat",
        lambda api_key, messages: {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"assistantReply":"I renamed Backlog.","board":'
                            + json.dumps(board)
                            + "}"
                        )
                    }
                }
            ]
        },
    )

    response = client.post(
        "/api/ai/chat",
        headers=AUTH_HEADERS,
        json={
            "conversation": [],
            "board": board,
            "userMessage": "Rename backlog column to AI Backlog.",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mutationApplied"] is True
    assert payload["board"]["columns"][0]["title"] == "AI Backlog"

    read_back = client.get("/api/board", headers=AUTH_HEADERS)
    assert read_back.status_code == 200
    assert read_back.json()["columns"][0]["title"] == "AI Backlog"


def test_ai_chat_rejects_invalid_model_payload(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    client = TestClient(create_app(tmp_path / "pm.db"))
    board = client.get("/api/board", headers=AUTH_HEADERS).json()

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "backend.app.ai_chat_service.request_openrouter_chat",
        lambda api_key, messages: {"choices": [{"message": {"content": "not-json"}}]},
    )

    response = client.post(
        "/api/ai/chat",
        headers=AUTH_HEADERS,
        json={
            "conversation": [],
            "board": board,
            "userMessage": "Move card 1 to review.",
        },
    )
    assert response.status_code == 502
    assert response.json() == {"detail": "OpenRouter request failed."}
