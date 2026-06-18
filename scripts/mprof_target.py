"""Alvo do mprof: roda o pipeline uma vez para medir o pico de memória.

Usa os componentes-dublê por padrão (rápido/determinístico). Para medir o pipeline real,
defina ``APP_USE_REAL_PIPELINE=true`` e instale o extra ``ml``.
"""

import tempfile
from pathlib import Path

from app.config import get_settings
from app.services.factory import build_components
from app.services.pipeline import run_pipeline


def main() -> None:
    settings = get_settings()
    components = build_components(settings)
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        run_pipeline(
            job_dir=base / "job",
            video_path=base / "video.mp4",
            components=components,
            force=True,
        )


if __name__ == "__main__":
    main()
