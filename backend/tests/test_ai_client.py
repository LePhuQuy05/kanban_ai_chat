import json

import pytest

from backend.app.ai_client import (
    CONNECTIVITY_PROMPT,
    OPENROUTER_MODEL,
    OpenRouterError,
    run_ai_connectivity_check,
)


class FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_run_ai_connectivity_check_builds_request_and_returns_text(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    def fake_urlopen(http_request, timeout: int):
        captured["timeout"] = timeout
        captured["method"] = http_request.get_method()
        captured["url"] = http_request.full_url
        captured["authorization"] = http_request.headers.get("Authorization")
        captured["content_type"] = http_request.headers.get("Content-type")
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return FakeHTTPResponse({"choices": [{"message": {"content": "4"}}]})

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("backend.app.ai_client.request.urlopen", fake_urlopen)

    reply = run_ai_connectivity_check()

    assert reply == "4"
    assert captured["timeout"] == 30
    assert captured["method"] == "POST"
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["content_type"] == "application/json"
    assert captured["body"]["model"] == OPENROUTER_MODEL
    assert captured["body"]["messages"][0]["content"] == CONNECTIVITY_PROMPT


def test_run_ai_connectivity_check_raises_for_invalid_response(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(http_request, timeout: int):
        return FakeHTTPResponse({"choices": []})

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr("backend.app.ai_client.request.urlopen", fake_urlopen)

    with pytest.raises(OpenRouterError):
        run_ai_connectivity_check()
