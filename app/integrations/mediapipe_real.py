"""Análise facial real com MediaPipe Face Mesh (instanciado por job)."""

from pathlib import Path
from typing import Any

import numpy as np

from app.core.face_quality import score_frame_quality
from app.core.signals import detect_signals
from app.core.types import FrameMetrics, SignalEvent
from app.integrations.frames_cv2 import iter_frames

# Índices aproximados de landmarks do Face Mesh usados nas heurísticas geométricas.
_LEFT_EYE = 33
_RIGHT_EYE = 263
_NOSE_TIP = 1
_LEFT_IRIS = 468
_RIGHT_IRIS = 473
_KEY_LANDMARKS = (_NOSE_TIP, _LEFT_EYE, _RIGHT_EYE, _LEFT_IRIS, _RIGHT_IRIS)
_YAW_SCALE_DEG = 45.0
_PITCH_SCALE_DEG = 45.0
_EMA_ALPHA = 0.3


def _landmark_visibility(points: list[Any]) -> float:
    """Estabilidade de tracking a partir da profundidade relativa dos landmarks-chave."""
    scores: list[float] = []
    for index in _KEY_LANDMARKS:
        z = abs(float(getattr(points[index], "z", 0.0)))
        scores.append(max(0.0, 1.0 - z * 2.0))
    return sum(scores) / len(scores)


def _head_yaw_deg(nose: Any, left_eye: Any, right_eye: Any) -> float:
    """Aproximação de yaw pela assimetria das distâncias olho-nariz."""
    dist_left = abs(float(nose.x) - float(left_eye.x))
    dist_right = abs(float(right_eye.x) - float(nose.x))
    total = dist_left + dist_right
    if total <= 1e-9:
        return 0.0
    asymmetry = (dist_right - dist_left) / total
    return asymmetry * _YAW_SCALE_DEG


def _head_pitch_deg(nose: Any, left_eye: Any, right_eye: Any) -> float:
    """Aproximação de pitch pela posição vertical do nariz vs centro dos olhos."""
    eye_center_y = (float(left_eye.y) + float(right_eye.y)) / 2.0
    pitch_offset = float(nose.y) - eye_center_y
    return pitch_offset * _PITCH_SCALE_DEG


def _ema_smooth(prev: float, current: float, alpha: float = _EMA_ALPHA) -> float:
    return alpha * current + (1.0 - alpha) * prev


def _apply_ema_to_metrics(metrics: list[FrameMetrics]) -> list[FrameMetrics]:
    """Suaviza métricas espaciais frame-a-frame para reduzir jitter de landmarks."""
    if not metrics:
        return metrics
    smoothed: list[FrameMetrics] = []
    prev = metrics[0]
    smoothed.append(prev)
    for current in metrics[1:]:
        prev = FrameMetrics(
            timestamp_ms=current.timestamp_ms,
            looking_at_screen=current.looking_at_screen,
            face_size_ratio=current.face_size_ratio,
            face_center_x=_ema_smooth(prev.face_center_x, current.face_center_x),
            face_center_y=_ema_smooth(prev.face_center_y, current.face_center_y),
            confidence=current.confidence,
            quality_score=current.quality_score,
            head_yaw_deg=current.head_yaw_deg,
            head_pitch_deg=current.head_pitch_deg,
            gaze_offset_x=_ema_smooth(prev.gaze_offset_x, current.gaze_offset_x),
            gaze_offset_y=_ema_smooth(prev.gaze_offset_y, current.gaze_offset_y),
        )
        smoothed.append(prev)
    return smoothed


class MediaPipeFaceAnalyzer:
    """Extrai métricas por frame via Face Mesh e aplica as heurísticas de sinais."""

    def analyze(self, video_path: Path) -> list[SignalEvent]:
        import cv2
        import mediapipe as mp

        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False, max_num_faces=1, refine_landmarks=True
        )
        metrics: list[FrameMetrics] = []
        try:
            for timestamp_ms, frame in iter_frames(video_path):
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                result = face_mesh.process(rgb)
                metric = self._to_metrics(result, timestamp_ms, frame_bgr=frame)
                if metric is not None:
                    metrics.append(metric)
        finally:
            face_mesh.close()
        return detect_signals(_apply_ema_to_metrics(metrics))

    def _to_metrics(
        self,
        result: Any,
        timestamp_ms: int,
        frame_bgr: np.ndarray | None = None,
    ) -> FrameMetrics | None:
        landmarks = getattr(result, "multi_face_landmarks", None)
        if not landmarks:
            return None
        points = landmarks[0].landmark
        if len(points) <= _RIGHT_IRIS:
            return None

        nose = points[_NOSE_TIP]
        left_eye = points[_LEFT_EYE]
        right_eye = points[_RIGHT_EYE]
        left_iris = points[_LEFT_IRIS]
        right_iris = points[_RIGHT_IRIS]

        eye_center_x = (float(left_eye.x) + float(right_eye.x)) / 2.0
        eye_center_y = (float(left_eye.y) + float(right_eye.y)) / 2.0
        iris_center_x = (float(left_iris.x) + float(right_iris.x)) / 2.0
        iris_center_y = (float(left_iris.y) + float(right_iris.y)) / 2.0

        gaze_offset_x = iris_center_x - eye_center_x
        gaze_offset_y = iris_center_y - eye_center_y
        head_yaw_deg = _head_yaw_deg(nose, left_eye, right_eye)
        head_pitch_deg = _head_pitch_deg(nose, left_eye, right_eye)
        looking_at_screen = abs(gaze_offset_x) < 0.08 and abs(head_yaw_deg) < 15.0

        eye_span = abs(float(right_eye.x) - float(left_eye.x))
        tracking_stability = _landmark_visibility(points)

        if frame_bgr is not None:
            height, width = frame_bgr.shape[:2]
            xs = [float(p.x) * width for p in points]
            ys = [float(p.y) * height for p in points]
            face_bbox = (int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys)))
            quality_score = score_frame_quality(frame_bgr, face_bbox, tracking_stability)
        else:
            quality_score = 1.0

        confidence = round(quality_score * tracking_stability, 3)

        return FrameMetrics(
            timestamp_ms=timestamp_ms,
            looking_at_screen=looking_at_screen,
            face_size_ratio=eye_span,
            face_center_x=float(nose.x),
            face_center_y=float(nose.y),
            confidence=confidence,
            quality_score=quality_score,
            head_yaw_deg=head_yaw_deg,
            head_pitch_deg=head_pitch_deg,
            gaze_offset_x=gaze_offset_x,
            gaze_offset_y=gaze_offset_y,
        )
