"""Testes dos dublês determinísticos (espelham as asserções do E2E do Harness)."""

from mocks.mediapipe_fake import analyze
from mocks.ollama_fake import generate_report
from mocks.whisper_fake import transcribe


def test_whisper_contains_keywords() -> None:
    text = " ".join(seg["text"] for seg in transcribe("x.wav"))
    assert "produto" in text
    assert "preço" in text


def test_mediapipe_has_signal_type() -> None:
    signals = analyze("x.mp4")
    assert len(signals) >= 1
    assert all("signal_type" in s for s in signals)


def test_ollama_report_has_required_headers() -> None:
    report = generate_report("prompt")
    assert report.strip()
    for header in (
        "## 1. Resumo Executivo",
        "## 2. Objeções Identificadas",
        "## 4. Próximos Passos Recomendados",
    ):
        assert header in report
