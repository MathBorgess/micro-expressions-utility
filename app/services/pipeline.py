"""Orquestrador do pipeline em 5 estágios, com checkpoints em disco e retomada.

Estágios: extract-audio → transcribe → face-analysis → timeline-builder → llm-analysis.
Cada estágio persiste seu artefato; se o artefato já existe (e ``force`` é falso), o estágio
é pulado — permitindo retomar a partir de qualquer ponto (ex.: refazer só o relatório).
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.signals import SCHEMA_VERSION
from app.core.telemetry import Telemetry, measure
from app.core.timeline import build_timeline
from app.core.tokens import estimate_tokens
from app.core.types import Segment, SignalEvent, TimelineEntry
from app.services.context import DEFAULT_MAX_TOKENS, build_context
from app.services.interfaces import (
    AudioExtractor,
    FaceAnalyzer,
    ReportGenerator,
    Summarizer,
    Transcriber,
)
from app.services.report_builder import generate_validated_report

AUDIO_FILE = "audio.wav"
TRANSCRIPT_FILE = "transcript.json"
SIGNALS_FILE = "signals.json"
TIMELINE_FILE = "timeline.json"
REPORT_FILE = "report.md"


@dataclass
class PipelineComponents:
    audio: AudioExtractor
    transcriber: Transcriber
    face: FaceAnalyzer
    report: ReportGenerator
    summarizer: Summarizer
    count_tokens: Callable[[str], int] = estimate_tokens


@dataclass
class PipelineResult:
    report_markdown: str
    segments: list[Segment]
    signals: list[SignalEvent]
    timeline: list[TimelineEntry]
    telemetry: Telemetry


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_pipeline(
    *,
    job_dir: Path,
    video_path: Path,
    components: PipelineComponents,
    telemetry: Telemetry | None = None,
    force: bool = False,
    max_context_tokens: int = DEFAULT_MAX_TOKENS,
) -> PipelineResult:
    job_dir.mkdir(parents=True, exist_ok=True)
    telemetry = telemetry or Telemetry()

    audio_path = job_dir / AUDIO_FILE
    transcript_path = job_dir / TRANSCRIPT_FILE
    signals_path = job_dir / SIGNALS_FILE
    timeline_path = job_dir / TIMELINE_FILE
    report_path = job_dir / REPORT_FILE

    # 1) extract-audio
    with measure(telemetry, "extract-audio"):
        if force or not audio_path.exists():
            components.audio.extract(video_path, audio_path)

    # 2) transcribe
    with measure(telemetry, "transcribe"):
        if not force and transcript_path.exists():
            segments = [Segment.from_dict(d) for d in _load_json(transcript_path)]
        else:
            segments = components.transcriber.transcribe(audio_path)
            _save_json(transcript_path, [s.to_dict() for s in segments])

    # 3) face-analysis
    with measure(telemetry, "face-analysis"):
        if not force and signals_path.exists():
            payload = _load_json(signals_path)
            signals = [SignalEvent.from_dict(d) for d in payload["signals"]]
        else:
            signals = components.face.analyze(video_path)
            _save_json(
                signals_path,
                {"schema_version": SCHEMA_VERSION, "signals": [s.to_dict() for s in signals]},
            )

    # 4) timeline-builder
    with measure(telemetry, "timeline-builder"):
        timeline = build_timeline(segments, signals)
        _save_json(timeline_path, [e.to_dict() for e in timeline])

    # 5) llm-analysis (orçamento de tokens + compressão + validação/retry)
    with measure(telemetry, "llm-analysis"):
        if not force and report_path.exists():
            report_markdown = report_path.read_text(encoding="utf-8")
        else:
            context = build_context(
                segments,
                timeline,
                summarizer=components.summarizer,
                count_tokens=components.count_tokens,
                max_tokens=max_context_tokens,
            )
            output = generate_validated_report(prompt=context.prompt, generator=components.report)
            report_markdown = output.markdown
            report_path.write_text(report_markdown, encoding="utf-8")

    return PipelineResult(
        report_markdown=report_markdown,
        segments=segments,
        signals=signals,
        timeline=timeline,
        telemetry=telemetry,
    )
