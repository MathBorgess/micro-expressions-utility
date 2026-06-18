"""Retenção: apaga do disco os vídeos cujo job é mais antigo que N dias (questionário Q55).

Remove apenas o arquivo de vídeo do filesystem; o registro permanece no banco (sem histórico
de vídeo no MVP). A exclusão completa pelo usuário é o hard delete em `DELETE /meetings/{id}`.
"""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlmodel import Session, col, select

from app.models import Job, Meeting


def _as_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def purge_old_videos(
    session: Session, *, max_age_days: int = 7, now: datetime | None = None
) -> list[int]:
    """Apaga arquivos de vídeo de reuniões cujo job mais recente excedeu ``max_age_days``.

    Retorna os ids das reuniões cujo arquivo foi removido.
    """
    stamp = now or datetime.now(UTC)
    cutoff = stamp - timedelta(days=max_age_days)
    purged: list[int] = []
    for meeting in session.exec(select(Meeting)).all():
        if meeting.id is None:
            continue
        latest = session.exec(
            select(Job).where(col(Job.meeting_id) == meeting.id).order_by(col(Job.id).desc())
        ).first()
        reference = _as_aware(latest.created_at) if latest else _as_aware(meeting.created_at)
        if reference >= cutoff:
            continue
        video = Path(meeting.video_path)
        if video.exists():
            video.unlink()
            purged.append(meeting.id)
    return purged
