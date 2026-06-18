"""Testes da fila de jobs e do JobRunner (SQLite em memória + componentes-dublê)."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session

from app.config import Settings
from app.core.types import Segment, SignalEvent
from app.models import Job, JobStatus, Meeting
from app.services.errors import DefinitiveError, TemporaryError
from app.services.factory import build_components
from app.services.fake_components import (
    FakeAudioExtractor,
    FakeFaceAnalyzer,
    FakeReportGenerator,
    FakeSummarizer,
    FakeTranscriber,
)
from app.services.pipeline import PipelineComponents
from app.workers.manager import JobRunner, claim_next_job, reap_stuck_jobs


def _make_meeting_job(session: Session) -> tuple[int, int]:
    meeting = Meeting(filename="r.mp4", video_path="/tmp/r.mp4", consent=True)
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    assert meeting.id is not None
    job = Job(meeting_id=meeting.id, status=JobStatus.pending)
    session.add(job)
    session.commit()
    session.refresh(job)
    assert job.id is not None
    return meeting.id, job.id


def _noop_sleep(_seconds: float) -> None:
    return None


def test_claim_next_job_is_atomic(engine: Engine) -> None:
    with Session(engine) as session:
        _make_meeting_job(session)
        claimed = claim_next_job(session)
        assert claimed is not None
        assert claimed.status == JobStatus.processing
        assert claim_next_job(session) is None


def test_process_job_success(engine: Engine, tmp_path: Path) -> None:
    with Session(engine) as session:
        meeting_id, job_id = _make_meeting_job(session)
    settings = Settings(job_work_dir=tmp_path, use_real_pipeline=False)
    runner = JobRunner(engine, settings, components=build_components(settings), sleep=_noop_sleep)

    assert runner.process_job(job_id) == JobStatus.completed

    with Session(engine) as session:
        job = session.get(Job, job_id)
        meeting = session.get(Meeting, meeting_id)
        assert job is not None and meeting is not None
        assert job.status == JobStatus.completed
        assert meeting.report_markdown is not None
        assert "Relatório" in meeting.report_markdown
        assert job.telemetry is not None
        assert json.loads(job.telemetry)["stages"]


def test_process_job_retries_then_fails(engine: Engine, tmp_path: Path) -> None:
    class FlakyTranscriber:
        def __init__(self) -> None:
            self.calls = 0

        def transcribe(self, audio_path: Path) -> list[Segment]:
            self.calls += 1
            raise TemporaryError("rede instável")

    with Session(engine) as session:
        _, job_id = _make_meeting_job(session)
    flaky = FlakyTranscriber()
    components = PipelineComponents(
        audio=FakeAudioExtractor(),
        transcriber=flaky,
        face=FakeFaceAnalyzer(),
        report=FakeReportGenerator(),
        summarizer=FakeSummarizer(),
    )
    settings = Settings(job_work_dir=tmp_path, max_retries=3, retry_backoff_seconds=(0, 0, 0))
    runner = JobRunner(engine, settings, components=components, sleep=_noop_sleep)

    assert runner.process_job(job_id) == JobStatus.failed
    assert flaky.calls == 3
    with Session(engine) as session:
        job = session.get(Job, job_id)
        assert job is not None and job.error_log is not None


def test_process_job_definitive_fails_immediately(engine: Engine, tmp_path: Path) -> None:
    class BrokenFace:
        def analyze(self, video_path: Path) -> list[SignalEvent]:
            raise DefinitiveError("vídeo corrompido")

    with Session(engine) as session:
        _, job_id = _make_meeting_job(session)
    components = PipelineComponents(
        audio=FakeAudioExtractor(),
        transcriber=FakeTranscriber(),
        face=BrokenFace(),
        report=FakeReportGenerator(),
        summarizer=FakeSummarizer(),
    )
    settings = Settings(job_work_dir=tmp_path)
    runner = JobRunner(engine, settings, components=components, sleep=_noop_sleep)

    assert runner.process_job(job_id) == JobStatus.failed
    with Session(engine) as session:
        job = session.get(Job, job_id)
        assert job is not None and job.error_log is not None
        assert "definitivo" in job.error_log


def test_reap_stuck_jobs(engine: Engine) -> None:
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    with Session(engine) as session:
        meeting = Meeting(filename="r", video_path="/x", consent=True)
        session.add(meeting)
        session.commit()
        session.refresh(meeting)
        assert meeting.id is not None
        job = Job(
            meeting_id=meeting.id,
            status=JobStatus.processing,
            updated_at=now - timedelta(hours=1),
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job.id is not None
        job_id = job.id

        reaped = reap_stuck_jobs(session, timeout_seconds=1800, now=now)
        assert job_id in reaped
        reaped_job = session.get(Job, job_id)
        assert reaped_job is not None and reaped_job.status == JobStatus.failed


def test_run_once_processes_then_empty(engine: Engine, tmp_path: Path) -> None:
    with Session(engine) as session:
        _make_meeting_job(session)
    runner = JobRunner(engine, Settings(job_work_dir=tmp_path), sleep=_noop_sleep)
    assert runner.run_once() == JobStatus.completed
    assert runner.run_once() is None
