# tests/unit/test_face_quality.py
"""Testes de pontuação de qualidade facial por frame."""

import numpy as np

from app.core.face_quality import score_frame_quality


def test_high_quality_sharp_large_face() -> None:
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    frame[100:300, 200:440] = np.random.randint(0, 255, (200, 240, 3), dtype=np.uint8)
    result = score_frame_quality(
        frame_bgr=frame,
        face_bbox=(200, 100, 440, 300),
        landmark_visibility=1.0,
    )
    assert 0.0 <= result <= 1.0
    assert result >= 0.4


def test_low_quality_tiny_face() -> None:
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = score_frame_quality(
        frame_bgr=frame,
        face_bbox=(300, 220, 320, 240),
        landmark_visibility=0.5,
    )
    assert result < 0.5


def test_blurry_frame_lower_than_sharp() -> None:
    sharp = np.random.randint(0, 255, (120, 120, 3), dtype=np.uint8)
    blurry = np.full((120, 120, 3), 128, dtype=np.uint8)
    bbox = (10, 10, 110, 110)
    assert score_frame_quality(sharp, bbox, 1.0) > score_frame_quality(blurry, bbox, 1.0)
