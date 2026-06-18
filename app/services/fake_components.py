"""Componentes-dublê determinísticos do pipeline (usados em CI e dev).

Reaproveitam os dados fixos de ``mocks/`` e implementam os Protocols de ``interfaces``.
"""

from pathlib import Path

from app.core.types import Segment, SignalEvent
from mocks.mediapipe_fake import analyze as fake_mediapipe
from mocks.ollama_fake import generate_report as fake_ollama
from mocks.whisper_fake import transcribe as fake_whisper

# Mapeia o "HH:MM:SS" dos segmentos-dublê para milissegundos simples (00:00:05 -> 5000).
_FAKE_SEGMENT_BOUNDS_MS = (0, 5000)


class FakeAudioExtractor:
    """Gera um .wav vazio para satisfazer o checkpoint de áudio."""

    def extract(self, video_path: Path, out_wav: Path) -> Path:
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        out_wav.write_bytes(b"RIFF\x00\x00\x00\x00WAVEfmt ")
        return out_wav


class FakeTranscriber:
    def transcribe(self, audio_path: Path) -> list[Segment]:
        start_ms, end_ms = _FAKE_SEGMENT_BOUNDS_MS
        return [
            Segment(
                start_ms=start_ms,
                end_ms=end_ms,
                speaker=str(seg["speaker"]),
                text=str(seg["text"]),
            )
            for seg in fake_whisper(str(audio_path))
        ]


class FakeFaceAnalyzer:
    def analyze(self, video_path: Path) -> list[SignalEvent]:
        return [SignalEvent.from_dict(sig) for sig in fake_mediapipe(str(video_path))]


class FakeSummarizer:
    def summarize(self, text: str) -> str:
        snippet = text.strip().splitlines()[0][:120] if text.strip() else ""
        return f"[resumo] {snippet}" if snippet else ""


class FakeReportGenerator:
    def generate(self, prompt: str, *, temperature: float = 0.7) -> str:
        return fake_ollama(prompt)
