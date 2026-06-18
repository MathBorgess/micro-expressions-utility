"""Extração de áudio e normalização de vídeo via ffmpeg (subprocess)."""

import subprocess
from pathlib import Path

from app.services.errors import DefinitiveError


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise DefinitiveError(f"ffmpeg falhou ({cmd[0]}): {result.stderr[-500:]}")


class FfmpegAudioExtractor:
    """Extrai a faixa de áudio para WAV mono 16 kHz (formato esperado pelo Whisper)."""

    def extract(self, video_path: Path, out_wav: Path) -> Path:
        out_wav.parent.mkdir(parents=True, exist_ok=True)
        _run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                str(out_wav),
            ]
        )
        return out_wav


def normalize_video(video_path: Path, out_path: Path, fps: int = 24) -> Path:
    """Força CFR de ``fps`` quadros e codec H.264 (questionário Q34)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        ["ffmpeg", "-y", "-i", str(video_path), "-r", str(fps), "-vcodec", "libx264", str(out_path)]
    )
    return out_path
