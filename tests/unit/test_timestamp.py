"""Testes da conversão de tempo (frame ↔ ms ↔ HH:MM:SS)."""

import pytest

from app.core.timestamp import frame_to_ms, ms_to_timestamp


def test_frame_to_ms_basic() -> None:
    assert frame_to_ms(24, 24) == 1000.0
    assert frame_to_ms(0, 30) == 0.0
    assert frame_to_ms(36, 24) == 1500.0


def test_frame_to_ms_invalid_fps() -> None:
    with pytest.raises(ValueError):
        frame_to_ms(10, 0)


def test_frame_to_ms_negative_frame() -> None:
    with pytest.raises(ValueError):
        frame_to_ms(-1, 24)


def test_ms_to_timestamp() -> None:
    assert ms_to_timestamp(0) == "00:00:00"
    assert ms_to_timestamp(312000) == "00:05:12"
    assert ms_to_timestamp(3661000) == "01:01:01"


def test_ms_to_timestamp_negative() -> None:
    with pytest.raises(ValueError):
        ms_to_timestamp(-1)
