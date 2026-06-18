"""Montagem do prompt do Ollama e identificação de trechos que nunca podem ser removidos."""

import re

from app.core.types import Segment, TimelineEntry

SYSTEM_PROMPT = (
    "Você é um analista comercial sênior. A partir da transcrição e da timeline de sinais "
    "comportamentais de uma reunião de vendas, gere um relatório em Markdown em português, "
    "usando EXATAMENTE estes títulos e nesta ordem:\n"
    "# Relatório de Análise Comercial\n"
    "## 1. Resumo Executivo\n"
    "## 2. Objeções Identificadas\n"
    "## 3. Momentos de Alto Engajamento\n"
    "## 4. Próximos Passos Recomendados\n"
    "Não invente dados. Cite timestamps e evidências verbais quando houver."
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
    lines: list[str] = []
    for entry in timeline:
        if not entry.signals:
            continue
        types = ", ".join(sorted({str(s["signal_type"]) for s in entry.signals}))
        lines.append(f"{entry.start_time}-{entry.end_time} [{entry.speaker}]: {types}")
    return "\n".join(lines)


def build_prompt(transcript_text: str, signals_text: str) -> str:
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"## Transcrição\n{transcript_text}\n\n"
        f"## Sinais comportamentais\n{signals_text}\n"
    )
