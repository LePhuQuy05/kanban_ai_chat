from __future__ import annotations

import json
import logging
import os
from urllib import error, request

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "openai/gpt-oss-120b/free"
CONNECTIVITY_PROMPT = "What is 2+2? Reply with just the number."


class OpenRouterError(RuntimeError):
    pass


def request_openrouter_chat(api_key: str, messages: list[dict[str, str]]) -> dict:
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
    }
    body = json.dumps(payload).encode("utf-8")
    http_request = request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(http_request, timeout=30) as response:
            raw_body = response.read().decode("utf-8")
            return json.loads(raw_body)
    except error.HTTPError as http_error:
        error_body = http_error.read().decode("utf-8", errors="replace")
        logger.error("OpenRouter HTTP error: status=%s body=%s", http_error.code, error_body)
        raise OpenRouterError("OpenRouter HTTP request failed.") from http_error
    except error.URLError as url_error:
        logger.error("OpenRouter network error: %s", url_error.reason)
        raise OpenRouterError("OpenRouter network request failed.") from url_error
    except json.JSONDecodeError as json_error:
        logger.error("OpenRouter JSON decode error: %s", str(json_error))
        raise OpenRouterError("OpenRouter returned invalid JSON.") from json_error


def request_openrouter_completion(api_key: str, prompt: str) -> dict:
    return request_openrouter_chat(
        api_key,
        [{"role": "user", "content": prompt}],
    )


def run_ai_connectivity_check(api_key: str | None = None) -> str:
    resolved_api_key = api_key or os.getenv("OPENROUTER_API_KEY")
    if not resolved_api_key:
        logger.error("OPENROUTER_API_KEY is not set.")
        raise OpenRouterError("Missing OPENROUTER_API_KEY.")

    payload = request_openrouter_completion(resolved_api_key, CONNECTIVITY_PROMPT)
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as parse_error:
        logger.error("OpenRouter response shape error: %s", payload)
        raise OpenRouterError("OpenRouter response did not include assistant text.") from parse_error

    if not isinstance(content, str) or not content.strip():
        logger.error("OpenRouter response content is empty or invalid: %s", payload)
        raise OpenRouterError("OpenRouter response assistant text was empty.")

    return content.strip()
