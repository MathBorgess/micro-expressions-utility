"""Testes do timeline builder e da heurística de resistência."""

from app.core.timeline import build_timeline, has_resistance, signals_in_segment
from app.core.types import Segment, SignalEvent


def _segment(start: int, end: int, text: str, speaker: str = "Cliente") -> Segment:
    return Segment(start_ms=start, end_ms=end, speaker=speaker, text=text)


def test_signals_in_segment_filters_by_interval() -> None:
    seg = _segment(0, 5000, "fala")
    signals = [
        SignalEvent(3000, "olhar_desviado", 0.9),
        SignalEvent(9000, "afastamento_da_tela", 0.8),
    ]
    matched = signals_in_segment(seg, signals)
    assert len(matched) == 1
    assert matched[0].timestamp_ms == 3000


def test_build_timeline_groups_signals() -> None:
    segments = [_segment(0, 5000, "preço alto"), _segment(6000, 10000, "ok", "Vendedor")]
    signals = [SignalEvent(3000, "olhar_desviado", 0.9)]
    timeline = build_timeline(segments, signals)
    assert len(timeline) == 2
    assert len(timeline[0].signals) == 1
    assert timeline[1].signals == []


def test_has_resistance_true_when_keyword_and_disengagement() -> None:
    seg = _segment(0, 5000, "o preço está acima do orçamento")
    signals = [SignalEvent(2000, "olhar_desviado", 0.9)]
    assert has_resistance(seg, signals) is True


def test_has_resistance_false_without_keyword() -> None:
    seg = _segment(0, 5000, "gostei muito da solução")
    signals = [SignalEvent(2000, "olhar_desviado", 0.9)]
    assert has_resistance(seg, signals) is False


def test_has_resistance_false_without_signal() -> None:
    seg = _segment(0, 5000, "falando sobre preço")
    assert has_resistance(seg, []) is False
