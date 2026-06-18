"""Heurísticas de sinais comportamentais (geométricas, sem IA pesada).

Sinais do MVP (questionário, Bloco 5):
- ``olhar_desviado``: cliente sem olhar para a tela por mais de N segundos consecutivos.
- ``afastamento_da_tela``: redução súbita do tamanho relativo da face.
- ``aceno_cabeca_positivo`` / ``aceno_cabeca_negativo``: oscilação vertical / horizontal da cabeça.

As funções operam sobre uma lista ordenada de ``FrameMetrics`` e são puras/determinísticas.
"""

from itertools import pairwise
from statistics import mean

from app.core.types import FrameMetrics, SignalEvent

SCHEMA_VERSION = 1

# Limiares (ajustáveis). Mantidos explícitos para facilitar tuning e teste.
GAZE_AWAY_MIN_SECONDS = 3.0
WITHDRAW_DROP_RATIO = 0.30  # queda >30% do tamanho da face vs baseline recente
WITHDRAW_BASELINE_FRAMES = 5
NOD_WINDOW_FRAMES = 6
NOD_VERTICAL_AMPLITUDE = 0.08  # amplitude normalizada do centro vertical da face
SHAKE_HORIZONTAL_AMPLITUDE = 0.08
DIRECTION_REVERSALS_MIN = 2

SIGNAL_GAZE_AWAY = "olhar_desviado"
SIGNAL_WITHDRAW = "afastamento_da_tela"
SIGNAL_NOD_POSITIVE = "aceno_cabeca_positivo"
SIGNAL_NOD_NEGATIVE = "aceno_cabeca_negativo"


def _count_reversals(values: list[float]) -> int:
    """Conta inversões de direção (picos/vales) numa série."""
    reversals = 0
    prev_sign = 0
    for earlier, later in pairwise(values):
        delta = later - earlier
        sign = (delta > 0) - (delta < 0)
        if sign != 0 and prev_sign != 0 and sign != prev_sign:
            reversals += 1
        if sign != 0:
            prev_sign = sign
    return reversals


def detect_gaze_away(frames: list[FrameMetrics]) -> list[SignalEvent]:
    """Emite um evento por sequência contínua de frames com olhar desviado >= limiar."""
    events: list[SignalEvent] = []
    run: list[FrameMetrics] = []

    def flush(run_frames: list[FrameMetrics]) -> None:
        if not run_frames:
            return
        duration_s = (run_frames[-1].timestamp_ms - run_frames[0].timestamp_ms) / 1000.0
        if duration_s >= GAZE_AWAY_MIN_SECONDS:
            events.append(
                SignalEvent(
                    timestamp_ms=run_frames[0].timestamp_ms,
                    signal_type=SIGNAL_GAZE_AWAY,
                    confidence=round(mean(f.confidence for f in run_frames), 3),
                    meta={
                        "duration_seconds": round(duration_s, 2),
                        "frames_triggered": len(run_frames),
                    },
                    source="mediapipe_mesh_v1_eye_tracking",
                )
            )

    for frame in frames:
        if frame.looking_at_screen:
            flush(run)
            run = []
        else:
            run.append(frame)
    flush(run)
    return events


def detect_withdrawal(frames: list[FrameMetrics]) -> list[SignalEvent]:
    """Emite evento quando o tamanho da face cai abruptamente vs a baseline recente."""
    events: list[SignalEvent] = []
    for index in range(WITHDRAW_BASELINE_FRAMES, len(frames)):
        window = frames[index - WITHDRAW_BASELINE_FRAMES : index]
        baseline = mean(f.face_size_ratio for f in window)
        current = frames[index].face_size_ratio
        if baseline > 0 and current < baseline * (1 - WITHDRAW_DROP_RATIO):
            events.append(
                SignalEvent(
                    timestamp_ms=frames[index].timestamp_ms,
                    signal_type=SIGNAL_WITHDRAW,
                    confidence=frames[index].confidence,
                    meta={
                        "baseline_ratio": round(baseline, 3),
                        "current_ratio": round(current, 3),
                    },
                    source="mediapipe_mesh_v1_face_box",
                )
            )
    return events


def detect_head_gestures(frames: list[FrameMetrics]) -> list[SignalEvent]:
    """Detecta aceno (vertical) e negativa (horizontal) por amplitude + inversões na janela."""
    events: list[SignalEvent] = []
    window = NOD_WINDOW_FRAMES
    index = 0
    while index + window <= len(frames):
        chunk = frames[index : index + window]
        ys = [f.face_center_y for f in chunk]
        xs = [f.face_center_x for f in chunk]
        y_amp = max(ys) - min(ys)
        x_amp = max(xs) - min(xs)

        if y_amp >= NOD_VERTICAL_AMPLITUDE and _count_reversals(ys) >= DIRECTION_REVERSALS_MIN:
            events.append(
                SignalEvent(
                    timestamp_ms=chunk[0].timestamp_ms,
                    signal_type=SIGNAL_NOD_POSITIVE,
                    confidence=round(mean(f.confidence for f in chunk), 3),
                    meta={"amplitude": round(y_amp, 3)},
                    source="mediapipe_mesh_v1_head_pose",
                )
            )
            index += window
            continue
        if x_amp >= SHAKE_HORIZONTAL_AMPLITUDE and _count_reversals(xs) >= DIRECTION_REVERSALS_MIN:
            events.append(
                SignalEvent(
                    timestamp_ms=chunk[0].timestamp_ms,
                    signal_type=SIGNAL_NOD_NEGATIVE,
                    confidence=round(mean(f.confidence for f in chunk), 3),
                    meta={"amplitude": round(x_amp, 3)},
                    source="mediapipe_mesh_v1_head_pose",
                )
            )
            index += window
            continue
        index += 1
    return events


def detect_signals(frames: list[FrameMetrics]) -> list[SignalEvent]:
    """Roda todas as heurísticas e devolve os eventos ordenados por tempo."""
    events: list[SignalEvent] = []
    events.extend(detect_gaze_away(frames))
    events.extend(detect_withdrawal(frames))
    events.extend(detect_head_gestures(frames))
    events.sort(key=lambda event: event.timestamp_ms)
    return events
