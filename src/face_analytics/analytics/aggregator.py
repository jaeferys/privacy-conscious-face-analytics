"""Convert volatile tracks into coarse aggregate windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from face_analytics.analytics.heatmap import HeatmapAccumulator
from face_analytics.analytics.models import AggregateWindow, ZoneAggregate
from face_analytics.analytics.zones import PolygonZone
from face_analytics.tracking import TrackerUpdate


@dataclass(slots=True)
class _TransientTrack:
    first_seen: float
    last_observed: float
    zones: set[str] = field(default_factory=set)


@dataclass(slots=True)
class _MutableZoneAggregate:
    entries: int = 0
    exits: int = 0
    dwell_total_seconds: float = 0.0


class AggregateAnalytics:
    """In-memory aggregation that never exposes track IDs in output models."""

    def __init__(
        self,
        *,
        frame_width: int,
        frame_height: int,
        window_seconds: int = 300,
        heatmap_rows: int = 12,
        heatmap_columns: int = 16,
        zones: tuple[PolygonZone, ...] = (),
        dwell_bin_edges_seconds: tuple[float, ...] = (5, 15, 30, 60, 120, 300),
    ) -> None:
        if frame_width <= 0 or frame_height <= 0:
            raise ValueError("frame dimensions must be positive")
        if window_seconds < 60:
            raise ValueError("window_seconds must be at least 60")
        if tuple(sorted(dwell_bin_edges_seconds)) != dwell_bin_edges_seconds:
            raise ValueError("dwell bin edges must be sorted")
        if len({zone.name for zone in zones}) != len(zones):
            raise ValueError("zone names must be unique")
        self._frame_width = frame_width
        self._frame_height = frame_height
        self._window_seconds = window_seconds
        self._zones = {zone.name: zone for zone in zones}
        self._dwell_edges = dwell_bin_edges_seconds
        self._transient: dict[int, _TransientTrack] = {}
        self._heatmap = HeatmapAccumulator(heatmap_rows, heatmap_columns)
        self._zone_metrics = {
            name: _MutableZoneAggregate() for name in sorted(self._zones)
        }
        self._occupancy_samples = 0
        self._occupancy_sum = 0
        self._peak_occupancy = 0
        self._entries = 0
        self._exits = 0
        self._dwell_count = 0
        self._dwell_total = 0.0
        self._dwell_histogram = [0] * (len(self._dwell_edges) + 1)

    def observe(self, update: TrackerUpdate, *, now_monotonic: float) -> None:
        if now_monotonic < 0:
            raise ValueError("now_monotonic must be non-negative")
        self._occupancy_samples += 1
        self._occupancy_sum += len(update.active)
        self._peak_occupancy = max(self._peak_occupancy, len(update.active))

        for track in update.active:
            normalized = (
                min(max(track.position[0] / self._frame_width, 0.0), 1.0),
                min(max(track.position[1] / self._frame_height, 0.0), 1.0),
            )
            current_zones = {
                name for name, zone in self._zones.items() if zone.contains(normalized)
            }
            transient = self._transient.get(track.temporary_id)
            if transient is None:
                transient = _TransientTrack(
                    first_seen=track.first_seen_monotonic,
                    last_observed=now_monotonic,
                    zones=current_zones,
                )
                self._transient[track.temporary_id] = transient
                self._entries += 1
                for zone_name in current_zones:
                    self._zone_metrics[zone_name].entries += 1
            else:
                elapsed = max(0.0, now_monotonic - transient.last_observed)
                for zone_name in transient.zones:
                    self._zone_metrics[zone_name].dwell_total_seconds += elapsed
                for zone_name in current_zones - transient.zones:
                    self._zone_metrics[zone_name].entries += 1
                for zone_name in transient.zones - current_zones:
                    self._zone_metrics[zone_name].exits += 1
                transient.zones = current_zones
                transient.last_observed = now_monotonic
            self._heatmap.add(*normalized)

        for track in update.expired:
            transient = self._transient.pop(track.temporary_id, None)
            if transient is None:
                continue
            final_elapsed = max(
                0.0, track.last_seen_monotonic - transient.last_observed
            )
            for zone_name in transient.zones:
                metric = self._zone_metrics[zone_name]
                metric.dwell_total_seconds += final_elapsed
                metric.exits += 1
            dwell = max(0.0, track.last_seen_monotonic - transient.first_seen)
            self._dwell_count += 1
            self._dwell_total += dwell
            self._dwell_histogram[self._dwell_bin(dwell)] += 1
            self._exits += 1

    def snapshot_and_reset(self, *, window_start: datetime) -> AggregateWindow:
        record = AggregateWindow(
            window_start=window_start,
            window_seconds=self._window_seconds,
            occupancy_samples=self._occupancy_samples,
            occupancy_sum=self._occupancy_sum,
            peak_occupancy=self._peak_occupancy,
            entries=self._entries,
            exits=self._exits,
            dwell_count=self._dwell_count,
            dwell_total_seconds=self._dwell_total,
            dwell_histogram=tuple(self._dwell_histogram),
            zone_aggregates=tuple(
                ZoneAggregate(
                    name=name,
                    entries=metric.entries,
                    exits=metric.exits,
                    dwell_total_seconds=metric.dwell_total_seconds,
                )
                for name, metric in sorted(self._zone_metrics.items())
            ),
            heatmap_rows=self._heatmap.rows,
            heatmap_columns=self._heatmap.columns,
            normalized_heatmap=self._heatmap.normalized(),
        )
        self._reset_window_counters()
        return record

    def _dwell_bin(self, dwell_seconds: float) -> int:
        for index, edge in enumerate(self._dwell_edges):
            if dwell_seconds < edge:
                return index
        return len(self._dwell_edges)

    def _reset_window_counters(self) -> None:
        self._occupancy_samples = 0
        self._occupancy_sum = 0
        self._peak_occupancy = 0
        self._entries = 0
        self._exits = 0
        self._dwell_count = 0
        self._dwell_total = 0.0
        self._dwell_histogram = [0] * (len(self._dwell_edges) + 1)
        self._heatmap.reset()
        self._zone_metrics = {
            name: _MutableZoneAggregate() for name in sorted(self._zones)
        }
