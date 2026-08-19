"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def _get_bool(name: str, default: bool = False) -> bool:
    """Read a boolean value from the environment."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Runtime settings for the bot, read once at import time.

    A ``.env`` file in the project root is loaded automatically, but
    explicit environment variables always take precedence over it.
    """

    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    F1_CACHE_DIR: str = os.getenv("F1_CACHE_DIR", "").strip()
    POLLING_TIMEOUT: int = int(os.getenv("POLLING_TIMEOUT", "20"))
    LONG_POLLING: bool = _get_bool("LONG_POLLING", True)
    DEBUG: bool = _get_bool("DEBUG", False)


settings = Settings()
