"""In-memory frame sources with explicit lifecycle management."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Protocol

import cv2

from face_analytics.detection.base import Frame


class FrameSourceError(RuntimeError):
    """Raised when a requested camera or video source cannot be opened."""


class FrameSource(Protocol):
    def read(self) -> Frame | None:
        """Return the next in-memory frame or None at end of stream."""

    def close(self) -> None:
        """Release the source without writing frames."""


class OpenCVFrameSource:
    """Base source backed by cv2.VideoCapture."""

    def __init__(self, source: int | str) -> None:
        self._capture = cv2.VideoCapture(source)
        if not self._capture.isOpened():
            self._capture.release()
            raise FrameSourceError(f"unable to open frame source: {source}")

    def read(self) -> Frame | None:
        ok, frame = self._capture.read()
        if not ok or frame is None:
            return None
        return frame

    def close(self) -> None:
        self._capture.release()

    def __enter__(self) -> OpenCVFrameSource:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()


class WebcamFrameSource(OpenCVFrameSource):
    """Consented webcam input processed in memory."""

    def __init__(self, camera_index: int = 0) -> None:
        if camera_index < 0:
            raise ValueError("camera_index must be non-negative")
        super().__init__(camera_index)


class VideoFrameSource(OpenCVFrameSource):
    """Explicit local video input; this class never copies or saves frames."""

    def __init__(self, path: Path) -> None:
        if not path.is_file():
            raise FrameSourceError(f"video file does not exist: {path}")
        super().__init__(str(path))


class IterableFrameSource:
    """Deterministic source for tests and generated frames."""

    def __init__(self, frames: Iterable[Frame]) -> None:
        self._frames: Iterator[Frame] = iter(frames)
        self._closed = False

    def read(self) -> Frame | None:
        if self._closed:
            return None
        return next(self._frames, None)

    def close(self) -> None:
        self._closed = True
