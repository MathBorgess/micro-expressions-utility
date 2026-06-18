"""Conversão de tempo a partir de metadados de vídeo.

Fonte oficial do timestamp: tempo do vídeo em milissegundos.
Fórmula: Timestamp(ms) = (Frame Index / FPS) * 1000.
"""


def frame_to_ms(frame_index: int, fps: float) -> float:
    """Converte um índice de frame em timestamp absoluto (ms) usando o FPS nativo."""
    if fps <= 0:
        raise ValueError("fps deve ser > 0")
    if frame_index < 0:
        raise ValueError("frame_index deve ser >= 0")
    return (frame_index / fps) * 1000.0


def ms_to_timestamp(ms: float) -> str:
    """Formata milissegundos como `HH:MM:SS` (formato da timeline)."""
    if ms < 0:
        raise ValueError("ms deve ser >= 0")
    total_seconds = int(ms // 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
