from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


load_dotenv()


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: Literal["openai", "gemini", "demo"] = "demo"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    google_api_key: str | None = None
    gemini_model: str = "gemini-3.6-flash"
    gemini_fallback_models: str = ""

    tavily_api_key: str | None = None
    tavily_max_results: int = Field(default=5, ge=1, le=10)

    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    langchain_project: str = "deepinsight-agent"

    checkpoint_db_path: Path = Path("data/checkpoints/deepinsight.sqlite")

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str | None = None
    mysql_database: str = "deepinsight_agent"
    mysql_enabled: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
