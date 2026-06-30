"""Construção da timeline: cruza sinais faciais com os segmentos de fala por intervalo."""

from app.core.types import BehavioralObservation, Segment, SignalEvent, TimelineEntry

# Palavras-chave que, junto a sinais de desengajamento, sugerem resistência (questionário Q43).
RESISTANCE_KEYWORDS = ("preço", "preco", "contrato", "prazo", "concorrente")
RESISTANCE_SIGNALS = ("olhar_desviado", "afastamento_da_tela")


def signals_in_segment(segment: Segment, signals: list[SignalEvent]) -> list[SignalEvent]:
    """Sinais cujo timestamp cai dentro do intervalo [start_ms, end_ms] do segmento."""
    return [s for s in signals if segment.start_ms <= s.timestamp_ms <= segment.end_ms]


def observations_in_segment(
    segment: Segment, observations: list[BehavioralObservation]
) -> list[BehavioralObservation]:
    """Observações cujo timestamp cai dentro do intervalo [start_ms, end_ms] do segmento."""
    return [o for o in observations if segment.start_ms <= o.timestamp_ms <= segment.end_ms]


def build_timeline(
    segments: list[Segment],
    signals: list[SignalEvent],
    observations: list[BehavioralObservation] | None = None,
) -> list[TimelineEntry]:
    """Gera a timeline consolidada, agrupando sinais e observações em cada segmento de fala."""
    obs_list = observations or []
    entries: list[TimelineEntry] = []
    for segment in sorted(segments, key=lambda seg: seg.start_ms):
        matched_signals = signals_in_segment(segment, signals)
        matched_obs = observations_in_segment(segment, obs_list)
        entries.append(
            TimelineEntry(
                start_time=segment.start_time,
                end_time=segment.end_time,
                speaker=segment.speaker,
                text=segment.text,
                signals=[s.to_dict() for s in matched_signals],
                observations=[o.to_dict() for o in matched_obs],
            )
        )
    return entries


def has_resistance(segment: Segment, signals: list[SignalEvent]) -> bool:
    """Heurística de resistência: palavra-chave sensível + sinal de desengajamento no trecho."""
    text = segment.text.lower()
    if not any(keyword in text for keyword in RESISTANCE_KEYWORDS):
        return False
    matched = signals_in_segment(segment, signals)
    return any(s.signal_type in RESISTANCE_SIGNALS for s in matched)
