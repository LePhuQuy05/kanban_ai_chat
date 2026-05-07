import json
from pathlib import Path

import pytest

from backend.app.ai_chat_service import run_ai_chat_turn
from backend.app.ai_client import OpenRouterError
from backend.app.schemas import AIChatRequest


def build_payload() -> AIChatRequest:
    return AIChatRequest(
        conversation=[{"role": "assistant", "content": "How can I help?"}],
        userMessage="Move one card to review",
        board={
            "columns": [
                {"id": "col-1", "title": "Backlog", "cardIds": ["card-1"]},
            ],
            "cards": {
                "card-1": {
                    "id": "card-1",
                    "title": "Task",
                    "details": "Details",
                }
            },
        },
    )


def test_run_ai_chat_turn_returns_reply_without_mutation(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "backend.app.ai_chat_service.request_openrouter_chat",
        lambda api_key, messages: {
            "choices": [
                {
                    "message": {
                        "content": '{"assistantReply":"Noted. I will keep the board unchanged.","board":null}'
                    }
                }
            ]
        },
    )

    result = run_ai_chat_turn(Path("fake.db"), "user", "password", build_payload())

    assert result.reply == "Noted. I will keep the board unchanged."
    assert result.mutationApplied is False
    assert result.board is None


def test_run_ai_chat_turn_applies_valid_board_mutation(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    payload = build_payload()
    mutated_board_data = payload.board.model_dump()
    mutated_board_data["columns"][0]["title"] = "Updated"
    monkeypatch.setattr(
        "backend.app.ai_chat_service.request_openrouter_chat",
        lambda api_key, messages: {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"assistantReply":"Updated the board.","board":'
                            + json.dumps(mutated_board_data)
                            + "}"
                        )
                    }
                }
            ]
        },
    )
    monkeypatch.setattr(
        "backend.app.ai_chat_service.update_board_for_user",
        lambda db_path, username, password, board: board,
    )

    result = run_ai_chat_turn(Path("fake.db"), "user", "password", payload)

    assert result.mutationApplied is True
    assert result.board is not None
    assert result.board.columns[0].title == "Updated"


def test_run_ai_chat_turn_rejects_invalid_model_payload(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        "backend.app.ai_chat_service.request_openrouter_chat",
        lambda api_key, messages: {"choices": [{"message": {"content": "not-json"}}]},
    )

    with pytest.raises(OpenRouterError):
        run_ai_chat_turn(Path("fake.db"), "user", "password", build_payload())
