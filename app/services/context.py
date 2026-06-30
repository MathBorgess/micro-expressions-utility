"""Montagem do contexto do LLM com orçamento de tokens e sumarização hierárquica.

Se o prompt completo (sistema + transcrição + observações + features conversacionais) couber
no orçamento, usa-o íntegro. Caso contrário, comprime via sumarização por blocos (questionário
Q88): divide a transcrição não-protegida em duas metades e resume cada uma, **mantendo verbatim**
os trechos protegidos (valores monetários, prazos e objeções — Q89).
"""

from collections.abc import Callable
from dataclasses import dataclass

from app.core.conversation import extract_conversation_features
from app.core.observations import build_observations
from app.core.prompt import (
    build_conversation_text,
    build_observations_text,
    build_prompt,
    build_transcript_text,
    is_protected,
)
from app.core.tokens import estimate_tokens
from app.core.types import Segment, SignalEvent
from app.services.interfaces import Summarizer

DEFAULT_MAX_TOKENS = 7500


@dataclass
class ContextResult:
    prompt: str
    compressed: bool
    token_estimate: int


def build_context(
    segments: list[Segment],
    signals: list[SignalEvent],
    *,
    summarizer: Summarizer,
    count_tokens: Callable[[str], int] = estimate_tokens,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> ContextResult:
    conversation = extract_conversation_features(segments)
    observations = build_observations(signals, segments, conversation)
    observations_text = build_observations_text(observations)
    conversation_text = build_conversation_text(conversation)

    full_prompt = build_prompt(
        build_transcript_text(segments),
        observations_text,
        conversation_text,
    )
    full_tokens = count_tokens(full_prompt)
    if full_tokens <= max_tokens:
        return ContextResult(prompt=full_prompt, compressed=False, token_estimate=full_tokens)

    protected = [s for s in segments if is_protected(s.text)]
    rest = [s for s in segments if not is_protected(s.text)]
    mid = len(rest) // 2
    summary_a = summarizer.summarize(build_transcript_text(rest[:mid])) if rest[:mid] else ""
    summary_b = summarizer.summarize(build_transcript_text(rest[mid:])) if rest[mid:] else ""

    parts = [build_transcript_text(protected), summary_a, summary_b]
    compressed_transcript = "\n".join(part for part in parts if part.strip())
    prompt = build_prompt(compressed_transcript, observations_text, conversation_text)
    return ContextResult(prompt=prompt, compressed=True, token_estimate=count_tokens(prompt))
