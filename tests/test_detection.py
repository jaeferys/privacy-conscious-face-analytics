"""Tests for identity-free in-memory detection."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from face_analytics.benchmark import benchmark_detector
from face_analytics.detection.base import (
    BoundingBox,
    Detection,
    RelativeBox,
)
from face_analytics.detection.mediapipe_detector import MediaPipeDetector
from face_analytics.frame_sources import IterableFrameSource, VideoFrameSource


class FakeBackend:
    def __init__(self, detections: list[object] | None = None) -> None:
        self.detections = detections or []
        self.closed = False

    def process(
        self, _image: np.ndarray[tuple[int, ...], np.dtype[np.uint8]]
    ) -> object:
        return SimpleNamespace(detections=self.detections)

    def close(self) -> None:
        self.closed = True


class FakeDetector:
    def detect(
        self, _frame: np.ndarray[tuple[int, ...], np.dtype[np.uint8]]
    ) -> tuple[Detection, ...]:
        return ()

    def close(self) -> None:
        return None


def _raw_detection(confidence: float = 0.9) -> object:
    box = SimpleNamespace(xmin=0.25, ymin=0.2, width=0.5, height=0.4)
    location = SimpleNamespace(relative_bounding_box=box)
    return SimpleNamespace(score=[confidence], location_data=location)


def test_detection_schema_has_no_identity_or_embedding_fields() -> None:
    names = {field.name for field in fields(Detection)}
    assert names == {"box", "confidence", "relative_box"}


def test_detection_validates_confidence_and_geometry() -> None:
    with pytest.raises(ValueError, match="confidence"):
        Detection(BoundingBox(0, 0, 10, 10), 1.1, RelativeBox(0, 0, 1, 1))
    with pytest.raises(ValueError, match="dimensions"):
        BoundingBox(0, 0, 0, 10)


def test_mediapipe_adapter_converts_relative_geometry() -> None:
    backend = FakeBackend([_raw_detection()])
    detector = MediaPipeDetector(backend=backend)
    frame = np.zeros((100, 200, 3), dtype=np.uint8)

    detections = detector.detect(frame)

    assert len(detections) == 1
    assert detections[0].box == BoundingBox(50, 20, 100, 40)
    assert detections[0].confidence == pytest.approx(0.9)
    assert detections[0].relative_box.x == pytest.approx(0.25)
    assert detections[0].relative_box.y == pytest.approx(0.2)
    assert detections[0].relative_box.width == pytest.approx(0.5)
    assert detections[0].relative_box.height == pytest.approx(0.4)
    detector.close()
    assert backend.closed


def test_mediapipe_adapter_rejects_malformed_frame() -> None:
    detector = MediaPipeDetector(backend=FakeBackend())
    with pytest.raises(ValueError, match="three-dimensional"):
        detector.detect(np.zeros((10, 10), dtype=np.uint8))


def test_iterable_source_is_memory_only_and_closes() -> None:
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    source = IterableFrameSource([frame])
    assert source.read() is frame
    assert source.read() is None
    source.close()
    assert source.read() is None


def test_missing_video_fails_cleanly(tmp_path: Path) -> None:
    path = tmp_path.joinpath("missing.mp4")
    with pytest.raises(RuntimeError, match="does not exist"):
        VideoFrameSource(path)


def test_benchmark_uses_substitutable_detector() -> None:
    frame = np.zeros((8, 8, 3), dtype=np.uint8)
    result = benchmark_detector(FakeDetector(), IterableFrameSource([frame, frame]), 2)
    assert result.frames == 2
    assert result.detections == 0
    assert result.frames_per_second > 0
