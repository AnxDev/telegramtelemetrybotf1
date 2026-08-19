"""Business logic built on top of FastF1 to read Formula 1 telemetry data.

This module keeps the FastF1 / data-collection concerns isolated so that
the Telegram handlers stay thin and (pure) parsing/formatting helpers can be
unit-tested without any network access.
"""

from __future__ import annotations

from pathlib import Path

import fastf1
import matplotlib.pyplot as plt
from fastf1.plotting import setup_mpl

ALLOWED_SESSION_TYPES = frozenset({"R", "Q", "SQ", "FP1", "FP2", "FP3"})

SESSION_TYPE_NAMES = {
    "R": "Race",
    "Q": "Qualifying",
    "SQ": "Sprint Qualifying",
    "FP1": "Free Practice 1",
    "FP2": "Free Practice 2",
    "FP3": "Free Practice 3",
}

DRIVERS: dict[str, str] = {
    "ALB": "Alexander Albon",
    "ALO": "Fernando Alonso",
    "BEA": "Oliver Bearman",
    "BOT": "Valtteri Bottas",
    "DEV": "Nyck de Vries",
    "GAS": "Pierre Gasly",
    "HAM": "Lewis Hamilton",
    "HUL": "Nico Hülkenberg",
    "LAT": "Nicholas Latifi",
    "LAW": "Liam Lawson",
    "LEC": "Charles Leclerc",
    "MAG": "Kevin Magnussen",
    "NOR": "Lando Norris",
    "OCO": "Esteban Ocon",
    "PER": "Sergio Pérez",
    "PIA": "Oscar Piastri",
    "RIC": "Daniel Ricciardo",
    "RUS": "George Russell",
    "SAI": "Carlos Sainz Jr.",
    "SAR": "Logan Sargeant",
    "SCH": "Mick Schumacher",
    "STR": "Lance Stroll",
    "TSU": "Yuki Tsunoda",
    "VER": "Max Verstappen",
    "ZHO": "Zhou Guanyu",
}


class NoDataError(Exception):
    """Raised when a session is fetched but contains no usable lap times."""


class ValidationError(ValueError):
    """Raised when a command payload is malformed or refers to unknown data."""


def is_valid_session_type(session_type: str) -> bool:
    """Return ``True`` when the session type is one of the supported codes."""
    return session_type.upper() in ALLOWED_SESSION_TYPES


def normalize_driver_code(code: str) -> str:
    """Return the uppercased driver code, raising if it is not a known one."""
    normalized = code.upper()
    if normalized not in DRIVERS:
        raise ValidationError(
            f"Unknown driver '{code}'. Use /drivers to see all available codes."
        )
    return normalized


def _require_args(args: list[str], count: int, usage: str) -> None:
    if len(args) != count:
        raise ValidationError(
            f"Wrong number of arguments: expected {count - 1}, got {len(args) - 1}.\n\n{usage}"
        )


def parse_session_args(text: str) -> tuple[int, str, str, str]:
    """Parse ``/lap-times <year> <track> <session> <driver>`` into a tuple."""
    usage = (
        "Usage: /lap_times <year> <track> <session> <driver>\n"
        "Example: /lap_times 2024 Bahrain R LEC\n"
        "Allowed sessions: R, Q, SQ, FP1, FP2, FP3."
    )
    args = text.split()
    _require_args(args, 5, usage)

    year = int(args[1])
    track = args[2]
    session_type = args[3].upper()
    driver = normalize_driver_code(args[4])

    if not is_valid_session_type(session_type):
        raise ValidationError(
            f"Invalid session type '{args[3]}'. Allowed: {', '.join(sorted(ALLOWED_SESSION_TYPES))}."
        )
    return year, track, session_type, driver


def parse_compare_args(text: str) -> tuple[int, str, str, str, str]:
    """Parse ``/compare <year> <track> <session> <driver1> <driver2>`` into a tuple."""
    usage = (
        "Usage: /compare <year> <track> <session> <driver1> <driver2>\n"
        "Example: /compare 2024 Bahrain R LEC VER\n"
        "Allowed sessions: R, Q, SQ, FP1, FP2, FP3."
    )
    args = text.split()
    _require_args(args, 6, usage)

    year = int(args[1])
    track = args[2]
    session_type = args[3].upper()
    driver1 = normalize_driver_code(args[4])
    driver2 = normalize_driver_code(args[5])

    if not is_valid_session_type(session_type):
        raise ValidationError(
            f"Invalid session type '{args[3]}'. Allowed: {', '.join(sorted(ALLOWED_SESSION_TYPES))}."
        )
    if driver1 == driver2:
        raise ValidationError(
            "You compared a driver with themselves. Pick two different drivers."
        )
    return year, track, session_type, driver1, driver2


def lap_time_to_text(lap_time: str) -> str:
    """Format a lap time, dropping FastF1's ``0 days 00:`` prefix."""
    return str(lap_time).replace("0 days 00:", "")


def lap_times_to_seconds(lap_times: list[object]) -> list[float]:
    """Convert FastF1 lap times (``datetime.timedelta``) into plain seconds.

    Non-timed entries (``NaN``/``NaT``) are skipped, so the returned list
    only contains real, plottable values.
    """
    seconds = []
    for value in lap_times:
        if not hasattr(value, "total_seconds"):
            continue
        seconds.append(float(value.total_seconds()))
    return seconds


def build_lap_table(lap_times: list[str], compounds: list[str]) -> str:
    """Combine compounds and lap times into a single readable block of text."""
    if not lap_times:
        return ""
    lines = [
        f"{index}. {compound} - {lap_time_to_text(time)}"
        for index, (compound, time) in enumerate(zip(compounds, lap_times), start=1)
    ]
    return "\n".join(lines)


class F1Service:
    """Thin wrapper around FastF1 for fetching sessions, lap times and charts."""

    @staticmethod
    def _load_laps(year: int, track: str, session_type: str) -> object:
        """Load and return the FastF1 laps container for a session."""
        session = fastf1.get_session(year, track, session_type)
        session.load(laps=True, telemetry=False)
        return session.laps

    def get_lap_table(
        self, year: int, track: str, session_type: str, driver: str
    ) -> str:
        """Return a formatted lap-time table (with tyre compound) for a driver."""
        laps = self._load_laps(year, track, session_type).pick_drivers(driver)
        lap_times = [str(value) for value in laps["LapTime"]]
        compounds = [str(value) for value in laps["Compound"]]
        return build_lap_table(lap_times, compounds)

    def generate_comparison_chart(
        self,
        year: int,
        track: str,
        session_type: str,
        driver1: str,
        driver2: str,
        output_dir: Path,
    ) -> Path:
        """Plot per-lap times of two drivers (in seconds) into a PNG file.

        The figure is created explicitly per call (``fig, ax``) so that
        concurrent bot threads never share matplotlib's global state, which
        could otherwise produce blank or mis-scaled charts.
        """
        laps = self._load_laps(year, track, session_type)
        laps1 = laps.pick_drivers(driver1)
        laps2 = laps.pick_drivers(driver2)

        times1 = lap_times_to_seconds(laps1["LapTime"]) if not laps1.empty else []
        times2 = lap_times_to_seconds(laps2["LapTime"]) if not laps2.empty else []
        if not times1 or not times2:
            raise NoDataError(
                f"No lap data found for {driver1} / {driver2} "
                f"in {track} {year} (session {session_type})."
            )

        setup_mpl(color_scheme="fastf1")
        fig, ax = plt.subplots()
        ax.plot(range(1, len(times1) + 1), times1, label=driver1)
        ax.plot(range(1, len(times2) + 1), times2, label=driver2)
        ax.set_title(
            f"{track} {year} | {driver1} vs {driver2} | "
            f"{SESSION_TYPE_NAMES.get(session_type, session_type)}"
        )
        ax.set_xlabel("Lap")
        ax.set_ylabel("Lap time (s)")
        ax.legend(loc="upper right")
        fig.tight_layout()

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{year}{track}{session_type}{driver1}{driver2}.png"
        fig.savefig(output_path)
        plt.close(fig)
        return output_path
