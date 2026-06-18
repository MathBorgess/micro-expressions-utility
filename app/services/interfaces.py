"""Contratos (Protocols) dos componentes intercambiáveis do pipeline.

Permitem trocar dublês determinísticos (CI) por implementações reais (estágio final)
sem alterar o orquestrador.
"""

from pathlib import Path
from typing import Protocol

from app.core.types import Segment, SignalEvent


class AudioExtractor(Protocol):
    def extract(self, video_path: Path, out_wav: Path) -> Path:
        """Extrai a faixa de áudio do vídeo para um arquivo .wav e retorna o caminho."""
        ...


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> list[Segment]:
        """Transcreve o áudio em segmentos de fala (frases)."""
        ...


class FaceAnalyzer(Protocol):
    def analyze(self, video_path: Path) -> list[SignalEvent]:
        """Analisa os frames e devolve os eventos comportamentais detectados."""
        ...


class Summarizer(Protocol):
    def summarize(self, text: str) -> str:
        """Resume um bloco de texto preservando informações comerciais críticas."""
        ...


class ReportGenerator(Protocol):
    def generate(self, prompt: str, *, temperature: float = 0.7) -> str:
        """Gera o relatório final em Markdown a partir do prompt já montado."""
        ...
