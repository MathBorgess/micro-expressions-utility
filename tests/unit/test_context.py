"""Testes do orçamento de contexto e da sumarização hierárquica."""

from app.core.types import Segment
from app.services.context import build_context
from app.services.fake_components import FakeSummarizer


def _neutral_segments() -> list[Segment]:
    return [
        Segment(i * 1000, (i + 1) * 1000, "Cliente", f"fala número {i} sobre a solução")
        for i in range(20)
    ]


def test_no_compression_within_budget() -> None:
    result = build_context(_neutral_segments(), [], summarizer=FakeSummarizer(), max_tokens=100_000)
    assert result.compressed is False
    assert "fala número 0" in result.prompt


def test_compression_keeps_protected_verbatim() -> None:
    segments = [
        *_neutral_segments(),
        Segment(99_000, 100_000, "Cliente", "Proposta de R$ 50.000 fechando este mês"),
    ]
    result = build_context(segments, [], summarizer=FakeSummarizer(), max_tokens=10)
    assert result.compressed is True
    assert "R$ 50.000" in result.prompt  # trecho protegido mantido íntegro
    assert "[resumo]" in result.prompt  # restante foi sumarizado
