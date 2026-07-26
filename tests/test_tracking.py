"""Tests proving tracking is ephemeral geometry association, not identity."""

from __future__ import annotations

from dataclasses import fields

import pytest

from face_analytics.detection.base import BoundingBox, Detection, RelativeBox
from face_analytics.tracking import EphemeralTracker, TrackSnapshot


def detection(x: int, y: int, width: int = 20, height: int = 20) -> Detection:
    return Detection(
        box=BoundingBox(x, y, width, height),
        confidence=0.9,
        relative_box=RelativeBox(x / 200, y / 200, width / 200, height / 200),
    )


def test_track_schema_is_minimal_and_identity_free() -> None:
    assert {field.name for field in fields(TrackSnapshot)} == {
        "temporary_id",
        "first_seen_monotonic",
        "position",
        "last_seen_monotonic",
        "active",
    }


def test_creates_and_matches_track_across_adjacent_frames() -> None:
    tracker = EphemeralTracker(max_centroid_distance=30, minimum_iou=0.1)
    first = tracker.update((detection(10, 10),), now=1.0)
    second = tracker.update((detection(14, 12),), now=1.1)

    assert first.active[0].temporary_id == 1
    assert second.active[0].temporary_id == 1
    assert second.active[0].first_seen_monotonic == 1.0
    assert second.active[0].last_seen_monotonic == 1.1


def test_multiple_tracks_are_deterministic() -> None:
    tracker = EphemeralTracker(max_centroid_distance=30, minimum_iou=0.1)
    update = tracker.update((detection(10, 10), detection(100, 100)), now=1.0)
    assert [track.temporary_id for track in update.active] == [1, 2]

    moved = tracker.update((detection(102, 101), detection(12, 10)), now=1.1)
    assert [track.temporary_id for track in moved.active] == [1, 2]
    assert moved.active[0].position == (22.0, 20.0)
    assert moved.active[1].position == (112.0, 111.0)


def test_missed_detection_expires_after_configured_frame_boundary() -> None:
    tracker = EphemeralTracker(max_missed_frames=1, timeout_seconds=10.0)
    tracker.update((detection(10, 10),), now=0.0)
    first_miss = tracker.update((), now=0.1)
    second_miss = tracker.update((), now=0.2)

    assert len(first_miss.active) == 1
    assert first_miss.expired == ()
    assert second_miss.active == ()
    assert second_miss.expired[0].temporary_id == 1
    assert not second_miss.expired[0].active


def test_track_expires_on_timeout() -> None:
    tracker = EphemeralTracker(max_missed_frames=100, timeout_seconds=0.5)
    tracker.update((detection(10, 10),), now=5.0)
    update = tracker.update((), now=5.5)
    assert update.active == ()
    assert [track.temporary_id for track in update.expired] == [1]


def test_reset_destroys_state_and_does_not_restore_session() -> None:
    tracker = EphemeralTracker()
    tracker.update((detection(10, 10),), now=1.0)
    destroyed = tracker.reset()

    assert destroyed[0].temporary_id == 1
    assert not destroyed[0].active
    assert tracker.active_count == 0
    fresh = tracker.update((detection(100, 100),), now=0.0)
    assert fresh.active[0].temporary_id == 1
    assert fresh.active[0].first_seen_monotonic == 0.0


def test_new_tracker_has_no_cross_session_restoration() -> None:
    previous = EphemeralTracker()
    previous.update((detection(10, 10),), now=10.0)

    new_session = EphemeralTracker()
    assert new_session.active_count == 0
    update = new_session.update((detection(50, 50),), now=0.0)
    assert update.active[0].temporary_id == 1
    assert update.active[0].first_seen_monotonic == 0.0


def test_unmatched_detection_creates_new_monotonic_id() -> None:
    tracker = EphemeralTracker(max_centroid_distance=10, minimum_iou=0.1)
    tracker.update((detection(10, 10),), now=1.0)
    update = tracker.update((detection(100, 100),), now=1.1)
    assert [track.temporary_id for track in update.active] == [1, 2]


def test_time_cannot_move_backwards() -> None:
    tracker = EphemeralTracker()
    tracker.update((), now=2.0)
    with pytest.raises(ValueError, match="backwards"):
        tracker.update((), now=1.0)
