"""Engine, criação de schema e dependência de sessão do banco."""

from collections.abc import Iterator

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings


def _make_engine(database_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


engine: Engine = _make_engine(get_settings().database_url)


def init_db(target_engine: Engine | None = None) -> None:
    """Cria as tabelas. Importa os modelos para registrá-los no metadata."""
    import app.models  # noqa: F401  (registra Meeting/Job no SQLModel.metadata)

    SQLModel.metadata.create_all(target_engine or engine)


def get_session() -> Iterator[Session]:
    """Dependência FastAPI: fornece uma sessão por request."""
    with Session(engine) as session:
        yield session
