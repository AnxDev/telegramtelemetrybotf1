<div align="center">

# 🏎️ F1 Telemetry Telegram Bot

A Telegram bot that serves **Formula 1 lap-time data** for any driver across race,
qualifying, sprint and practice sessions, powered by [FastF1](https://github.com/theOehrly/Fast-F1).

![Python](https://img.shields.io/badge/python-3.10+-blue)
![FastF1](https://img.shields.io/badge/FastF1-3.8.3-orange)
![Telegram](https://img.shields.io/badge/telegram-bot-26A5E4)
![License](https://img.shields.io/badge/license-MIT-green)
[![CI](https://github.com/AnxDev/telegramtelemetrybotf1/actions/workflows/ci.yml/badge.svg)](https://github.com/AnxDev/telegramtelemetrybotf1/actions)

</div>

## What it does

Send the bot a request and get back:

- 📊 **Lap times** for a single driver in any session, with the tyre *compound* used on every lap
- 🖼️ A **comparison chart** of two drivers' per-lap times rendered as a PNG image

Data is downloaded from the official F1 / FastF1 datasets and becomes available
roughly **1–1.5 hours after a session ends**.

## Features

- Thread-safe background queue — several users can queue requests without blocking the bot
- Tyre compound information alongside every lap time
- On-demand chart generation with `matplotlib` (headless, no display required)
- Optional persistent cache for FastF1 downloads (`F1_CACHE_DIR`) for much faster repeat queries
- Fully configurable through environment variables — **no secrets in the code**
- Unit-tested parsing and formatting logic, linted with Ruff

## Tech stack

| Component   | Technology                                    |
|-------------|-----------------------------------------------|
| Language    | Python 3.10+                                  |
| Bot         | [pyTelegramBotAPI 4.36](https://github.com/eternnoir/pyTelegramBotAPI) |
| F1 data     | [FastF1 3.8](https://github.com/theOehrly/Fast-F1) |
| Charts      | [matplotlib](https://matplotlib.org)          |
| Config      | `python-dotenv` (.env / environment variables)|
| Quality     | pytest + ruff, GitHub Actions CI              |

## Architecture

```
                         ┌─────────────────────────────┐
  Telegram user ──► ──► │          bot.py             │──► config.py (env)
    /lap_times  /compare│   (entry point / polling)   │
                         └─────────────┬───────────────┘
                                       │
                         ┌─────────────▼───────────────┐
                         │       commands.py           │
                         │   Telegram handlers / args  │
                         └─────────────┬───────────────┘
                                       │
                  ┌────────────────────┼────────────────────┐
                  ▼                                         ▼
     ┌────────────────────────┐               ┌────────────────────────┐
     │   queue_manager.py     │               │      f1_service.py     │
     │  background worker per │               │  FastF1 + matplotlib   │
     │  queued lap-time request│               │  (session data / chart)│
     └────────────────────────┘               └────────────────────────┘
```

## Getting started

### Prerequisites

- Python 3.10 or newer
- A Telegram bot token from [@BotFather](https://t.me/BotFather) (`/newbot`)

> ⚠️ **Security**: never commit a real token. If one ever leaks, revoke it
> immediately with `/revoke` in BotFather.

### Installation

```bash
git clone https://github.com/AnxDev/telegramtelemetrybotf1.git
cd telegramtelemetrybotf1

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # Windows: copy .env.example .env
# edit .env and set TELEGRAM_BOT_TOKEN
```

### Run

```bash
python bot.py
```

Enable the optional FastF1 cache in `.env` to avoid re-downloading sessions:

```
F1_CACHE_DIR=~/.cache/fastf1
```

## Usage

| Command | Description | Example |
|---|---|---|
| `/start` | Welcome message | `/start` |
| `/help` | All commands and examples | `/help` |
| `/drivers` | List of all driver codes | `/drivers` |
| `/lap_times <year> <track> <session> <driver>` | Lap times of a driver in a session | `/lap_times 2024 Bahrain R LEC` |
| `/compare <year> <track> <session> <driver1> <driver2>` | Chart comparing two drivers | `/compare 2024 Bahrain R LEC VER` |

**Session codes:** `R` race · `Q` qualifying · `SQ` sprint qualifying · `FP1`/`FP2`/`FP3` practice

**Driver codes** are 3-letter abbreviations (e.g. `LEC`, `VER`, `ALO`, `SAI`) — list them all with `/drivers`.

### Example output

```
LAP TIMES of LEC in Bahrain 2024 (session R):
1. SOFT - 01:33.762
2. SOFT - 01:34.021
3. MEDIUM - 01:34.110
...
```

## Project layout

```
telegramtelemetrybotf1/
├── bot.py              # Entry point: wiring + Telegram polling
├── config.py           # Settings from environment variables
├── commands.py         # Telegram command handlers
├── f1_service.py       # FastF1 queries, chart generation, validation
├── queue_manager.py    # Thread-safe background request queue
├── tests/              # Unit tests (pytest)
├── .env.example        # Template for local configuration
└── .github/workflows/  # CI pipeline (lint + format + tests)
```

## Development

```bash
pip install -r requirements-dev.txt

ruff check .            # lint
ruff format .           # format
pytest -v               # tests
```

The parsing, validation and formatting logic is covered by tests that need
**no network access**, so CI stays fast and reliable.

## Disclaimer

This project is unofficial and not affiliated with Formula 1, FOM, the FIA,
or any of their licensees. All racing data is provided by
[FastF1](https://github.com/theOehrly/Fast-F1).

## License

[MIT](LICENSE)