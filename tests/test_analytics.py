"""Deterministic aggregate, zone, heatmap, and SQLite tests."""

from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from pathlib import Path

import pytest

from face_analytics.analytics import AggregateAnalytics, AggregateWindow, RectangleZone
from face_analytics.storage import AggregateStore
from face_analytics.tracking import TrackerUpdate, TrackSnapshot


def track(
    temporary_id: int,
    *,
    first: float,
    last: float,
    position: tuple[float, float],
    active: bool = True,
) -> TrackSnapshot:
    return TrackSnapshot(temporary_id, first, position, last, active)


def test_aggregate_output_has_no_track_or_identity_fields() -> None:
    names = {field.name for field in fields(AggregateWindow)}
    assert not any(
        forbidden in name
        for name in names
        for forbidden in ("track", "identity", "embedding", "image", "path")
    )


def test_occupancy_dwell_zone_transitions_and_heatmap() -> None:
    analytics = AggregateAnalytics(
        frame_width=100,
        frame_height=100,
        window_seconds=300,
        heatmap_rows=2,
        heatmap_columns=2,
        zones=(RectangleZone("display", left=0, top=0, right=0.5, bottom=1),),
        dwell_bin_edges_seconds=(5, 10),
    )
    analytics.observe(
        TrackerUpdate(
            active=(track(1, first=0, last=0, position=(20, 20)),), expired=()
        ),
        now_monotonic=0,
    )
    analytics.observe(
        TrackerUpdate(
            active=(track(1, first=0, last=4, position=(70, 20)),), expired=()
        ),
        now_monotonic=4,
    )
    analytics.observe(
        TrackerUpdate(
            active=(),
            expired=(track(1, first=0, last=8, position=(70, 20), active=False),),
        ),
        now_monotonic=8,
    )

    record = analytics.snapshot_and_reset(window_start=datetime(2026, 1, 1, tzinfo=UTC))

    assert record.occupancy_samples == 3
    assert record.occupancy_sum == 2
    assert record.average_occupancy == pytest.approx(2 / 3)
    assert record.peak_occupancy == 1
    assert record.entries == 1
    assert record.exits == 1
    assert record.dwell_count == 1
    assert record.dwell_total_seconds == 8
    assert record.dwell_histogram == (0, 1, 0)
    assert record.zone_aggregates[0].entries == 1
    assert record.zone_aggregates[0].exits == 1
    assert record.zone_aggregates[0].dwell_total_seconds == 4
    assert record.normalized_heatmap == (1.0, 1.0, 0.0, 0.0)


def test_window_reset_keeps_active_track_transient_but_resets_counts() -> None:
    analytics = AggregateAnalytics(frame_width=100, frame_height=100)
    update = TrackerUpdate(
        active=(track(1, first=0, last=0, position=(50, 50)),), expired=()
    )
    analytics.observe(update, now_monotonic=0)
    analytics.snapshot_and_reset(window_start=datetime(2026, 1, 1, tzinfo=UTC))
    analytics.observe(update, now_monotonic=1)
    second = analytics.snapshot_and_reset(
        window_start=datetime(2026, 1, 1, 0, 5, tzinfo=UTC)
    )
    assert second.entries == 0
    assert second.occupancy_samples == 1


def test_sqlite_schema_and_round_trip_are_aggregate_only(tmp_path: Path) -> None:
    store = AggregateStore(tmp_path / "analytics.sqlite3")
    store.initialize()
    columns = store.aggregate_columns()
    forbidden = ("track", "identity", "embedding", "image", "face", "path")
    assert not any(word in column for column in columns for word in forbidden)

    analytics = AggregateAnalytics(frame_width=100, frame_height=100)
    analytics.observe(
        TrackerUpdate(
            active=(track(1, first=0, last=0, position=(50, 50)),), expired=()
        ),
        now_monotonic=0,
    )
    record = analytics.snapshot_and_reset(window_start=datetime(2026, 1, 1, tzinfo=UTC))
    row_id = store.save(record)
    stored = store.list_recent()

    assert row_id == 1
    assert len(stored) == 1
    assert stored[0].record == record
    assert store.clear() == 1
    assert store.list_recent() == ()


def test_sqlite_uses_minimum_coarse_window(tmp_path: Path) -> None:
    store = AggregateStore(tmp_path / "analytics.sqlite3")
    store.initialize()
    analytics = AggregateAnalytics(frame_width=10, frame_height=10)
    record = analytics.snapshot_and_reset(window_start=datetime(2026, 1, 1, tzinfo=UTC))
    assert record.window_seconds >= 60
