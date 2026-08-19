"""Unit tests for the pure parsing/formatting helpers in ``f1_service``."""

from __future__ import annotations

import pytest

from f1_service import (
    ValidationError,
    build_lap_table,
    is_valid_session_type,
    lap_time_to_text,
    normalize_driver_code,
    parse_compare_args,
    parse_session_args,
)


class TestValidation:
    def test_allows_all_session_types(self) -> None:
        for code in ("R", "Q", "SQ", "FP1", "FP2", "FP3", "r", "q"):
            assert is_valid_session_type(code) is True

    def test_rejects_unknown_session_type(self) -> None:
        assert is_valid_session_type("W") is False
        assert is_valid_session_type("race") is False

    def test_normalize_driver_code_uppercases(self) -> None:
        assert normalize_driver_code("lec") == "LEC"

    def test_normalize_driver_code_rejects_unknown(self) -> None:
        with pytest.raises(ValidationError):
            normalize_driver_code("XYZ")


class TestParseSessionArgs:
    def test_valid_command(self) -> None:
        assert parse_session_args("/lap_times 2024 Bahrain R LEC") == (
            2024,
            "Bahrain",
            "R",
            "LEC",
        )

    def test_accepts_lowercase_driver(self) -> None:
        assert parse_session_args("/lap_times 2024 Bahrain R lec")[3] == "LEC"

    def test_rejects_too_few_arguments(self) -> None:
        with pytest.raises(ValidationError):
            parse_session_args("/lap_times 2024 Bahrain")

    def test_rejects_invalid_year(self) -> None:
        with pytest.raises(ValueError):
            parse_session_args("/lap_times not-a-year Bahrain R LEC")

    def test_rejects_unknown_driver(self) -> None:
        with pytest.raises(ValidationError):
            parse_session_args("/lap_times 2024 Bahrain R XYZ")


class TestParseCompareArgs:
    def test_valid_command(self) -> None:
        assert parse_compare_args("/compare 2024 Bahrain R LEC VER") == (
            2024,
            "Bahrain",
            "R",
            "LEC",
            "VER",
        )

    def test_rejects_same_driver_twice(self) -> None:
        with pytest.raises(ValidationError):
            parse_compare_args("/compare 2024 Bahrain R LEC LEC")

    def test_rejects_too_few_arguments(self) -> None:
        with pytest.raises(ValidationError):
            parse_compare_args("/compare 2024 Bahrain R LEC")


class TestFormatting:
    def test_lap_time_drops_prefix(self) -> None:
        assert lap_time_to_text("0 days 00:01:32.456") == "01:32.456"

    def test_build_lap_table_empty(self) -> None:
        assert build_lap_table([], []) == ""

    def test_build_lap_table_zips_compound_and_time(self) -> None:
        table = build_lap_table(
            ["0 days 00:01:32.456", "0 days 00:01:33.100"],
            ["SOFT", "MEDIUM"],
        )
        assert table == "1. SOFT - 01:32.456\n2. MEDIUM - 01:33.100"
