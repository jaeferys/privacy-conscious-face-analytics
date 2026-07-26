"""End-to-end volatile pipeline test using generated frames."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from face_analytics.detection.base import BoundingBox, Detection, RelativeBox
from face_analytics.frame_sources import IterableFrameSource
from face_analytics.pipeline import run_pipeline
from face_analytics.storage import AggregateStore
from face_analytics.tracking import EphemeralTracker


class MovingFakeDetector:
    def __init__(self) -> None:
        self.index = 0

    def detect(
        self, _frame: np.ndarray[tuple[int, ...], np.dtype[np.uint8]]
    ) -> tuple[Detection, ...]:
        x = 10 + self.index * 2
        self.index += 1
        return (
            Detection(
                BoundingBox(x, 10, 20, 20),
                0.9,
                RelativeBox(x / 100, 0.1, 0.2, 0.2),
            ),
        )

    def close(self) -> None:
        return None


def test_pipeline_discards_frames_and_persists_one_aggregate_window(
    tmp_path: Path,
) -> None:
    frames = [np.zeros((100, 100, 3), dtype=np.uint8) for _ in range(3)]
    source = IterableFrameSource(frames)
    store = AggregateStore(tmp_path / "analytics.sqlite3")
    ticks = iter((0.0, 1.0, 2.0, 3.0))

    result = run_pipeline(
        detector=MovingFakeDetector(),
        source=source,
        tracker=EphemeralTracker(max_centroid_distance=30, minimum_iou=0.1),
        store=store,
        max_frames=3,
        monotonic_clock=lambda: next(ticks),
        utc_clock=lambda: datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert result.frames_processed == 3
    assert result.detections_processed == 3
    assert result.aggregate_row_id == 1
    stored = store.list_recent()[0].record
    assert stored.entries == 1
    assert stored.exits == 1
    assert stored.dwell_count == 1
    assert stored.dwell_total_seconds == 2
    assert stored.data_source == "observed"
    assert not any("track" in column for column in store.aggregate_columns())


def test_pipeline_handles_empty_source_without_persisting(tmp_path: Path) -> None:
    result = run_pipeline(
        detector=MovingFakeDetector(),
        source=IterableFrameSource([]),
        tracker=EphemeralTracker(),
        store=AggregateStore(tmp_path / "empty.sqlite3"),
        max_frames=3,
    )
    assert result.aggregate_row_id is None
    assert result.frames_processed == 0
