from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ApplyMate AI Server"
    app_env: str = "development"
    ai_server_port: int = 8010
    temp_file_dir: str = ".tmp"

    # Real LLM mode is the default for the application. Set MOCK_LLM_MODE=true only
    # for offline tests or deterministic demos.
    mock_llm_mode: bool = False
    google_api_key: str | None = None
    llm_model: str = "gemini-2.0-flash"
    enable_mcp_server: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
