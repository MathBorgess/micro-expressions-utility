"""Testes de _to_metrics do MediaPipe com landmarks fake (sem vídeo real)."""

from types import SimpleNamespace

import numpy as np

from app.integrations.mediapipe_real import MediaPipeFaceAnalyzer


class _Pt:
    def __init__(self, x: float, y: float, z: float = 0.0) -> None:
        self.x, self.y, self.z = x, y, z


def _fake_landmarks(
    *,
    nose: tuple[float, float] = (0.52, 0.48),
    left_eye: tuple[float, float] = (0.40, 0.45),
    right_eye: tuple[float, float] = (0.60, 0.45),
    left_iris: tuple[float, float] = (0.42, 0.46),
    right_iris: tuple[float, float] = (0.58, 0.46),
) -> list[_Pt]:
    points = [_Pt(0.5, 0.5) for _ in range(478)]
    points[1] = _Pt(*nose)
    points[33] = _Pt(*left_eye)
    points[263] = _Pt(*right_eye)
    points[468] = _Pt(*left_iris)
    points[473] = _Pt(*right_iris)
    return points


def test_to_metrics_uses_variable_confidence() -> None:
    analyzer = MediaPipeFaceAnalyzer()
    points = _fake_landmarks()
    result = SimpleNamespace(multi_face_landmarks=[SimpleNamespace(landmark=points)])
    metric = analyzer._to_metrics(result, timestamp_ms=1000, frame_bgr=None)
    assert metric is not None
    assert metric.confidence <= 1.0
    assert hasattr(metric, "gaze_offset_x")


def test_to_metrics_centered_gaze_looks_at_screen() -> None:
    analyzer = MediaPipeFaceAnalyzer()
    points = _fake_landmarks()
    result = SimpleNamespace(multi_face_landmarks=[SimpleNamespace(landmark=points)])
    metric = analyzer._to_metrics(result, timestamp_ms=500, frame_bgr=None)
    assert metric is not None
    assert abs(metric.gaze_offset_x) < 0.08
    assert abs(metric.head_yaw_deg) < 15.0
    assert metric.looking_at_screen is True


def test_to_metrics_large_gaze_offset_not_looking() -> None:
    analyzer = MediaPipeFaceAnalyzer()
    points = _fake_landmarks(left_iris=(0.30, 0.46), right_iris=(0.46, 0.46))
    result = SimpleNamespace(multi_face_landmarks=[SimpleNamespace(landmark=points)])
    metric = analyzer._to_metrics(result, timestamp_ms=500, frame_bgr=None)
    assert metric is not None
    assert abs(metric.gaze_offset_x) >= 0.08
    assert metric.looking_at_screen is False


def test_to_metrics_uses_frame_quality_when_frame_available() -> None:
    analyzer = MediaPipeFaceAnalyzer()
    points = _fake_landmarks()
    result = SimpleNamespace(multi_face_landmarks=[SimpleNamespace(landmark=points)])
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    metric = analyzer._to_metrics(result, timestamp_ms=1000, frame_bgr=frame)
    assert metric is not None
    assert 0.0 <= metric.quality_score <= 1.0
    assert metric.confidence <= metric.quality_score


def test_to_metrics_returns_none_without_landmarks() -> None:
    analyzer = MediaPipeFaceAnalyzer()
    result = SimpleNamespace(multi_face_landmarks=None)
    assert analyzer._to_metrics(result, timestamp_ms=0, frame_bgr=None) is None
