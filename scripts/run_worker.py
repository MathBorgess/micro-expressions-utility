#!/usr/bin/env python3
"""Worker em loop contínuo: processa jobs pendentes da fila (concorrência 1).

Uso:
    uv run python scripts/run_worker.py

Com pipeline real:
    APP_USE_REAL_PIPELINE=true uv run python scripts/run_worker.py
"""

from __future__ import annotations

import time

from app.config import get_settings
from app.db import engine, init_db
from app.workers.manager import JobRunner

POLL_INTERVAL_SECONDS = 2.0


def main() -> None:
    init_db()
    settings = get_settings()
    mode = "real" if settings.use_real_pipeline else "dublê"
    runner = JobRunner(engine, settings)
    print(f"Worker iniciado (pipeline={mode}), aguardando jobs... Ctrl+C para parar.")
    while True:
        result = runner.run_once()
        if result is not None:
            print(f"Job processado: {result}")
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
