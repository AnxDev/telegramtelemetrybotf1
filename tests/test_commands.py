"""Basic smoke tests for the command handler layer (no network required)."""

from __future__ import annotations

from types import SimpleNamespace

from commands import BotHandlers, close_button


class _FakeBot:
    """Minimal stand-in for telebot used to exercise handler logic."""

    def __init__(self) -> None:
        self.sent = []

    def reply_to(self, message, text):  # type: ignore[no-untyped-def]
        self.sent.append(text)
        return SimpleNamespace(message_id=0)

    def send_message(self, chat_id, text):  # type: ignore[no-untyped-def]
        self.sent.append(text)

    @staticmethod
    def message_handler(**_):  # type: ignore[no-untyped-def]
        """Fake telebot registration decorator that returns the function."""

        def inner(function):  # type: ignore[no-untyped-def]
            return function

        return inner

    callback_query_handler = message_handler


class _FakeQueue:
    def __init__(self) -> None:
        self.tasks = []

    def enqueue(self, task: object) -> int:
        self.tasks.append(task)
        return len(self.tasks)


class _FakeMessage:
    def __init__(self, text: str) -> None:
        self.text = text
        self.chat = SimpleNamespace(id=1)


def test_close_button_has_callback() -> None:
    markup = close_button()
    button = markup.keyboard[0][0]
    assert button.callback_data == "close"


def test_handlers_reject_bad_lap_times_command() -> None:
    bot = _FakeBot()
    handlers = BotHandlers(bot=bot, service=None, queue=None)  # type: ignore[arg-type]
    handlers.on_lap_times(_FakeMessage("/lap_times 2024 Bahrain"))
    assert bot.sent and "Usage: /lap_times" in bot.sent[0]


def test_handlers_reject_unknown_driver() -> None:
    bot = _FakeBot()
    handlers = BotHandlers(bot=bot, service=None, queue=None)  # type: ignore[arg-type]
    handlers.on_lap_times(_FakeMessage("/lap_times 2024 Bahrain R XXX"))
    assert "Unknown driver" in bot.sent[0]


def test_valid_lap_times_command_is_queued() -> None:
    bot = _FakeBot()
    queue = _FakeQueue()
    handlers = BotHandlers(bot=bot, service=None, queue=queue)  # type: ignore[arg-type]
    handlers.on_lap_times(_FakeMessage("/lap_times 2024 Bahrain R LEC"))
    assert len(queue.tasks) == 1
    task = queue.tasks[0]
    assert task.year == 2024
    assert task.driver == "LEC"
