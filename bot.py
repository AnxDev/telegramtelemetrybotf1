"""Entry point for the Formula 1 telemetry Telegram bot.

Run it with::

    python bot.py

A valid Telegram bot token has to be available, either through the
``TELEGRAM_BOT_TOKEN`` environment variable or via a ``.env`` file.
"""

from __future__ import annotations

import logging
import sys

import matplotlib

matplotlib.use("Agg")  # headless backend: the bot runs without a display.

import fastf1  # must come after matplotlib backend selection
import telebot

import config
import f1_service
from commands import BotHandlers
from queue_manager import TelemetryQueue

logging.basicConfig(
    level=logging.DEBUG if config.settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Wire the bot together and start polling for updates."""
    if not config.settings.TELEGRAM_BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Create a .env file (see .env.example) or set the environment variable."
        )
        sys.exit(1)

    if config.settings.F1_CACHE_DIR:
        fastf1.Cache.enable_cache(config.settings.F1_CACHE_DIR)
        logger.info("FastF1 cache enabled at %s", config.settings.F1_CACHE_DIR)

    bot = telebot.TeleBot(config.settings.TELEGRAM_BOT_TOKEN)
    service = f1_service.F1Service()
    queue = TelemetryQueue()

    BotHandlers(bot=bot, service=service, queue=queue)
    queue.start(bot, service)

    logger.info("Bot is polling for updates...")
    bot.infinity_polling(timeout=config.settings.POLLING_TIMEOUT)


if __name__ == "__main__":
    main()
