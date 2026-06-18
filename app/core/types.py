"""Tipos de domínio compartilhados pelo pipeline de processamento."""

from dataclasses import dataclass, field
from typing import Any

from app.core.timestamp import ms_to_timestamp


@dataclass
class Segment:
    """Trecho de fala transcrito pelo Whisper (granularidade de frase)."""

    start_ms: int
    end_ms: int
    speaker: str
    text: str

    @property
    def start_time(self) -> str:
        return ms_to_timestamp(self.start_ms)

    @property
    def end_time(self) -> str:
        return ms_to_timestamp(self.end_ms)

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_ms": self.start_ms,
            "end_ms": self.end_ms,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "speaker": self.speaker,
            "text": self.text,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Segment":
        return cls(
            start_ms=int(data["start_ms"]),
            end_ms=int(data["end_ms"]),
            speaker=str(data["speaker"]),
            text=str(data["text"]),
        )


@dataclass
class SignalEvent:
    """Evento comportamental heurístico extraído dos landmarks faciais."""

    timestamp_ms: int
    signal_type: str
    confidence: float
    meta: dict[str, Any] = field(default_factory=dict)
    source: str = "mediapipe_mesh_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_ms": self.timestamp_ms,
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "meta": self.meta,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SignalEvent":
        return cls(
            timestamp_ms=int(data["timestamp_ms"]),
            signal_type=str(data["signal_type"]),
            confidence=float(data["confidence"]),
            meta=dict(data.get("meta", {})),
            source=str(data.get("source", "mediapipe_mesh_v1")),
        )


@dataclass
class FrameMetrics:
    """Métricas por frame produzidas pela análise facial (entrada das heurísticas).

    Mantém-se desacoplado do MediaPipe para permitir testes determinísticos das heurísticas.
    """

    timestamp_ms: int
    looking_at_screen: bool
    face_size_ratio: float  # área relativa da face no frame (0..1)
    face_center_x: float  # 0..1
    face_center_y: float  # 0..1
    confidence: float = 1.0


@dataclass
class TimelineEntry:
    """Segmento de fala com os sinais faciais ocorridos no mesmo intervalo."""

    start_time: str
    end_time: str
    speaker: str
    text: str
    signals: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "speaker": self.speaker,
            "text": self.text,
            "signals": self.signals,
        }
