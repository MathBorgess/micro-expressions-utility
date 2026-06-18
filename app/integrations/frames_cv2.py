"""Leitura de frames em streaming via OpenCV (descarta cada frame após o uso)."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from app.core.timestamp import frame_to_ms


def iter_frames(video_path: Path) -> Iterator[tuple[int, Any]]:
    """Itera ``(timestamp_ms, frame)`` sem carregar o vídeo inteiro na memória."""
    import cv2

    capture = cv2.VideoCapture(str(video_path))
    fps = capture.get(cv2.CAP_PROP_FPS) or 24.0
    index = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            yield int(frame_to_ms(index, fps)), frame
            del frame  # libera a memória do frame imediatamente
            index += 1
    finally:
        capture.release()
