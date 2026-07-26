"""End-to-end volatile frame processing into aggregate-only storage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic

from face_analytics.analytics import AggregateAnalytics, PolygonZone
from face_analytics.detection.base import FaceDetector
from face_analytics.frame_sources import FrameSource
from face_analytics.storage import AggregateStore
from face_analytics.tracking import EphemeralTracker, TrackerUpdate


@dataclass(frozen=True, slots=True)
class PipelineResult:
    frames_processed: int
    detections_processed: int
    aggregate_row_id: int | None


def run_pipeline(
    *,
    detector: FaceDetector,
    source: FrameSource,
    tracker: EphemeralTracker,
    store: AggregateStore,
    max_frames: int,
    window_seconds: int = 300,
    heatmap_rows: int = 12,
    heatmap_columns: int = 16,
    zones: tuple[PolygonZone, ...] = (),
    monotonic_clock: Callable[[], float] = monotonic,
    utc_clock: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> PipelineResult:
    """Process frames in memory and persist one final aggregate window."""

    if max_frames <= 0:
        raise ValueError("max_frames must be positive")
    store.initialize()
    analytics: AggregateAnalytics | None = None
    frames_processed = 0
    detections_processed = 0
    window_start = utc_clock()
    while frames_processed < max_frames:
        frame = source.read()
        if frame is None:
            break
        if analytics is None:
            height, width = frame.shape[:2]
            analytics = AggregateAnalytics(
                frame_width=width,
                frame_height=height,
                window_seconds=window_seconds,
                heatmap_rows=heatmap_rows,
                heatmap_columns=heatmap_columns,
                zones=zones,
            )
        now = monotonic_clock()
        detections = detector.detect(frame)
        update = tracker.update(detections, now=now)
        analytics.observe(update, now_monotonic=now)
        frames_processed += 1
        detections_processed += len(detections)
        del frame

    if analytics is None:
        return PipelineResult(0, 0, None)
    destroyed = tracker.reset()
    final_time = max(
        (track.last_seen_monotonic for track in destroyed),
        default=monotonic_clock(),
    )
    analytics.observe(
        TrackerUpdate(active=(), expired=destroyed), now_monotonic=final_time
    )
    record = analytics.snapshot_and_reset(window_start=window_start)
    return PipelineResult(
        frames_processed=frames_processed,
        detections_processed=detections_processed,
        aggregate_row_id=store.save(record),
    )
