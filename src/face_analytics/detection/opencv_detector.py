"""Bundled OpenCV fallback for environments without MediaPipe wheels."""

from __future__ import annotations

from pathlib import Path

import cv2

from face_analytics.detection.base import (
    BoundingBox,
    Detection,
    Frame,
    RelativeBox,
)
from face_analytics.detection.mediapipe_detector import _validate_frame


class OpenCVHaarDetector:
    """Lightweight local fallback using OpenCV's bundled frontal-face cascade."""

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        *,
        cascade_path: Path | None = None,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between zero and one")
        path = cascade_path or (
            Path(cv2.data.haarcascades)  # type: ignore[attr-defined]
            / "haarcascade_frontalface_default.xml"
        )
        self._cascade = cv2.CascadeClassifier(str(path))
        if self._cascade.empty():
            raise RuntimeError(f"unable to load OpenCV cascade: {path}")
        self._confidence_threshold = confidence_threshold

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        height, width = _validate_frame(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes, _reject_levels, weights = self._cascade.detectMultiScale3(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(24, 24),
            outputRejectLevels=True,
        )
        output: list[Detection] = []
        for raw_box, raw_weight in zip(boxes, weights, strict=True):
            x, y, box_width, box_height = (int(value) for value in raw_box)
            confidence = max(0.0, min(1.0, float(raw_weight) / 10.0))
            if confidence < self._confidence_threshold:
                continue
            output.append(
                Detection(
                    box=BoundingBox(x, y, box_width, box_height),
                    confidence=confidence,
                    relative_box=RelativeBox(
                        x / width,
                        y / height,
                        box_width / width,
                        box_height / height,
                    ),
                )
            )
        return tuple(output)

    def close(self) -> None:
        """OpenCV's cascade classifier has no external resource to release."""
