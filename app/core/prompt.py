"""Montagem do prompt do Ollama e identificação de trechos que nunca podem ser removidos."""

import re

from app.core.types import (
    BehavioralObservation,
    ConversationFeatures,
    Segment,
    TimelineEntry,
)

FORBIDDEN_EXAMPLE_PHRASES = (
    "perdeu confiança",
    "ficou com medo",
    "odiou",
    "rejeitou o produto",
    "não gostou",
)

SYSTEM_PROMPT = (
    "Você é um analista de comunicação comercial. "
    "NUNCA afirme emoções, intenções internas ou atitudes sem evidência multimodal explícita.\n"
    "Separe: (1) Observação mensurável (2) Hipótese com alternativas (3) Recomendação.\n"
    "Use 'pode indicar' — nunca certeza.\n"
    "Cite timestamps [HH:MM:SS] e modalidade (vídeo/transcrição/silêncio).\n"
    "Estrutura OBRIGATÓRIA:\n"
    "# Relatório de Análise Comercial\n"
    "## 1. Comportamentos Observados\n"
    "## 2. Linha do Tempo\n"
    "## 3. Mudanças de Comportamento\n"
    "## 4. Hipóteses Interpretativas\n"
    "## 5. Contexto Conversacional\n"
    "## 6. Confiança e Limitações\n"
    "## 7. Perguntas de Follow-up Sugeridas\n"
    "## 8. Oportunidades e Coaching\n"
)

# Trechos protegidos (questionário Q89): valores monetários, prazos e objeções explícitas.
_MONEY_RE = re.compile(r"(r\$\s*\d|\d+\s*(reais|mil|k\b)|\d+\s*%|desconto)", re.IGNORECASE)
_DEADLINE_RE = re.compile(r"(prazo|fechamento|deadline|semana|m[eê]s\b|trimestre)", re.IGNORECASE)
_OBJECTION_RE = re.compile(
    r"(caro|pre[çc]o|or[çc]amento|concorrente|contrato|obje[çc])", re.IGNORECASE
)


def is_protected(text: str) -> bool:
    """True se o trecho contém valor monetário, prazo de fechamento ou objeção explícita."""
    return bool(_MONEY_RE.search(text) or _DEADLINE_RE.search(text) or _OBJECTION_RE.search(text))


def build_transcript_text(segments: list[Segment]) -> str:
    return "\n".join(f"[{s.speaker}] {s.text}" for s in segments)


def build_signals_text(timeline: list[TimelineEntry]) -> str:
    """Deprecated: prefer build_observations_text para o fluxo evidence-first."""
    lines: list[str] = []
    for entry in timeline:
        if not entry.signals:
            continue
        types = ", ".join(sorted({str(s["signal_type"]) for s in entry.signals}))
        lines.append(f"{entry.start_time}-{entry.end_time} [{entry.speaker}]: {types}")
    return "\n".join(lines)


def build_observations_text(observations: list[BehavioralObservation]) -> str:
    lines: list[str] = []
    for ob in observations:
        hyps = "; ".join(ob.hypotheses)
        mods = ", ".join(ob.modalities)
        lines.append(
            f"[{ob.timestamp_ms}ms] {ob.observation} | conf={ob.confidence} | "
            f"modalidades={mods} | hipóteses: {hyps}"
        )
    return "\n".join(lines)


def build_conversation_text(features: ConversationFeatures) -> str:
    return (
        f"Gaps de resposta (ms): {features.response_gaps_ms}\n"
        f"Segmentos com objeção verbal: {features.verbal_objection_segments}\n"
        f"Segmentos com concordância verbal: {features.verbal_agreement_segments}"
    )


def build_prompt(
    transcript_text: str,
    observations_text: str,
    conversation_text: str,
) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"## Transcrição\n{transcript_text}\n\n"
        f"## Observações comportamentais (pré-processadas)\n{observations_text}\n\n"
        f"## Features conversacionais\n{conversation_text}\n"
    )
