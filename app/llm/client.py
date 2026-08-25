"""Thin async client for the Claude Messages API (api.anthropic.com/v1/messages).

The API key is read from the environment (ANTHROPIC_API_KEY) - never hardcoded.
To swap providers, implement a client with the same `complete`/`structured`
interface (see README "Swapping the LLM provider").
"""

import json
import logging
import re
from typing import Optional

import httpx

from app.config import get_settings

log = logging.getLogger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when LLM calls are disabled or no API key is configured."""


def strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` fences and trim surrounding prose."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def parse_json_response(text: str) -> dict:
    """Best-effort JSON parsing: strip fences, extract the outermost object,
    fall back to raw json.loads. Raises ValueError on total failure."""
    cleaned = strip_code_fences(text)
    obj = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if obj:
        cleaned = obj.group(0)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        raise ValueError(f"Model did not return valid JSON: {text[:200]!r}")


class ClaudeClient:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()

    @property
    def available(self) -> bool:
        return self.settings.llm_available

    async def complete(self, system: str, user: str, max_tokens: int = 2000) -> str:
        if not self.available:
            raise LLMUnavailableError(
                "LLM disabled or ANTHROPIC_API_KEY not set. Set ENABLE_LLM=1 and "
                "ANTHROPIC_API_KEY in the environment/.env file."
            )
        payload = {
            "model": self.settings.anthropic_model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                self.settings.anthropic_base_url, json=payload, headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def structured(self, system: str, user: str, max_tokens: int = 2000) -> dict:
        """Ask for strict JSON and parse it defensively."""
        text = await self.complete(system, user, max_tokens=max_tokens)
        return parse_json_response(text)


def get_llm_client() -> ClaudeClient:
    return ClaudeClient()