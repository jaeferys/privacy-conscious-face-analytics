"""Pure aggregate transformations for Streamlit and tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from face_analytics.storage import StoredWindow


@dataclass(frozen=True, slots=True)
class TrafficPoint:
    timestamp: datetime
    average_occupancy: float
    entries: int
    exits: int
    peak_occupancy: int


@dataclass(frozen=True, slots=True)
class ZonePoint:
    name: str
    entries: int
    exits: int
    dwell_minutes: float


@dataclass(frozen=True, slots=True)
class DashboardData:
    current_occupancy: float
    total_entries: int
    total_exits: int
    peak_occupancy: int
    average_dwell_seconds: float
    latest_timestamp: datetime | None
    data_sources: tuple[str, ...]
    traffic: tuple[TrafficPoint, ...]
    dwell_histogram: tuple[int, ...]
    zones: tuple[ZonePoint, ...]
    heatmap_rows: int
    heatmap_columns: int
    heatmap: tuple[float, ...]


def prepare_dashboard_data(windows: tuple[StoredWindow, ...]) -> DashboardData:
    if not windows:
        return DashboardData(
            current_occupancy=0.0,
            total_entries=0,
            total_exits=0,
            peak_occupancy=0,
            average_dwell_seconds=0.0,
            latest_timestamp=None,
            data_sources=(),
            traffic=(),
            dwell_histogram=(),
            zones=(),
            heatmap_rows=0,
            heatmap_columns=0,
            heatmap=(),
        )
    records = tuple(
        item.record
        for item in sorted(windows, key=lambda item: item.record.window_start)
    )
    latest = records[-1]
    dwell_count = sum(record.dwell_count for record in records)
    dwell_total = sum(record.dwell_total_seconds for record in records)
    histogram_length = max(len(record.dwell_histogram) for record in records)
    histogram = tuple(
        sum(
            record.dwell_histogram[index] if index < len(record.dwell_histogram) else 0
            for record in records
        )
        for index in range(histogram_length)
    )
    zone_totals: dict[str, list[float]] = {}
    for record in records:
        for zone in record.zone_aggregates:
            totals = zone_totals.setdefault(zone.name, [0, 0, 0.0])
            totals[0] += zone.entries
            totals[1] += zone.exits
            totals[2] += zone.dwell_total_seconds
    return DashboardData(
        current_occupancy=latest.average_occupancy,
        total_entries=sum(record.entries for record in records),
        total_exits=sum(record.exits for record in records),
        peak_occupancy=max(record.peak_occupancy for record in records),
        average_dwell_seconds=dwell_total / dwell_count if dwell_count else 0.0,
        latest_timestamp=latest.window_start,
        data_sources=tuple(sorted({record.data_source for record in records})),
        traffic=tuple(
            TrafficPoint(
                timestamp=record.window_start,
                average_occupancy=record.average_occupancy,
                entries=record.entries,
                exits=record.exits,
                peak_occupancy=record.peak_occupancy,
            )
            for record in records
        ),
        dwell_histogram=histogram,
        zones=tuple(
            ZonePoint(
                name=name,
                entries=int(values[0]),
                exits=int(values[1]),
                dwell_minutes=values[2] / 60,
            )
            for name, values in sorted(zone_totals.items())
        ),
        heatmap_rows=latest.heatmap_rows,
        heatmap_columns=latest.heatmap_columns,
        heatmap=latest.normalized_heatmap,
    )
