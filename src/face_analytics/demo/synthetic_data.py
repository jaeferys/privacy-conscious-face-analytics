"""Deterministic synthetic aggregate data for a recruiter-safe demo."""

from __future__ import annotations

import math
import random
from datetime import UTC, datetime, timedelta

from face_analytics.analytics.models import AggregateWindow, ZoneAggregate


def generate_synthetic_windows(
    *,
    count: int = 48,
    seed: int = 7,
    start: datetime | None = None,
    window_seconds: int = 1800,
    heatmap_rows: int = 6,
    heatmap_columns: int = 8,
) -> tuple[AggregateWindow, ...]:
    if count <= 0:
        raise ValueError("count must be positive")
    if window_seconds < 60:
        raise ValueError("window_seconds must be at least 60")
    rng = random.Random(seed)
    window_start = start or datetime.now(UTC).replace(
        minute=0, second=0, microsecond=0
    ) - timedelta(seconds=window_seconds * count)
    output: list[AggregateWindow] = []
    for index in range(count):
        timestamp = window_start + timedelta(seconds=index * window_seconds)
        hour = timestamp.hour + timestamp.minute / 60
        opening_curve = max(0.0, math.sin((hour - 8) / 12 * math.pi))
        baseline = 2 + 28 * opening_curve
        average_occupancy = max(0.0, baseline + rng.uniform(-2.5, 2.5))
        samples = 30
        occupancy_sum = round(average_occupancy * samples)
        peak = max(round(average_occupancy), round(average_occupancy * 1.45))
        entries = max(0, round(average_occupancy * rng.uniform(0.6, 1.1)))
        exits = max(0, entries + rng.choice((-2, -1, 0, 0, 1, 2)))
        dwell_count = max(0, exits)
        average_dwell = rng.uniform(35, 150)
        dwell_total = dwell_count * average_dwell
        histogram = _dwell_histogram(dwell_count, rng)
        heatmap = _synthetic_heatmap(heatmap_rows, heatmap_columns, index, rng)
        output.append(
            AggregateWindow(
                window_start=timestamp,
                window_seconds=window_seconds,
                occupancy_samples=samples,
                occupancy_sum=occupancy_sum,
                peak_occupancy=peak,
                entries=entries,
                exits=exits,
                dwell_count=dwell_count,
                dwell_total_seconds=dwell_total,
                dwell_histogram=histogram,
                zone_aggregates=(
                    ZoneAggregate(
                        "entrance",
                        entries=entries,
                        exits=exits,
                        dwell_total_seconds=dwell_total * 0.15,
                    ),
                    ZoneAggregate(
                        "featured-display",
                        entries=max(0, round(entries * 0.55)),
                        exits=max(0, round(exits * 0.52)),
                        dwell_total_seconds=dwell_total * 0.45,
                    ),
                    ZoneAggregate(
                        "checkout",
                        entries=max(0, round(entries * 0.35)),
                        exits=max(0, round(exits * 0.33)),
                        dwell_total_seconds=dwell_total * 0.30,
                    ),
                ),
                heatmap_rows=heatmap_rows,
                heatmap_columns=heatmap_columns,
                normalized_heatmap=heatmap,
                data_source="synthetic",
            )
        )
    return tuple(output)


def _dwell_histogram(count: int, rng: random.Random) -> tuple[int, ...]:
    if count == 0:
        return (0, 0, 0, 0, 0, 0, 0)
    weights = (0.08, 0.15, 0.23, 0.25, 0.18, 0.08, 0.03)
    values = [round(count * weight) for weight in weights]
    difference = count - sum(values)
    values[rng.randrange(len(values))] += difference
    return tuple(values)


def _synthetic_heatmap(
    rows: int, columns: int, index: int, rng: random.Random
) -> tuple[float, ...]:
    center_x = 0.35 + 0.15 * math.sin(index / 7)
    center_y = 0.55 + 0.10 * math.cos(index / 5)
    values = []
    for row in range(rows):
        for column in range(columns):
            x = (column + 0.5) / columns
            y = (row + 0.5) / rows
            distance = (x - center_x) ** 2 + (y - center_y) ** 2
            values.append(
                max(0.0, math.exp(-distance / 0.08) + rng.uniform(-0.04, 0.04))
            )
    maximum = max(values)
    return tuple(min(1.0, value / maximum) for value in values)
