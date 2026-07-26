"""Tests for synthetic data and aggregate-only dashboard preparation."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from face_analytics.dashboard import DashboardData, prepare_dashboard_data
from face_analytics.demo import generate_synthetic_windows
from face_analytics.storage import AggregateStore


def test_synthetic_windows_contain_aggregates_only() -> None:
    windows = generate_synthetic_windows(count=3, seed=1)
    assert len(windows) == 3
    assert all(window.data_source == "synthetic" for window in windows)
    names = {field.name for field in fields(windows[0])}
    assert not any(
        forbidden in name
        for name in names
        for forbidden in ("track", "identity", "embedding", "image", "path")
    )


def test_dashboard_preparation_handles_empty_database() -> None:
    data = prepare_dashboard_data(())
    assert isinstance(data, DashboardData)
    assert data.traffic == ()
    assert data.latest_timestamp is None


def test_dashboard_prepares_summary_zone_heatmap_and_source(tmp_path: Path) -> None:
    store = AggregateStore(tmp_path / "synthetic.sqlite3")
    store.initialize()
    for window in generate_synthetic_windows(count=4, seed=2):
        store.save(window)

    data = prepare_dashboard_data(store.list_recent())

    assert len(data.traffic) == 4
    assert data.total_entries > 0
    assert data.peak_occupancy > 0
    assert data.average_dwell_seconds > 0
    assert data.data_sources == ("synthetic",)
    assert {zone.name for zone in data.zones} == {
        "checkout",
        "entrance",
        "featured-display",
    }
    assert len(data.heatmap) == data.heatmap_rows * data.heatmap_columns


def test_schema_migration_marks_existing_rows_observed(tmp_path: Path) -> None:
    store = AggregateStore(tmp_path / "analytics.sqlite3")
    store.initialize()
    assert "data_source" in store.aggregate_columns()
