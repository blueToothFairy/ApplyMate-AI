import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from google.genai.errors import APIError
from app.services.llm_provider import LLMProvider
from app.config import Settings


@pytest.mark.asyncio
async def test_llm_provider_retry_success():
    # Test when first calls fail with a retriable error, and subsequent succeeds
    provider = LLMProvider()
    provider.settings = Settings(
        mock_llm_mode=False,
        google_api_key="test-key",
        llm_max_retries=3,
        llm_initial_delay=0.01,
        llm_backoff_factor=2.0,
        llm_max_delay=1.0
    )

    # Mock Client and generation
    mock_client = MagicMock()
    mock_generate = AsyncMock()

    # Prepare side effect: raise APIError, then succeed
    api_error_429 = APIError(
        code=429,
        response_json={
            "error": {
                "code": 429,
                "message": "Rate limit exceeded",
                "status": "RESOURCE_EXHAUSTED",
            }
        },
    )
    mock_response = MagicMock()
    mock_response.text = "Success response"

    mock_generate.side_effect = [api_error_429, api_error_429, mock_response]
    mock_client.aio.models.generate_content = mock_generate

    with patch.object(provider, "_get_client", return_value=mock_client):
        res = await provider.complete("hello")
        assert res == "Success response"
        assert mock_generate.call_count == 3


@pytest.mark.asyncio
async def test_llm_provider_retry_exhausted():
    # Test when all retries fail with a retriable error
    provider = LLMProvider()
    provider.settings = Settings(
        mock_llm_mode=False,
        google_api_key="test-key",
        llm_max_retries=2,
        llm_initial_delay=0.01,
        llm_backoff_factor=2.0,
        llm_max_delay=1.0
    )

    mock_client = MagicMock()
    mock_generate = AsyncMock()

    api_error_503 = APIError(
        code=503,
        response_json={
            "error": {
                "code": 503,
                "message": "Service unavailable",
                "status": "UNAVAILABLE",
            }
        },
    )
    mock_generate.side_effect = api_error_503
    mock_client.aio.models.generate_content = mock_generate

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(APIError) as exc_info:
            await provider.complete("hello")
        assert exc_info.value.code == 503
        assert mock_generate.call_count == 3  # 1 initial attempt + 2 retries


@pytest.mark.asyncio
async def test_llm_provider_no_retry_on_bad_request():
    # Test that non-retriable errors (like 400 ClientError) fail immediately
    provider = LLMProvider()
    provider.settings = Settings(
        mock_llm_mode=False,
        google_api_key="test-key",
        llm_max_retries=3,
        llm_initial_delay=0.01,
        llm_backoff_factor=2.0,
        llm_max_delay=1.0
    )

    mock_client = MagicMock()
    mock_generate = AsyncMock()

    api_error_400 = APIError(
        code=400,
        response_json={
            "error": {
                "code": 400,
                "message": "Bad request",
                "status": "INVALID_ARGUMENT",
            }
        },
    )
    mock_generate.side_effect = api_error_400
    mock_client.aio.models.generate_content = mock_generate

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(APIError) as exc_info:
            await provider.complete("hello")
        assert exc_info.value.code == 400
        assert mock_generate.call_count == 1  # No retries for 400
