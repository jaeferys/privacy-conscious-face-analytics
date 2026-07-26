"""SQLite repository accepting aggregate windows only."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from face_analytics.analytics.models import AggregateWindow

SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class StoredWindow:
    id: int
    record: AggregateWindow


class AggregateStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except sqlite3.Error:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS aggregate_windows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    window_start TEXT NOT NULL,
                    window_seconds INTEGER NOT NULL CHECK(window_seconds >= 60),
                    occupancy_samples INTEGER NOT NULL,
                    occupancy_sum INTEGER NOT NULL,
                    peak_occupancy INTEGER NOT NULL,
                    entries INTEGER NOT NULL,
                    exits INTEGER NOT NULL,
                    dwell_count INTEGER NOT NULL,
                    dwell_total_seconds REAL NOT NULL,
                    dwell_histogram_json TEXT NOT NULL,
                    zone_aggregates_json TEXT NOT NULL,
                    heatmap_rows INTEGER NOT NULL,
                    heatmap_columns INTEGER NOT NULL,
                    normalized_heatmap_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            connection.execute(
                """
                INSERT INTO schema_metadata(key, value)
                VALUES('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )

    def save(self, record: AggregateWindow) -> int:
        with self._connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO aggregate_windows (
                    window_start, window_seconds, occupancy_samples,
                    occupancy_sum, peak_occupancy, entries, exits, dwell_count,
                    dwell_total_seconds, dwell_histogram_json,
                    zone_aggregates_json, heatmap_rows, heatmap_columns,
                    normalized_heatmap_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.window_start.isoformat(),
                    record.window_seconds,
                    record.occupancy_samples,
                    record.occupancy_sum,
                    record.peak_occupancy,
                    record.entries,
                    record.exits,
                    record.dwell_count,
                    record.dwell_total_seconds,
                    json.dumps(record.dwell_histogram),
                    json.dumps([asdict(zone) for zone in record.zone_aggregates]),
                    record.heatmap_rows,
                    record.heatmap_columns,
                    json.dumps(record.normalized_heatmap),
                ),
            )
            if cursor.lastrowid is None:
                raise RuntimeError("SQLite did not return an aggregate row ID")
            return int(cursor.lastrowid)

    def list_recent(self, *, limit: int = 100) -> tuple[StoredWindow, ...]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM aggregate_windows
                ORDER BY window_start DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(_stored_window(row) for row in rows)

    def clear(self) -> int:
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM aggregate_windows")
            return cursor.rowcount

    def aggregate_columns(self) -> tuple[str, ...]:
        with self._connection() as connection:
            rows = connection.execute("PRAGMA table_info(aggregate_windows)").fetchall()
        return tuple(str(row["name"]) for row in rows)


def _stored_window(row: sqlite3.Row) -> StoredWindow:
    from face_analytics.analytics.models import ZoneAggregate

    return StoredWindow(
        id=int(row["id"]),
        record=AggregateWindow(
            window_start=datetime.fromisoformat(str(row["window_start"])),
            window_seconds=int(row["window_seconds"]),
            occupancy_samples=int(row["occupancy_samples"]),
            occupancy_sum=int(row["occupancy_sum"]),
            peak_occupancy=int(row["peak_occupancy"]),
            entries=int(row["entries"]),
            exits=int(row["exits"]),
            dwell_count=int(row["dwell_count"]),
            dwell_total_seconds=float(row["dwell_total_seconds"]),
            dwell_histogram=tuple(json.loads(row["dwell_histogram_json"])),
            zone_aggregates=tuple(
                ZoneAggregate(**item)
                for item in json.loads(row["zone_aggregates_json"])
            ),
            heatmap_rows=int(row["heatmap_rows"]),
            heatmap_columns=int(row["heatmap_columns"]),
            normalized_heatmap=tuple(json.loads(row["normalized_heatmap_json"])),
        ),
    )
