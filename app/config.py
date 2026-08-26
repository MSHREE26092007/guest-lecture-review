"""Application settings. All values can be overridden via environment variables
or a .env file (python-dotenv-style loading is handled by pydantic-settings)."""

import os
import tempfile
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

IS_VERCEL = os.getenv("VERCEL") == "1" or "VERCEL" in os.environ


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    # --- LLM (module 4, 5, subjective part of 8) ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_base_url: str = "https://api.anthropic.com/v1/messages"
    enable_llm: bool = True

    # --- Embeddings (module 5) ---
    enable_embeddings: bool = True
    embedding_model: str = "all-mpnet-base-v2"
    semantic_threshold: float = 0.35

    # --- Grammar (module 6) ---
    languagetool_url: str = "https://api.languagetool.org/v2/check"
    languagetool_timeout: float = 30.0

    # --- Paths ---
    config_dir: Path = BASE_DIR / "config"
    upload_dir: Path = Path("/tmp/uploads") if IS_VERCEL else BASE_DIR / "uploads"

    # --- Database ---
    database_url: str = (
        "sqlite:////tmp/guest_lecture_review.db"
        if IS_VERCEL
        else f"sqlite:///{(BASE_DIR / 'guest_lecture_review.db').as_posix()}"
    )

    @property
    def llm_available(self) -> bool:
        return self.enable_llm and bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    try:
        settings.upload_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        tmp_dir = Path(tempfile.gettempdir()) / "uploads"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        settings.upload_dir = tmp_dir
    return settings