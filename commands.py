"""Telegram command handlers for the F1 lap-time bot."""

from __future__ import annotations

import logging
from pathlib import Path
from tempfile import gettempdir

import telebot
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import f1_service
from queue_manager import TelemetryQueue, TelemetryTask

logger = logging.getLogger(__name__)

CLOSE_CALLBACK = "close"


def close_button() -> InlineKeyboardMarkup:
    """Return a keyboard with a single button that deletes the message."""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("Close", callback_data=CLOSE_CALLBACK))
    return markup


class BotHandlers:
    """Registers and implements every Telegram command the bot understands."""

    def __init__(
        self,
        bot: telebot.TeleBot,
        service: f1_service.F1Service,
        queue: TelemetryQueue,
    ) -> None:
        self._bot = bot
        self._service = service
        self._queue = queue
        self._register()

    def _register(self) -> None:
        self._bot.message_handler(commands=["start"])(self.on_start)
        self._bot.message_handler(commands=["help"])(self.on_help)
        self._bot.message_handler(commands=["drivers"])(self.on_drivers)
        self._bot.message_handler(commands=["lap_times"])(self.on_lap_times)
        self._bot.message_handler(commands=["compare"])(self.on_compare)
        self._bot.callback_query_handler(func=lambda call: True)(self.on_callback)

    def on_start(self, message: Message) -> None:
        """Welcome message shown when a user starts the bot."""
        self._bot.send_message(
            message.chat.id,
            "Hi! I send lap times for every Formula 1 session of a chosen driver.\n"
            "Data becomes available roughly 1-1.5 hours after a session ends.\n"
            "\n"
            "Type /help to see what I can do.",
        )

    def on_help(self, message: Message) -> None:
        """Print the list of available commands with examples."""
        text = (
            "AVAILABLE COMMANDS\n"
            "\n"
            "/drivers\n"
            "  Lists all known driver codes.\n"
            "\n"
            "/lap_times <year> <track> <session> <driver>\n"
            "  Returns the lap times (with tyre compound) of a driver.\n"
            "  Sessions: R, Q, SQ, FP1, FP2, FP3.\n"
            "\n"
            "/compare <year> <track> <session> <driver1> <driver2>\n"
            "  Generates a chart comparing lap times of two drivers.\n"
            "\n"
            "EXAMPLES\n"
            "/lap_times 2024 Bahrain R LEC\n"
            "/compare 2024 Bahrain R LEC VER"
        )
        self._bot.send_message(message.chat.id, text)

    def on_drivers(self, message: Message) -> None:
        """Print every known driver code together with the full name."""
        lines = [f"{code}  {name}" for code, name in sorted(f1_service.DRIVERS.items())]
        self._bot.send_message(message.chat.id, "DRIVER CODES:\n" + "\n".join(lines))

    def on_lap_times(self, message: Message) -> None:
        """Queue a lap-time request and run it later in the background worker."""
        try:
            year, track, session_type, driver = f1_service.parse_session_args(
                message.text
            )
        except (f1_service.ValidationError, ValueError) as exc:
            self._bot.reply_to(message, str(exc))
            return

        confirmation = self._bot.reply_to(
            message,
            f"Queued for {driver} in {track} {year} (session {session_type}). "
            "I'll process it shortly...",
        )
        task = TelemetryTask(
            year=year,
            track=track,
            session_type=session_type,
            driver=driver,
            chat_id=message.chat.id,
            status_message_id=confirmation.message_id,
        )
        self._queue.enqueue(task)

    def on_compare(self, message: Message) -> None:
        """Generate and send a lap-time comparison chart for two drivers."""
        try:
            year, track, session_type, driver1, driver2 = f1_service.parse_compare_args(
                message.text
            )
        except (f1_service.ValidationError, ValueError) as exc:
            self._bot.reply_to(message, str(exc))
            return

        status = self._bot.reply_to(message, "Loading session, please wait...")
        output_dir = Path(gettempdir()) / "f1-bot-charts"
        try:
            chart_path = self._service.generate_comparison_chart(
                year=year,
                track=track,
                session_type=session_type,
                driver1=driver1,
                driver2=driver2,
                output_dir=output_dir,
            )
            with chart_path.open("rb") as image:
                self._bot.send_photo(
                    message.chat.id,
                    image,
                    caption=f"{track} {year} | {driver1} vs {driver2} | session {session_type}",
                    reply_markup=close_button(),
                )
            chart_path.unlink(missing_ok=True)
        except Exception:
            logger.exception("Failed to generate comparison chart")
            self._bot.reply_to(
                message,
                "I couldn't load that session. "
                "Please double-check the parameters and try again.",
            )
        finally:
            self._bot.delete_message(message.chat.id, status.message_id)

    def on_callback(self, callback: CallbackQuery) -> None:
        """Handle 'Close' button presses by deleting the message."""
        if callback.data == CLOSE_CALLBACK and callback.message:
            self._bot.delete_message(callback.message.chat.id, callback.message.id)
