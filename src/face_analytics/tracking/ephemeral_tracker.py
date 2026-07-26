"""Deterministic geometry-only tracking with explicit expiration."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from time import monotonic

from face_analytics.detection.base import BoundingBox, Detection


@dataclass(frozen=True, slots=True)
class TrackSnapshot:
    """Minimal volatile track data exposed to the in-memory aggregator."""

    temporary_id: int
    first_seen_monotonic: float
    position: tuple[float, float]
    last_seen_monotonic: float
    active: bool


@dataclass(frozen=True, slots=True)
class TrackerUpdate:
    """Active and newly expired tracks for one frame boundary."""

    active: tuple[TrackSnapshot, ...]
    expired: tuple[TrackSnapshot, ...]


@dataclass(slots=True)
class _TrackState:
    temporary_id: int
    first_seen: float
    last_seen: float
    box: BoundingBox
    missed_frames: int = 0

    def snapshot(self, *, active: bool) -> TrackSnapshot:
        return TrackSnapshot(
            temporary_id=self.temporary_id,
            first_seen_monotonic=self.first_seen,
            position=self.box.centroid,
            last_seen_monotonic=self.last_seen,
            active=active,
        )


class EphemeralTracker:
    """Track detections by geometry within one process session only."""

    def __init__(
        self,
        *,
        max_missed_frames: int = 5,
        timeout_seconds: float = 2.0,
        max_centroid_distance: float = 80.0,
        minimum_iou: float = 0.05,
    ) -> None:
        if max_missed_frames < 0:
            raise ValueError("max_missed_frames must be non-negative")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_centroid_distance <= 0:
            raise ValueError("max_centroid_distance must be positive")
        if not 0.0 <= minimum_iou <= 1.0:
            raise ValueError("minimum_iou must be between zero and one")
        self._max_missed_frames = max_missed_frames
        self._timeout_seconds = timeout_seconds
        self._max_centroid_distance = max_centroid_distance
        self._minimum_iou = minimum_iou
        self._tracks: dict[int, _TrackState] = {}
        self._next_id = 1
        self._last_update_time: float | None = None

    def update(
        self, detections: tuple[Detection, ...], *, now: float | None = None
    ) -> TrackerUpdate:
        timestamp = monotonic() if now is None else now
        if timestamp < 0:
            raise ValueError("monotonic timestamp must be non-negative")
        if self._last_update_time is not None and timestamp < self._last_update_time:
            raise ValueError("monotonic timestamp cannot move backwards")
        self._last_update_time = timestamp

        unmatched_tracks = set(self._tracks)
        unmatched_detections = set(range(len(detections)))
        candidates: list[tuple[float, float, int, int]] = []
        for track_id, state in self._tracks.items():
            for detection_index, detection in enumerate(detections):
                distance = _centroid_distance(state.box, detection.box)
                overlap = _iou(state.box, detection.box)
                if (
                    distance <= self._max_centroid_distance
                    and overlap >= self._minimum_iou
                ):
                    candidates.append((-overlap, distance, track_id, detection_index))

        for _negative_overlap, _distance, track_id, detection_index in sorted(
            candidates
        ):
            if (
                track_id not in unmatched_tracks
                or detection_index not in unmatched_detections
            ):
                continue
            state = self._tracks[track_id]
            state.box = detections[detection_index].box
            state.last_seen = timestamp
            state.missed_frames = 0
            unmatched_tracks.remove(track_id)
            unmatched_detections.remove(detection_index)

        for detection_index in sorted(unmatched_detections):
            track_id = self._next_id
            self._next_id += 1
            self._tracks[track_id] = _TrackState(
                temporary_id=track_id,
                first_seen=timestamp,
                last_seen=timestamp,
                box=detections[detection_index].box,
            )

        expired: list[TrackSnapshot] = []
        for track_id in sorted(unmatched_tracks):
            state = self._tracks[track_id]
            state.missed_frames += 1
            timed_out = timestamp - state.last_seen >= self._timeout_seconds
            missed_out = state.missed_frames > self._max_missed_frames
            if timed_out or missed_out:
                expired.append(state.snapshot(active=False))
                del self._tracks[track_id]

        active = tuple(
            self._tracks[track_id].snapshot(active=True)
            for track_id in sorted(self._tracks)
        )
        return TrackerUpdate(active=active, expired=tuple(expired))

    def reset(self) -> tuple[TrackSnapshot, ...]:
        """Destroy all track state and start a fresh process-local ID sequence."""

        destroyed = tuple(
            self._tracks[track_id].snapshot(active=False)
            for track_id in sorted(self._tracks)
        )
        self._tracks.clear()
        self._next_id = 1
        self._last_update_time = None
        return destroyed

    @property
    def active_count(self) -> int:
        return len(self._tracks)


def _centroid_distance(first: BoundingBox, second: BoundingBox) -> float:
    first_x, first_y = first.centroid
    second_x, second_y = second.centroid
    return hypot(first_x - second_x, first_y - second_y)


def _iou(first: BoundingBox, second: BoundingBox) -> float:
    left = max(first.x, second.x)
    top = max(first.y, second.y)
    right = min(first.right, second.right)
    bottom = min(first.bottom, second.bottom)
    intersection = max(0, right - left) * max(0, bottom - top)
    if intersection == 0:
        return 0.0
    union = first.width * first.height + second.width * second.height - intersection
    return intersection / union
