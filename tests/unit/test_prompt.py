"""Testes da montagem de prompt e da detecção de trechos protegidos."""

from app.core.prompt import (
    FORBIDDEN_EXAMPLE_PHRASES,
    SYSTEM_PROMPT,
    build_conversation_text,
    build_observations_text,
    build_prompt,
    build_signals_text,
    build_transcript_text,
    is_protected,
)
from app.core.types import BehavioralObservation, ConversationFeatures, Segment, TimelineEntry


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


def test_system_prompt_forbids_mind_reading() -> None:
    assert "NUNCA" in SYSTEM_PROMPT or "nunca" in SYSTEM_PROMPT.lower()
    assert "emoç" in SYSTEM_PROMPT.lower() or "emoções" in SYSTEM_PROMPT.lower()


def test_build_observations_text_includes_hypotheses() -> None:
    obs = [
        BehavioralObservation(
            1000,
            "Contato visual reduzido",
            {"signal_type": "olhar_desviado"},
            ["hipótese A", "hipótese B"],
            0.6,
            ["vídeo"],
        )
    ]
    text = build_observations_text(obs)
    assert "hipótese A" in text
    assert "0.6" in text or "0.60" in text


def test_build_conversation_text_includes_features() -> None:
    features = ConversationFeatures(
        response_gaps_ms=[500, 1200],
        verbal_objection_segments=[2],
        verbal_agreement_segments=[5],
    )
    text = build_conversation_text(features)
    assert "500" in text
    assert "2" in text


def test_forbidden_phrases_list_not_empty() -> None:
    assert "perdeu confiança" in FORBIDDEN_EXAMPLE_PHRASES


def test_build_prompt_has_sections_and_title() -> None:
    prompt = build_prompt("T", "O", "C")
    assert "Relatório de Análise Comercial" in prompt
    assert "## Transcrição" in prompt
    assert "## Observações comportamentais (pré-processadas)" in prompt
    assert "## Features conversacionais" in prompt
    assert "Comportamentos Observados" in prompt
    assert "Oportunidades e Coaching" in prompt
