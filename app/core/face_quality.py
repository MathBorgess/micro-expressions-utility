# app/core/face_quality.py
"""Pontuação de qualidade de frame facial (0..1) para filtrar ruído de percepção."""

from collections.abc import Sequence

import cv2
import numpy as np

MIN_FACE_AREA_RATIO = 0.02
BLUR_VAR_LOW = 50.0
BLUR_VAR_HIGH = 400.0


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _blur_score(roi: np.ndarray) -> float:
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if variance <= BLUR_VAR_LOW:
        return 0.0
    if variance >= BLUR_VAR_HIGH:
        return 1.0
    return (variance - BLUR_VAR_LOW) / (BLUR_VAR_HIGH - BLUR_VAR_LOW)


def _size_score(bbox: Sequence[int], frame_shape: tuple[int, ...]) -> float:
    x1, y1, x2, y2 = bbox
    face_area = max(0, x2 - x1) * max(0, y2 - y1)
    frame_area = frame_shape[0] * frame_shape[1]
    if frame_area == 0:
        return 0.0
    ratio = face_area / frame_area
    if ratio < MIN_FACE_AREA_RATIO:
        return ratio / MIN_FACE_AREA_RATIO * 0.5
    return _clamp(ratio / 0.15)


def score_frame_quality(
    frame_bgr: np.ndarray,
    face_bbox: tuple[int, int, int, int],
    landmark_visibility: float,
) -> float:
    x1, y1, x2, y2 = face_bbox
    h, w = frame_bgr.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    roi = frame_bgr[y1:y2, x1:x2]
    blur = _blur_score(roi)
    size = _size_score((x1, y1, x2, y2), (h, w))
    visibility = _clamp(landmark_visibility)
    return round(_clamp(blur * 0.4 + size * 0.35 + visibility * 0.25), 3)
