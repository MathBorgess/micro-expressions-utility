"""Features conversacionais derivadas só da transcrição (sem nova dep)."""

import re

from app.core.types import ConversationFeatures, Segment

GAP_THRESHOLD_MS = 1500
_OBJECTION_RE = re.compile(
    r"(caro|pre[çc]o|or[çc]amento|concorrente|n[aã]o\s+sei|dif[ií]cil)", re.IGNORECASE
)
_AGREEMENT_RE = re.compile(
    r"(concordo|faz sentido|interessante|gostei|perfeito|ok\b)", re.IGNORECASE
)


def extract_conversation_features(segments: list[Segment]) -> ConversationFeatures:
    sorted_segments = sorted(segments, key=lambda s: s.start_ms)
    gaps: list[int] = []
    objections: list[int] = []
    agreements: list[int] = []

    for index, segment in enumerate(sorted_segments):
        if _OBJECTION_RE.search(segment.text):
            objections.append(index)
        if _AGREEMENT_RE.search(segment.text):
            agreements.append(index)
        if index == 0:
            continue
        prev = sorted_segments[index - 1]
        gap = segment.start_ms - prev.end_ms
        if gap >= GAP_THRESHOLD_MS:
            gaps.append(gap)

    return ConversationFeatures(
        response_gaps_ms=gaps,
        verbal_objection_segments=objections,
        verbal_agreement_segments=agreements,
    )
