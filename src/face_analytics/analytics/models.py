"""Persistable aggregate models with no individual identifiers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ZoneAggregate:
    name: str
    entries: int
    exits: int
    dwell_total_seconds: float


@dataclass(frozen=True, slots=True)
class AggregateWindow:
    """One coarse analytics window suitable for aggregate-only persistence."""

    window_start: datetime
    window_seconds: int
    occupancy_samples: int
    occupancy_sum: int
    peak_occupancy: int
    entries: int
    exits: int
    dwell_count: int
    dwell_total_seconds: float
    dwell_histogram: tuple[int, ...]
    zone_aggregates: tuple[ZoneAggregate, ...]
    heatmap_rows: int
    heatmap_columns: int
    normalized_heatmap: tuple[float, ...]

    def __post_init__(self) -> None:
        if self.window_start.tzinfo is None:
            raise ValueError("window_start must be timezone-aware")
        if self.window_seconds < 60:
            raise ValueError("window_seconds must be at least 60")
        if self.heatmap_rows <= 0 or self.heatmap_columns <= 0:
            raise ValueError("heatmap dimensions must be positive")
        if len(self.normalized_heatmap) != self.heatmap_rows * self.heatmap_columns:
            raise ValueError("heatmap length does not match its dimensions")

    @property
    def average_occupancy(self) -> float:
        if self.occupancy_samples == 0:
            return 0.0
        return self.occupancy_sum / self.occupancy_samples

    @property
    def average_dwell_seconds(self) -> float:
        if self.dwell_count == 0:
            return 0.0
        return self.dwell_total_seconds / self.dwell_count

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(UTC)
