"""Testes da retenção de vídeos (purge > N dias)."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import Engine
from sqlmodel import Session

from app.models import Job, JobStatus, Meeting
from app.services.retention import purge_old_videos


def _meeting_with_video(session: Session, tmp_path: Path, *, age_days: int) -> int:
    video = tmp_path / f"video_{age_days}.mp4"
    video.write_bytes(b"fake")
    meeting = Meeting(filename=video.name, video_path=str(video), consent=True)
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    assert meeting.id is not None
    job = Job(
        meeting_id=meeting.id,
        status=JobStatus.completed,
        created_at=datetime.now(UTC) - timedelta(days=age_days),
    )
    session.add(job)
    session.commit()
    return meeting.id


def test_purge_removes_old_video_keeps_recent(engine: Engine, tmp_path: Path) -> None:
    with Session(engine) as session:
        old_id = _meeting_with_video(session, tmp_path, age_days=10)
        recent_id = _meeting_with_video(session, tmp_path, age_days=1)

        purged = purge_old_videos(session, max_age_days=7)

        assert old_id in purged
        assert recent_id not in purged

        old = session.get(Meeting, old_id)
        recent = session.get(Meeting, recent_id)
        assert old is not None and recent is not None
        assert not Path(old.video_path).exists()  # vídeo apagado
        assert Path(recent.video_path).exists()  # vídeo recente preservado
        assert session.get(Meeting, old_id) is not None  # registro mantido
