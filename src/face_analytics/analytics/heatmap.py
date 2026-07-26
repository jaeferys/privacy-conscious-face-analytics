"""Coarse normalized heatmap accumulation."""

from __future__ import annotations


class HeatmapAccumulator:
    def __init__(self, rows: int, columns: int) -> None:
        if rows <= 0 or columns <= 0:
            raise ValueError("heatmap dimensions must be positive")
        self.rows = rows
        self.columns = columns
        self._counts = [0] * (rows * columns)

    def add(self, normalized_x: float, normalized_y: float) -> None:
        if not 0.0 <= normalized_x <= 1.0 or not 0.0 <= normalized_y <= 1.0:
            raise ValueError("heatmap points must be normalized")
        column = min(int(normalized_x * self.columns), self.columns - 1)
        row = min(int(normalized_y * self.rows), self.rows - 1)
        self._counts[row * self.columns + column] += 1

    def normalized(self) -> tuple[float, ...]:
        maximum = max(self._counts, default=0)
        if maximum == 0:
            return tuple(0.0 for _ in self._counts)
        return tuple(count / maximum for count in self._counts)

    def reset(self) -> None:
        self._counts = [0] * (self.rows * self.columns)
