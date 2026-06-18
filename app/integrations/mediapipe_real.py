"""Análise facial real com MediaPipe Face Mesh (instanciado por job)."""

from pathlib import Path
from typing import Any

from app.core.signals import detect_signals
from app.core.types import FrameMetrics, SignalEvent
from app.integrations.frames_cv2 import iter_frames

# Índices aproximados de landmarks do Face Mesh usados nas heurísticas geométricas.
_LEFT_EYE = 33
_RIGHT_EYE = 263
_NOSE_TIP = 1


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
                metric = self._to_metrics(result, timestamp_ms)
                if metric is not None:
                    metrics.append(metric)
        finally:
            face_mesh.close()
        return detect_signals(metrics)

    def _to_metrics(self, result: Any, timestamp_ms: int) -> FrameMetrics | None:
        landmarks = getattr(result, "multi_face_landmarks", None)
        if not landmarks:
            return None
        points = landmarks[0].landmark
        nose = points[_NOSE_TIP]
        left_eye = points[_LEFT_EYE]
        right_eye = points[_RIGHT_EYE]
        eye_span = abs(right_eye.x - left_eye.x)
        gaze_centered = abs(nose.x - 0.5) < 0.2 and abs(nose.y - 0.5) < 0.25
        return FrameMetrics(
            timestamp_ms=timestamp_ms,
            looking_at_screen=gaze_centered,
            face_size_ratio=eye_span,
            face_center_x=float(nose.x),
            face_center_y=float(nose.y),
            confidence=1.0,
        )
