"""Fila de jobs no próprio banco (concorrência 1) e execução com retries.

- ``claim_next_job``: dequeue atômico (``pending`` → ``processing``) evitando duplicidade.
- ``reap_stuck_jobs``: marca como ``failed`` jobs ``processing`` parados além do timeout.
- ``JobRunner``: roda o pipeline de um job com retries/backoff e distinção de erros.
"""

import json
import time
import traceback
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session, col, select

from app.config import Settings
from app.core.telemetry import Telemetry
from app.models import Job, JobStatus, Meeting
from app.services.errors import DefinitiveError, TemporaryError
from app.services.factory import build_components
from app.services.pipeline import PipelineComponents, run_pipeline


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def claim_next_job(session: Session, *, now: datetime | None = None) -> Job | None:
    """Reivindica o próximo job pendente, marcando-o como ``processing`` atomicamente."""
    stamp = now or _utcnow()
    job = session.exec(
        select(Job).where(col(Job.status) == JobStatus.pending).order_by(col(Job.id))
    ).first()
    if job is None:
        return None
    job.status = JobStatus.processing
    job.updated_at = stamp
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def reap_stuck_jobs(
    session: Session, *, timeout_seconds: int, now: datetime | None = None
) -> list[int]:
    """Marca como ``failed`` jobs ``processing`` cujo ``updated_at`` excedeu o timeout."""
    stamp = now or _utcnow()
    cutoff = stamp - timedelta(seconds=timeout_seconds)
    stuck = session.exec(select(Job).where(col(Job.status) == JobStatus.processing)).all()
    reaped: list[int] = []
    for job in stuck:
        if _as_aware(job.updated_at) < cutoff:
            job.status = JobStatus.failed
            job.error_log = f"{job.error_log or ''}\n[reaper] job travado além do timeout".strip()
            job.updated_at = stamp
            session.add(job)
            if job.id is not None:
                reaped.append(job.id)
    session.commit()
    return reaped


class JobRunner:
    """Executa o pipeline de um job, persistindo status, telemetria e erros."""

    def __init__(
        self,
        engine: Engine,
        settings: Settings,
        *,
        components: PipelineComponents | None = None,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = _utcnow,
    ) -> None:
        self._engine = engine
        self._settings = settings
        self._components = components or build_components(settings)
        self._sleep = sleep
        self._now = now

    def _fail(self, session: Session, job: Job, message: str) -> None:
        job.status = JobStatus.failed
        job.error_log = message
        job.updated_at = self._now()
        session.add(job)
        session.commit()

    def process_job(self, job_id: int) -> JobStatus:
        with Session(self._engine) as session:
            job = session.get(Job, job_id)
            if job is None:
                raise ValueError(f"job {job_id} não encontrado")
            meeting = session.get(Meeting, job.meeting_id)
            if meeting is None:
                self._fail(session, job, "reunião associada não encontrada")
                return JobStatus.failed

            job_dir = self._settings.job_work_dir / str(meeting.id)
            video_path = Path(meeting.video_path)
            backoff = self._settings.retry_backoff_seconds
            attempts = max(1, self._settings.max_retries)

            for attempt in range(attempts):
                telemetry = Telemetry()
                try:
                    result = run_pipeline(
                        job_dir=job_dir,
                        video_path=video_path,
                        components=self._components,
                        telemetry=telemetry,
                        max_context_tokens=self._settings.max_context_tokens,
                    )
                except DefinitiveError as exc:
                    self._fail(session, job, f"erro definitivo: {exc}")
                    return JobStatus.failed
                except TemporaryError as exc:
                    if attempt + 1 >= attempts:
                        self._fail(session, job, f"erro temporário (retries esgotados): {exc}")
                        return JobStatus.failed
                    self._sleep(backoff[min(attempt, len(backoff) - 1)])
                    continue
                except Exception:
                    self._fail(session, job, f"erro inesperado:\n{traceback.format_exc()}")
                    return JobStatus.failed

                meeting.report_markdown = result.report_markdown
                job.telemetry = json.dumps(result.telemetry.to_dict(), ensure_ascii=False)
                job.status = JobStatus.completed
                job.error_log = None
                job.updated_at = self._now()
                session.add(meeting)
                session.add(job)
                session.commit()
                return JobStatus.completed

            return JobStatus.failed  # pragma: no cover - laço sempre retorna antes

    def run_once(self) -> JobStatus | None:
        """Reivindica e processa o próximo job pendente, se houver."""
        with Session(self._engine) as session:
            job = claim_next_job(session, now=self._now())
            job_id = job.id if job else None
        if job_id is None:
            return None
        return self.process_job(job_id)
