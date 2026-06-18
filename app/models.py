"""Modelos de tabela (SQLModel). JSON é salvo como TEXT para portabilidade SQLite↔Postgres."""

from datetime import UTC, datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel


class JobStatus(StrEnum):
    """Estados do ciclo de vida de um job de processamento."""

    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Meeting(SQLModel, table=True):
    """Uma reunião enviada pelo usuário. O vídeo fica no filesystem (apenas o caminho aqui)."""

    __tablename__ = "meetings"

    id: int | None = Field(default=None, primary_key=True)
    filename: str
    video_path: str
    consent: bool = False
    # Relatório final em Markdown (sobrescrito no reprocessamento; sem histórico no MVP).
    report_markdown: str | None = None
    created_at: datetime = Field(default_factory=_utcnow)


class Job(SQLModel, table=True):
    """Tentativa de processamento de uma reunião (relação 1-N com `meetings`)."""

    __tablename__ = "jobs"

    id: int | None = Field(default=None, primary_key=True)
    meeting_id: int = Field(foreign_key="meetings.id", index=True)
    status: JobStatus = Field(default=JobStatus.pending)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    error_log: str | None = None
    # JSON serializado como string: tempos por estágio / CPU (Sprint 2+).
    telemetry: str | None = None
