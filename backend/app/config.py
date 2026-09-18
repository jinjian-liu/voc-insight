from functools import lru_cache
import os
from pathlib import Path
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


def default_database_url() -> str:
    if getattr(sys, "frozen", False):
        local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home()))
        data_dir = local_app_data / "VoCInsight"
    else:
        data_dir = BASE_DIR / "data"
    return f"sqlite:///{(data_dir / 'voc.db').as_posix()}"


class Settings(BaseSettings):
    app_name: str = "VoC API"
    database_url: str = default_database_url()
    frontend_origin: str = "http://localhost:5173"
    session_idle_hours: int = 8
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-flash"
    ai_timeout_seconds: int = 60
    ai_max_retries: int = 2
    ai_concurrency: int = 3

    model_config = SettingsConfigDict(env_prefix="VOC_")


@lru_cache
def get_settings() -> Settings:
    return Settings()
