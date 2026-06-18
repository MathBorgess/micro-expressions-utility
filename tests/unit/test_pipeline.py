"""Testes do orquestrador do pipeline (com componentes-dublê)."""

from pathlib import Path

from app.config import Settings
from app.services.factory import build_components
from app.services.pipeline import (
    AUDIO_FILE,
    REPORT_FILE,
    SIGNALS_FILE,
    TRANSCRIPT_FILE,
    PipelineResult,
    run_pipeline,
)


def _run(tmp_path: Path, *, force: bool = False) -> PipelineResult:
    components = build_components(Settings(use_real_pipeline=False))
    return run_pipeline(
        job_dir=tmp_path,
        video_path=tmp_path / "video.mp4",
        components=components,
        force=force,
    )


def test_pipeline_produces_report_and_checkpoints(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert "Relatório de Análise Comercial" in result.report_markdown
    assert (tmp_path / AUDIO_FILE).exists()
    assert (tmp_path / TRANSCRIPT_FILE).exists()
    assert (tmp_path / SIGNALS_FILE).exists()
    assert (tmp_path / REPORT_FILE).exists()
    assert len(result.telemetry.stages) == 5


def test_pipeline_resumes_from_checkpoint(tmp_path: Path) -> None:
    _run(tmp_path)
    (tmp_path / REPORT_FILE).write_text("CUSTOM", encoding="utf-8")
    result = _run(tmp_path)
    assert result.report_markdown == "CUSTOM"


def test_pipeline_force_regenerates(tmp_path: Path) -> None:
    _run(tmp_path)
    (tmp_path / REPORT_FILE).write_text("CUSTOM", encoding="utf-8")
    result = _run(tmp_path, force=True)
    assert result.report_markdown != "CUSTOM"
