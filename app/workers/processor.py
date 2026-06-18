"""Entrypoint do worker: processa um job num ProcessPoolExecutor de concorrência 1.

Alvo do gate de memória (Sprint 2): ``mprof run -m app.workers.processor`` deve manter o
pico de RAM < 2.5 GB. O worker roda com prioridade reduzida (``nice -n 10``) para não
disputar CPU com a API.
"""

import contextlib
import os
from concurrent.futures import ProcessPoolExecutor

from app.config import get_settings
from app.db import engine, init_db
from app.workers.manager import JobRunner


def process_one() -> None:  # pragma: no cover - executado em subprocesso
    with contextlib.suppress(AttributeError, PermissionError, OSError):
        os.nice(10)
    settings = get_settings()
    init_db()
    runner = JobRunner(engine, settings)
    status = runner.run_once()
    print(f"[processor] run_once -> {status}")


def main() -> None:  # pragma: no cover - wiring de processo
    # 1 worker = processamento estritamente sequencial (concurrency=1).
    with ProcessPoolExecutor(max_workers=1) as pool:
        pool.submit(process_one).result()


if __name__ == "__main__":  # pragma: no cover
    main()
