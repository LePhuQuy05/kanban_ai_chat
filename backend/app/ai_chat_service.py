from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from backend.app.ai_client import (
    OpenRouterError,
    request_openrouter_chat,
    resolve_openrouter_api_key,
)
from backend.app.board_service import update_board_for_user
from backend.app.schemas import AIChatRequest, AIChatResponse, AIModelOutputPayload

logger = logging.getLogger(__name__)

_JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", flags=re.DOTALL)

SYSTEM_PROMPT = (
    "You are a project management assistant. "
    "Return only valid JSON matching this schema: "
    '{"assistantReply":"string","board":null|BoardPayload}. '
    "If no board mutation is needed, set board to null."
)


def _extract_json_object(content: str) -> dict:
    candidate = content.strip()
    if not candidate.startswith("{"):
        match = _JSON_BLOCK_PATTERN.search(candidate)
        if not match:
            raise OpenRouterError("Model response did not include JSON.")
        candidate = match.group(0)

    try:
        return json.loads(candidate)
    except json.JSONDecodeError as error:
        logger.error("AI chat JSON parse failure: %s", content)
        raise OpenRouterError("Model response JSON was invalid.") from error


def run_ai_chat_turn(
    db_path: str | Path,
    username: str,
    password: str,
    payload: AIChatRequest,
) -> AIChatResponse:
    api_key = resolve_openrouter_api_key()
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(
        {"role": message.role, "content": message.content}
        for message in payload.conversation
    )
    messages.append(
        {
            "role": "user",
            "content": (
                "Current board JSON:\n"
                f"{payload.board.model_dump_json()}\n\n"
                f"User message:\n{payload.userMessage}"
            ),
        }
    )

    raw_response = request_openrouter_chat(api_key, messages)
    try:
        raw_content = raw_response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        logger.error("AI chat response shape invalid: %s", raw_response)
        raise OpenRouterError("OpenRouter response did not include assistant text.") from error

    if not isinstance(raw_content, str) or not raw_content.strip():
        logger.error("AI chat response content empty: %s", raw_response)
        raise OpenRouterError("OpenRouter response assistant text was empty.")

    structured_payload = _extract_json_object(raw_content)
    try:
        model_output = AIModelOutputPayload.model_validate(structured_payload)
    except Exception as error:
        logger.error("AI chat structured payload validation failed: %s", structured_payload)
        raise OpenRouterError("Model response schema was invalid.") from error

    if model_output.board is None:
        return AIChatResponse(
            reply=model_output.assistantReply,
            mutationApplied=False,
            board=None,
        )

    saved_board = update_board_for_user(
        db_path,
        username,
        password,
        model_output.board,
    )
    return AIChatResponse(
        reply=model_output.assistantReply,
        mutationApplied=True,
        board=saved_board,
    )
