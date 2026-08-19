"""Thread-safe FIFO queue that processes telemetry requests in the background."""

from __future__ import annotations

import logging
import queue
import threading
from dataclasses import dataclass

import telebot

import f1_service

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelemetryTask:
    """A lap-time request waiting to be processed by the background worker."""

    year: int
    track: str
    session_type: str
    driver: str
    chat_id: int
    status_message_id: int


class TelemetryQueue:
    """A FIFO queue whose sole worker processes all requests sequentially.

    FastF1 sessions are expensive to download; running them one at a time
    keeps the bot responsive and avoids hammering the data providers.
    """

    def __init__(self) -> None:
        self._tasks: queue.Queue[TelemetryTask] = queue.Queue()

    def enqueue(self, task: TelemetryTask) -> int:
        """Add a task to the queue and return its position (1-based)."""
        self._tasks.put(task)
        return self._tasks.qsize()

    def start(self, bot: telebot.TeleBot, service: f1_service.F1Service) -> None:
        """Start the background worker thread."""
        worker = threading.Thread(
            target=self._worker,
            args=(bot, service),
            name="telemetry-queue",
            daemon=True,
        )
        worker.start()
        logger.info("Telemetry queue worker started")

    def _worker(self, bot: telebot.TeleBot, service: f1_service.F1Service) -> None:
        while True:
            task = self._tasks.get()
            try:
                self._process(bot, service, task)
            except f1_service.NoDataError:
                bot.send_message(
                    task.chat_id,
                    "No lap times found for that session yet. "
                    "Data usually appears 1-1.5 hours after the session ends.",
                )
            except Exception:
                logger.exception("Failed to process task %s", task)
                bot.send_message(
                    task.chat_id,
                    "I couldn't load that session. "
                    "Please double-check the parameters and try again.",
                )
            finally:
                self._tasks.task_done()

    @staticmethod
    def _process(
        bot: telebot.TeleBot, service: f1_service.F1Service, task: TelemetryTask
    ) -> None:
        bot.edit_message_text(
            chat_id=task.chat_id,
            message_id=task.status_message_id,
            text="Loading session, please wait...",
        )

        table = service.get_lap_table(
            task.year, task.track, task.session_type, task.driver
        )
        if not table.strip():
            raise f1_service.NoDataError(task)

        bot.delete_message(task.chat_id, task.status_message_id)
        header = (
            f"LAP TIMES of {task.driver} in {task.track} {task.year} "
            f"(session {task.session_type}):\n"
        )
        bot.send_message(task.chat_id, header + table)
