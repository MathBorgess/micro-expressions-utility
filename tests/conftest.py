"""Fixtures de teste: banco SQLite em memória e TestClient com dependências sobrescritas."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import Settings, get_settings
from app.db import get_session
from app.main import app


@pytest.fixture
def engine() -> Iterator[Engine]:
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as sess:
        yield sess


@pytest.fixture
def client(engine: Engine, tmp_path: Path) -> Iterator[TestClient]:
    def get_session_override() -> Iterator[Session]:
        with Session(engine) as sess:
            yield sess

    test_settings = Settings(upload_dir=tmp_path / "uploads")

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_settings] = lambda: test_settings
    yield TestClient(app)
    app.dependency_overrides.clear()
