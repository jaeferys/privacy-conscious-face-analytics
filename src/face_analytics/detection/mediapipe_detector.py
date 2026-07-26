"""MediaPipe face detector with lazy optional dependency loading."""

from __future__ import annotations

from typing import Any, Protocol, cast

import cv2

from face_analytics.detection.base import (
    BoundingBox,
    Detection,
    Frame,
    RelativeBox,
)


class MediaPipeUnavailableError(RuntimeError):
    """Raised when MediaPipe cannot run on the active interpreter."""


class _MediaPipeBackend(Protocol):
    def process(self, image: Frame) -> Any:
        """Return a MediaPipe-compatible result object."""

    def close(self) -> None:
        """Release backend resources."""


class MediaPipeDetector:
    """In-memory MediaPipe detector returning identity-free geometry only."""

    def __init__(
        self,
        confidence_threshold: float = 0.5,
        model_selection: int = 0,
        *,
        backend: _MediaPipeBackend | None = None,
    ) -> None:
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between zero and one")
        if model_selection not in (0, 1):
            raise ValueError("model_selection must be 0 or 1")
        self._confidence_threshold = confidence_threshold
        self._backend = backend or self._load_backend(
            confidence_threshold, model_selection
        )

    @staticmethod
    def _load_backend(
        confidence_threshold: float, model_selection: int
    ) -> _MediaPipeBackend:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise MediaPipeUnavailableError(
                "MediaPipe is unavailable on this interpreter. Use Python 3.11/3.12 "
                "or select the OpenCV fallback."
            ) from exc

        solutions = getattr(mp, "solutions", None)
        if solutions is None or not hasattr(solutions, "face_detection"):
            raise MediaPipeUnavailableError(
                "This MediaPipe build does not expose solutions.face_detection."
            )
        return cast(
            "_MediaPipeBackend",
            solutions.face_detection.FaceDetection(
                model_selection=model_selection,
                min_detection_confidence=confidence_threshold,
            ),
        )

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        height, width = _validate_frame(frame)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self._backend.process(rgb)
        output: list[Detection] = []
        for raw in getattr(result, "detections", None) or ():
            scores = getattr(raw, "score", ())
            confidence = float(scores[0]) if scores else 0.0
            if confidence < self._confidence_threshold:
                continue
            location = raw.location_data.relative_bounding_box
            relative = _clamp_relative_box(
                float(location.xmin),
                float(location.ymin),
                float(location.width),
                float(location.height),
            )
            output.append(
                Detection(
                    box=_absolute_box(relative, width, height),
                    confidence=confidence,
                    relative_box=relative,
                )
            )
        return tuple(output)

    def close(self) -> None:
        self._backend.close()


def _validate_frame(frame: Frame) -> tuple[int, int]:
    if frame.ndim != 3:
        raise ValueError("frame must be a three-dimensional BGR image")
    height, width, channels = frame.shape
    if height <= 0 or width <= 0 or channels != 3:
        raise ValueError("frame must have positive dimensions and three BGR channels")
    return height, width


def _clamp_relative_box(x: float, y: float, width: float, height: float) -> RelativeBox:
    left = min(max(x, 0.0), 1.0)
    top = min(max(y, 0.0), 1.0)
    right = min(max(x + width, left), 1.0)
    bottom = min(max(y + height, top), 1.0)
    if right <= left or bottom <= top:
        raise ValueError("detector returned an empty bounding box")
    return RelativeBox(left, top, right - left, bottom - top)


def _absolute_box(relative: RelativeBox, width: int, height: int) -> BoundingBox:
    x = min(int(relative.x * width), width - 1)
    y = min(int(relative.y * height), height - 1)
    right = max(x + 1, min(round((relative.x + relative.width) * width), width))
    bottom = max(y + 1, min(round((relative.y + relative.height) * height), height))
    return BoundingBox(x=x, y=y, width=right - x, height=bottom - y)
