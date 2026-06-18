"""Testes das heurísticas de sinais comportamentais."""

from app.core.signals import (
    SIGNAL_GAZE_AWAY,
    SIGNAL_NOD_NEGATIVE,
    SIGNAL_NOD_POSITIVE,
    SIGNAL_WITHDRAW,
    detect_gaze_away,
    detect_head_gestures,
    detect_signals,
    detect_withdrawal,
)
from app.core.types import FrameMetrics


def _frame(
    ts: int,
    *,
    looking: bool = True,
    size: float = 0.3,
    cx: float = 0.5,
    cy: float = 0.5,
) -> FrameMetrics:
    return FrameMetrics(
        timestamp_ms=ts,
        looking_at_screen=looking,
        face_size_ratio=size,
        face_center_x=cx,
        face_center_y=cy,
    )


def test_gaze_away_emits_event_when_long_enough() -> None:
    frames = [_frame(ts, looking=False) for ts in range(0, 3501, 500)]
    events = detect_gaze_away(frames)
    assert len(events) == 1
    assert events[0].signal_type == SIGNAL_GAZE_AWAY
    assert events[0].meta["duration_seconds"] == 3.5


def test_gaze_away_ignores_short_glances() -> None:
    frames = [_frame(ts, looking=False) for ts in range(0, 2001, 500)]
    assert detect_gaze_away(frames) == []


def test_withdrawal_detects_sudden_drop() -> None:
    frames = [_frame(i * 100, size=0.3) for i in range(5)]
    frames.append(_frame(500, size=0.1))
    events = detect_withdrawal(frames)
    assert len(events) == 1
    assert events[0].signal_type == SIGNAL_WITHDRAW
    assert events[0].timestamp_ms == 500


def test_head_nod_positive() -> None:
    ys = [0.5, 0.42, 0.58, 0.42, 0.58, 0.42]
    frames = [_frame(i * 100, cy=y) for i, y in enumerate(ys)]
    events = detect_head_gestures(frames)
    assert len(events) == 1
    assert events[0].signal_type == SIGNAL_NOD_POSITIVE


def test_head_shake_negative() -> None:
    xs = [0.5, 0.42, 0.58, 0.42, 0.58, 0.42]
    frames = [_frame(i * 100, cx=x) for i, x in enumerate(xs)]
    events = detect_head_gestures(frames)
    assert len(events) == 1
    assert events[0].signal_type == SIGNAL_NOD_NEGATIVE


def test_detect_signals_empty() -> None:
    assert detect_signals([]) == []


def test_detect_signals_sorted() -> None:
    frames = [_frame(i * 100, size=0.3) for i in range(5)]
    frames.append(_frame(500, size=0.1))  # withdrawal em 500
    frames.extend(_frame(600 + ts, looking=False) for ts in range(0, 3501, 500))  # gaze
    events = detect_signals(frames)
    timestamps = [e.timestamp_ms for e in events]
    assert timestamps == sorted(timestamps)
    assert {e.signal_type for e in events} >= {SIGNAL_WITHDRAW, SIGNAL_GAZE_AWAY}
