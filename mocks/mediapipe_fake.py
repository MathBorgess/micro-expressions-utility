"""Dublê do MediaPipe: devolve uma lista fixa de eventos com `signal_type`."""

from typing import Any

FAKE_SIGNALS: list[dict[str, Any]] = [
    {
        "timestamp_ms": 312000,
        "signal_type": "olhar_desviado",
        "confidence": 0.91,
        "meta": {"duration_seconds": 3.5},
        "source": "mediapipe_mesh_v1_eye_tracking",
    },
]

SCHEMA_VERSION = 1


def analyze(video_path: str = "") -> list[dict[str, Any]]:
    """Simula a análise facial, ignorando o vídeo e devolvendo sinais predefinidos."""
    return FAKE_SIGNALS
