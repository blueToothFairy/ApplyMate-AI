from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.config import get_settings
from app.services.json_utils import extract_json

logger = logging.getLogger(__name__)


class LLMProvider:
    """Gemini-backed LLM adapter used by ApplyMate agents.

    Set MOCK_LLM_MODE=false and GOOGLE_API_KEY=<key> in .env to use a real LLM.
    Mock mode remains available for tests and offline demos only.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.settings.google_api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is required when MOCK_LLM_MODE=false. "
                "Add GOOGLE_API_KEY to .env or set MOCK_LLM_MODE=true for offline tests."
            )
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is not installed. Run: pip install -r requirements.txt"
            ) from exc
        self._client = genai.Client(api_key=self.settings.google_api_key)
        return self._client

    async def complete(
        self,
        prompt: str,
        system: str = "",
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        if self.settings.mock_llm_mode:
            return self._mock_text_response(prompt, system)

        client = self._get_client()
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system or None,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
            )
            response = await client.aio.models.generate_content(
                model=self.settings.llm_model,
                contents=prompt,
                config=config,
            )
        except Exception:
            logger.exception("LLM text generation failed")
            raise
        return getattr(response, "text", "") or ""

    async def complete_json(
        self,
        prompt: str,
        system: str = "",
        *,
        temperature: float = 0.15,
        max_output_tokens: int = 4096,
    ) -> Any:
        if self.settings.mock_llm_mode:
            return self._mock_json_response(prompt, system)

        client = self._get_client()
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                system_instruction=system or None,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
            )
            response = await client.aio.models.generate_content(
                model=self.settings.llm_model,
                contents=prompt,
                config=config,
            )
        except Exception:
            logger.exception("LLM JSON generation failed")
            raise
        return extract_json(getattr(response, "text", "") or "")

    def _mock_text_response(self, prompt: str, system: str = "") -> str:
        return "Mock LLM response. Set MOCK_LLM_MODE=false and GOOGLE_API_KEY to use Gemini."

    def _mock_json_response(self, prompt: str, system: str = "") -> Any:
        # Minimal generic JSON for offline tests. Agent-specific code usually falls back
        # to rule-based post-processing when mock mode is enabled.
        return {"mock": True, "notes": ["MOCK_LLM_MODE is enabled."]}


llm_provider = LLMProvider()
