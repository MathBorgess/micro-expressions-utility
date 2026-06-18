"""Endpoints de reuniões sob `/api/v1/meetings`.

Sprint 1 (lean): o upload valida, persiste o arquivo no filesystem e enfileira um job
`pending`. O processamento real (workers/pipeline) chega no Sprint 2.
"""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session, col, select

from app.config import Settings, get_settings
from app.db import get_session
from app.models import Job, JobStatus, Meeting
from app.schemas import (
    MeetingCreatedResponse,
    MeetingReportResponse,
    MeetingStatusResponse,
    MeetingSummary,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])

_CHUNK_SIZE = 1024 * 1024


def _latest_job(session: Session, meeting_id: int) -> Job | None:
    statement = select(Job).where(col(Job.meeting_id) == meeting_id).order_by(col(Job.id).desc())
    return session.exec(statement).first()


def _get_meeting_or_404(session: Session, meeting_id: int) -> Meeting:
    meeting = session.get(Meeting, meeting_id)
    if meeting is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="reunião não encontrada")
    return meeting


@router.post(
    "/upload",
    response_model=MeetingCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Faz upload de um vídeo de reunião e enfileira o processamento",
)
async def upload_meeting(
    file: UploadFile = File(...),
    consent: bool = Form(...),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> MeetingCreatedResponse:
    if not consent:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="consentimento é obrigatório"
        )
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"tipo não suportado: {file.content_type}",
        )

    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "video").suffix or ".mp4"
    dest = settings.upload_dir / f"{uuid4().hex}{suffix}"

    size = 0
    with dest.open("wb") as buffer:
        while chunk := await file.read(_CHUNK_SIZE):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                buffer.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="arquivo excede o limite máximo de upload",
                )
            buffer.write(chunk)

    meeting = Meeting(filename=file.filename or dest.name, video_path=str(dest), consent=consent)
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    assert meeting.id is not None

    job = Job(meeting_id=meeting.id, status=JobStatus.pending)
    session.add(job)
    session.commit()
    session.refresh(job)

    return MeetingCreatedResponse(meeting_id=meeting.id, status=job.status)


@router.get("/", response_model=list[MeetingSummary], summary="Lista as reuniões")
def list_meetings(session: Session = Depends(get_session)) -> list[MeetingSummary]:
    meetings = session.exec(select(Meeting).order_by(col(Meeting.id).desc())).all()
    summaries: list[MeetingSummary] = []
    for meeting in meetings:
        assert meeting.id is not None
        job = _latest_job(session, meeting.id)
        summaries.append(
            MeetingSummary(
                id=meeting.id,
                filename=meeting.filename,
                status=job.status if job else JobStatus.pending,
                created_at=meeting.created_at,
            )
        )
    return summaries


@router.get(
    "/{meeting_id}/status",
    response_model=MeetingStatusResponse,
    summary="Status de processamento da reunião",
)
def get_status(meeting_id: int, session: Session = Depends(get_session)) -> MeetingStatusResponse:
    _get_meeting_or_404(session, meeting_id)
    job = _latest_job(session, meeting_id)
    return MeetingStatusResponse(
        meeting_id=meeting_id, status=job.status if job else JobStatus.pending
    )


@router.get(
    "/{meeting_id}/report",
    response_model=MeetingReportResponse,
    summary="Relatório consolidado em Markdown",
)
def get_report(meeting_id: int, session: Session = Depends(get_session)) -> MeetingReportResponse:
    meeting = _get_meeting_or_404(session, meeting_id)
    job = _latest_job(session, meeting_id)
    return MeetingReportResponse(
        meeting_id=meeting_id,
        status=job.status if job else JobStatus.pending,
        report_markdown=meeting.report_markdown,
    )


@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui a reunião (hard delete: registro + arquivo)",
)
def delete_meeting(meeting_id: int, session: Session = Depends(get_session)) -> None:
    meeting = _get_meeting_or_404(session, meeting_id)
    for job in session.exec(select(Job).where(col(Job.meeting_id) == meeting_id)).all():
        session.delete(job)
    Path(meeting.video_path).unlink(missing_ok=True)
    session.delete(meeting)
    session.commit()
