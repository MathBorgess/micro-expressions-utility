"""Testes da montagem de prompt e da detecção de trechos protegidos."""

from app.core.prompt import (
    build_prompt,
    build_signals_text,
    build_transcript_text,
    is_protected,
)
from app.core.types import Segment, TimelineEntry


def test_is_protected_money() -> None:
    assert is_protected("Proposta de R$ 50.000 com desconto")


def test_is_protected_deadline() -> None:
    assert is_protected("fechamos no próximo mês")


def test_is_protected_objection() -> None:
    assert is_protected("o preço está acima do orçamento")


def test_is_not_protected() -> None:
    assert not is_protected("gostei muito da demonstração de hoje")


def test_build_transcript_text() -> None:
    segments = [Segment(0, 1000, "Cliente", "olá")]
    assert "[Cliente] olá" in build_transcript_text(segments)


def test_build_signals_text_skips_empty() -> None:
    timeline = [
        TimelineEntry("00:00:00", "00:00:05", "Cliente", "x", [{"signal_type": "olhar_desviado"}]),
        TimelineEntry("00:00:06", "00:00:10", "Vendedor", "y", []),
    ]
    out = build_signals_text(timeline)
    assert "olhar_desviado" in out
    assert "Vendedor" not in out


def test_build_prompt_has_sections_and_title() -> None:
    prompt = build_prompt("T", "S")
    assert "Relatório de Análise Comercial" in prompt
    assert "## Transcrição" in prompt
    assert "## Sinais comportamentais" in prompt
