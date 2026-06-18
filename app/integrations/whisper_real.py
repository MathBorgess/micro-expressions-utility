"""Transcrição real com Faster-Whisper (modelo carregado uma vez por worker)."""

from pathlib import Path
from typing import Any

from app.core.types import Segment
from app.services.errors import DefinitiveError


class WhisperTranscriber:
    """Carrega o modelo de forma preguiçosa e o mantém como singleton da instância."""

    def __init__(self, model_size: str = "base") -> None:
        self._model_size = model_size
        self._model: Any = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(self._model_size, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio_path: Path) -> list[Segment]:
        if not audio_path.exists():
            raise DefinitiveError(f"áudio não encontrado: {audio_path}")
        model = self._ensure_model()
        segments_iter, _info = model.transcribe(str(audio_path), language="pt")
        return [
            Segment(
                start_ms=int(seg.start * 1000),
                end_ms=int(seg.end * 1000),
                speaker="Desconhecido",
                text=seg.text.strip(),
            )
            for seg in segments_iter
        ]
