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
        self.logical_call_count = 0
        self.retry_attempt_count = 0

    def reset_call_counter(self) -> None:
        self.logical_call_count = 0
        self.retry_attempt_count = 0

    def get_call_count(self) -> int:
        return self.logical_call_count

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

    def _is_retriable(self, exc: Exception) -> bool:
        try:
            from google.genai.errors import APIError
            if isinstance(exc, APIError):
                # Retry on 429 (Rate limit) or 5xx server errors
                return exc.code == 429 or (500 <= exc.code < 600)
        except ImportError:
            pass

        import httpx
        if isinstance(exc, (httpx.HTTPError, ConnectionError, TimeoutError)):
            return True

        return False

    async def _execute_with_retry(self, func, retry_context: dict | None = None, *args, **kwargs):
        max_retries = self.settings.llm_max_retries
        initial_delay = self.settings.llm_initial_delay
        backoff_factor = self.settings.llm_backoff_factor
        max_delay = self.settings.llm_max_delay

        attempts = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                if not self._is_retriable(exc):
                    raise

                attempts += 1
                self.retry_attempt_count += 1
                if retry_context is not None:
                    retry_context["attempts"] = attempts

                if attempts > max_retries:
                    logger.error(
                        f"LLM API call failed after {max_retries} retries. Final error: {exc.__class__.__name__}: {exc}"
                    )
                    raise

                delay = min(max_delay, initial_delay * (backoff_factor ** (attempts - 1)))
                import random
                delay_with_jitter = delay + random.uniform(0, 1)

                logger.warning(
                    f"LLM API call failed with {exc.__class__.__name__}: {exc}. "
                    f"Retrying in {delay_with_jitter:.2f} seconds... (Attempt {attempts}/{max_retries})"
                )
                await asyncio.sleep(delay_with_jitter)

    async def complete(
        self,
        prompt: str,
        system: str = "",
        *,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
        agent_name: str = "UnknownAgent",
    ) -> str:
        self.logical_call_count += 1

        import time
        import datetime
        start_time = time.perf_counter()
        start_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        logger.info(
            f"[LLM CALL START] agent_name={agent_name} | model={self.settings.llm_model} | "
            f"mock_llm_mode={self.settings.mock_llm_mode} | timestamp={start_timestamp}"
        )

        if self.settings.mock_llm_mode:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"[LLM CALL COMPLETE] agent_name={agent_name} | model={self.settings.llm_model} | "
                f"mock_llm_mode=True | duration_ms={duration_ms:.2f} | retry_attempts=0"
            )
            return self._mock_text_response(prompt, system)

        client = self._get_client()
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        async def _call():
            return await client.aio.models.generate_content(
                model=self.settings.llm_model,
                contents=prompt,
                config=config,
            )

        retry_context = {"attempts": 0}
        try:
            response = await self._execute_with_retry(_call, retry_context)
            text = getattr(response, "text", "") or ""
        except Exception:
            logger.exception("LLM text generation failed")
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            attempts = retry_context["attempts"]
            logger.info(
                f"[LLM CALL COMPLETE] agent_name={agent_name} | model={self.settings.llm_model} | "
                f"mock_llm_mode=False | duration_ms={duration_ms:.2f} | retry_attempts={attempts}"
            )
        return text

    async def complete_json(
        self,
        prompt: str,
        system: str = "",
        *,
        temperature: float = 0.15,
        max_output_tokens: int | None = None,
        agent_name: str = "UnknownAgent",
    ) -> Any:
        self.logical_call_count += 1

        import time
        import datetime
        start_time = time.perf_counter()
        start_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        logger.info(
            f"[LLM CALL START] agent_name={agent_name} | model={self.settings.llm_model} | "
            f"mock_llm_mode={self.settings.mock_llm_mode} | timestamp={start_timestamp}"
        )

        if self.settings.mock_llm_mode:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"[LLM CALL COMPLETE] agent_name={agent_name} | model={self.settings.llm_model} | "
                f"mock_llm_mode=True | duration_ms={duration_ms:.2f} | retry_attempts=0"
            )
            return self._mock_json_response(prompt, system)

        client = self._get_client()
        from google.genai import types
        config = types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
        )

        async def _call():
            return await client.aio.models.generate_content(
                model=self.settings.llm_model,
                contents=prompt,
                config=config,
            )

        retry_context = {"attempts": 0}
        try:
            response = await self._execute_with_retry(_call, retry_context)
            raw_text = getattr(response, "text", "") or ""
            return extract_json(raw_text)
        except Exception as exc:
            raw_text = locals().get("raw_text", "")
            logger.error(f"LLM JSON generation or parsing failed. Raw response snippet: {raw_text[:1000]}")
            raise
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000
            attempts = retry_context["attempts"]
            logger.info(
                f"[LLM CALL COMPLETE] agent_name={agent_name} | model={self.settings.llm_model} | "
                f"mock_llm_mode=False | duration_ms={duration_ms:.2f} | retry_attempts={attempts}"
            )

    def _mock_text_response(self, prompt: str, system: str = "") -> str:
        return "Mock LLM response. Set MOCK_LLM_MODE=false and GOOGLE_API_KEY to use Gemini."

    def _mock_json_response(self, prompt: str, system: str = "") -> Any:
        return {"mock": True, "notes": ["MOCK_LLM_MODE is enabled."]}


llm_provider = LLMProvider()
