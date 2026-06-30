"""Converte sinais brutos em observações evidenciadas com hipóteses alternativas."""

from app.core.timeline import signals_in_segment
from app.core.types import BehavioralObservation, ConversationFeatures, Segment, SignalEvent

_SIGNAL_COPY: dict[str, str] = {
    "olhar_desviado": "Contato visual reduzido por período prolongado",
    "afastamento_da_tela": "Afastamento físico em relação à câmera",
    "aceno_cabeca_positivo": "Movimento rítmico de cabeça (vertical)",
    "aceno_cabeca_negativo": "Movimento rítmico de cabeça (horizontal)",
}

_GAZE_HYPOTHESES = [
    "Processamento cognitivo ou reflexão",
    "Desconforto ou discordância possível (não conclusivo)",
    "Distração ambiental ou fadiga",
]
_DEFAULT_HYPOTHESES = [
    "Mudança postural sem significado afetivo específico",
    "Resposta a estímulo externo à conversa",
]
_MULTIMODAL_BONUS = 0.15
_MAX_CONFIDENCE = 0.95


def _hypotheses_for(signal_type: str) -> list[str]:
    if signal_type == "olhar_desviado":
        return list(_GAZE_HYPOTHESES)
    return list(_DEFAULT_HYPOTHESES)


def _modalities_for(segment_index: int, conv: ConversationFeatures, has_video: bool) -> list[str]:
    mods: list[str] = []
    if has_video:
        mods.append("vídeo")
    if segment_index in conv.verbal_objection_segments:
        mods.append("transcrição")
    if segment_index in conv.verbal_agreement_segments:
        mods.append("transcrição")
    return mods


def build_observations(
    signals: list[SignalEvent],
    segments: list[Segment],
    conversation: ConversationFeatures,
) -> list[BehavioralObservation]:
    observations: list[BehavioralObservation] = []
    sorted_segments = sorted(segments, key=lambda s: s.start_ms)

    for index, segment in enumerate(sorted_segments):
        matched = signals_in_segment(segment, signals)
        for signal in matched:
            base_conf = min(signal.confidence, 1.0)
            modalities = _modalities_for(index, conversation, has_video=True)
            confidence = base_conf
            if "transcrição" in modalities and signal.signal_type in (
                "olhar_desviado",
                "afastamento_da_tela",
            ):
                confidence = min(_MAX_CONFIDENCE, base_conf + _MULTIMODAL_BONUS)

            observations.append(
                BehavioralObservation(
                    timestamp_ms=signal.timestamp_ms,
                    observation=_SIGNAL_COPY.get(signal.signal_type, signal.signal_type),
                    evidence={
                        "signal_type": signal.signal_type,
                        "segment_text": segment.text,
                        "meta": signal.meta,
                        "speaker": segment.speaker,
                    },
                    hypotheses=_hypotheses_for(signal.signal_type),
                    confidence=round(confidence, 3),
                    modalities=modalities,
                )
            )
    observations.sort(key=lambda o: o.timestamp_ms)
    return observations
