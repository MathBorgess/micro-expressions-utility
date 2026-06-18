"""Monta os componentes do pipeline conforme a configuração (dublês vs reais)."""

from app.config import Settings
from app.services.fake_components import (
    FakeAudioExtractor,
    FakeFaceAnalyzer,
    FakeReportGenerator,
    FakeSummarizer,
    FakeTranscriber,
)
from app.services.pipeline import PipelineComponents


def build_components(settings: Settings) -> PipelineComponents:
    """Componentes-dublê por padrão; reais quando ``use_real_pipeline`` está ligado."""
    if settings.use_real_pipeline:
        return _build_real(settings)
    return PipelineComponents(
        audio=FakeAudioExtractor(),
        transcriber=FakeTranscriber(),
        face=FakeFaceAnalyzer(),
        report=FakeReportGenerator(),
        summarizer=FakeSummarizer(),
    )


def _build_real(settings: Settings) -> PipelineComponents:  # pragma: no cover
    # Imports preguiçosos: só exigem o extra `ml` quando o pipeline real é usado.
    from app.integrations.audio_ffmpeg import FfmpegAudioExtractor
    from app.integrations.mediapipe_real import MediaPipeFaceAnalyzer
    from app.integrations.ollama_real import OllamaReportGenerator, OllamaSummarizer
    from app.integrations.tiktoken_counter import count_tokens
    from app.integrations.whisper_real import WhisperTranscriber

    return PipelineComponents(
        audio=FfmpegAudioExtractor(),
        transcriber=WhisperTranscriber(settings.whisper_model),
        face=MediaPipeFaceAnalyzer(),
        report=OllamaReportGenerator(settings.ollama_url),
        summarizer=OllamaSummarizer(settings.ollama_url),
        count_tokens=count_tokens,
    )
