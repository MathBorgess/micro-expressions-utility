"""E2E determinístico (dublês): login → upload → worker → relatório.

Cobre os critérios do Harness: gera audio.wav, transcrição com 'produto'/'preço', JSON do
MediaPipe com 'signal_type', relatório estruturado não vazio — tudo em < 3 minutos.
"""

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import Engine

from app.config import Settings
from app.models import JobStatus
from app.workers.manager import JobRunner


def _noop_sleep(_seconds: float) -> None:
    return None


def test_full_pipeline_e2e(client: TestClient, engine: Engine, tmp_path: Path) -> None:
    started = time.perf_counter()

    # 1) login
    login = client.post("/api/v1/auth/login", json={"username": "vendedor", "password": "changeme"})
    assert login.status_code == 200

    # 2) upload do vídeo (mock)
    upload = client.post(
        "/api/v1/meetings/upload",
        files={"file": ("reuniao.mp4", b"fake-video-bytes", "video/mp4")},
        data={"consent": "true"},
    )
    assert upload.status_code == 201
    meeting_id = upload.json()["meeting_id"]
    assert client.get(f"/api/v1/meetings/{meeting_id}/status").json()["status"] == "pending"

    # 3) worker processa o job (concorrência 1, dublês determinísticos)
    jobs_dir = tmp_path / "jobs"
    runner = JobRunner(engine, Settings(job_work_dir=jobs_dir), sleep=_noop_sleep)
    assert runner.run_once() == JobStatus.completed

    # 4) status completed + relatório estruturado
    assert client.get(f"/api/v1/meetings/{meeting_id}/status").json()["status"] == "completed"
    report = client.get(f"/api/v1/meetings/{meeting_id}/report").json()["report_markdown"]
    assert report
    for header in (
        "## 1. Resumo Executivo",
        "## 2. Objeções Identificadas",
        "## 4. Próximos Passos Recomendados",
    ):
        assert header in report

    # 5) checkpoints físicos + asserções do Harness
    job_dir = jobs_dir / str(meeting_id)
    assert (job_dir / "audio.wav").exists()
    transcript = json.loads((job_dir / "transcript.json").read_text(encoding="utf-8"))
    transcript_text = " ".join(seg["text"] for seg in transcript)
    assert "produto" in transcript_text
    assert "preço" in transcript_text
    signals = json.loads((job_dir / "signals.json").read_text(encoding="utf-8"))
    assert any("signal_type" in signal for signal in signals["signals"])
    assert (job_dir / "report.md").exists()

    # 6) tempo total do E2E < 3 minutos
    assert time.perf_counter() - started < 180
