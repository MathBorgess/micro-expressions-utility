"""Job de retenção (rodar via cron diário): apaga vídeos com job > N dias."""

from sqlmodel import Session

from app.config import get_settings
from app.db import engine, init_db
from app.services.retention import purge_old_videos


def main() -> None:  # pragma: no cover - entrypoint de cron
    init_db()
    settings = get_settings()
    with Session(engine) as session:
        purged = purge_old_videos(session, max_age_days=settings.retention_days)
    print(f"[retention] vídeos removidos: {len(purged)}")


if __name__ == "__main__":  # pragma: no cover
    main()
