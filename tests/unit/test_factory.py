"""Testes da factory de componentes do pipeline."""

from app.config import Settings
from app.services.factory import build_components
from app.services.fake_components import (
    FakeAudioExtractor,
    FakeFaceAnalyzer,
    FakeReportGenerator,
    FakeTranscriber,
)


def test_factory_builds_fakes_by_default() -> None:
    components = build_components(Settings(use_real_pipeline=False))
    assert isinstance(components.audio, FakeAudioExtractor)
    assert isinstance(components.transcriber, FakeTranscriber)
    assert isinstance(components.face, FakeFaceAnalyzer)
    assert isinstance(components.report, FakeReportGenerator)
