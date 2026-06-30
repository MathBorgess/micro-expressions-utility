"""Testes dos tipos de domínio enriquecidos."""

from app.core.types import FrameMetrics


def test_frame_metrics_optional_fields_default() -> None:
    m = FrameMetrics(
        timestamp_ms=0,
        looking_at_screen=True,
        face_size_ratio=0.1,
        face_center_x=0.5,
        face_center_y=0.5,
    )
    assert m.quality_score == 1.0
    assert m.head_yaw_deg == 0.0
    assert m.head_pitch_deg == 0.0
    assert m.gaze_offset_x == 0.0
