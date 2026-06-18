"""Testes de integração da API de reuniões via TestClient (SQLite em memória)."""

import httpx
from fastapi.testclient import TestClient


def _upload(client: TestClient, *, consent: str = "true") -> httpx.Response:
    response: httpx.Response = client.post(
        "/api/v1/meetings/upload",
        files={"file": ("reuniao.mp4", b"fake-video-bytes", "video/mp4")},
        data={"consent": consent},
    )
    return response


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_available(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/api/v1/meetings/upload" in response.json()["paths"]


def test_upload_creates_pending_job(client: TestClient) -> None:
    response = _upload(client)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert isinstance(body["meeting_id"], int)


def test_upload_requires_consent(client: TestClient) -> None:
    response = _upload(client, consent="false")
    assert response.status_code == 422


def test_upload_rejects_bad_content_type(client: TestClient) -> None:
    response = client.post(
        "/api/v1/meetings/upload",
        files={"file": ("nota.txt", b"x", "text/plain")},
        data={"consent": "true"},
    )
    assert response.status_code == 415


def test_upload_missing_file_returns_422(client: TestClient) -> None:
    response = client.post("/api/v1/meetings/upload", data={"consent": "true"})
    assert response.status_code == 422


def test_status_and_report_flow(client: TestClient) -> None:
    meeting_id = _upload(client).json()["meeting_id"]

    status_response = client.get(f"/api/v1/meetings/{meeting_id}/status")
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "pending"

    report_response = client.get(f"/api/v1/meetings/{meeting_id}/report")
    assert report_response.status_code == 200
    assert report_response.json()["report_markdown"] is None


def test_list_meetings(client: TestClient) -> None:
    _upload(client)
    response = client.get("/api/v1/meetings/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_status_404_for_unknown(client: TestClient) -> None:
    assert client.get("/api/v1/meetings/9999/status").status_code == 404


def test_report_404_for_unknown(client: TestClient) -> None:
    assert client.get("/api/v1/meetings/9999/report").status_code == 404


def test_delete_meeting(client: TestClient) -> None:
    meeting_id = _upload(client).json()["meeting_id"]
    delete_response = client.delete(f"/api/v1/meetings/{meeting_id}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/meetings/{meeting_id}/status").status_code == 404


def test_delete_404_for_unknown(client: TestClient) -> None:
    assert client.delete("/api/v1/meetings/9999").status_code == 404
