"""Simple normalized zone geometry."""

from __future__ import annotations

from dataclasses import dataclass

NormalizedPoint = tuple[float, float]


@dataclass(frozen=True, slots=True)
class PolygonZone:
    name: str
    points: tuple[NormalizedPoint, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("zone name must not be empty")
        if len(self.points) < 3:
            raise ValueError("polygon requires at least three points")
        if not all(
            0.0 <= coordinate <= 1.0 for point in self.points for coordinate in point
        ):
            raise ValueError("zone points must use normalized zero-to-one geometry")

    def contains(self, point: NormalizedPoint) -> bool:
        x, y = point
        inside = False
        previous = self.points[-1]
        for current in self.points:
            current_x, current_y = current
            previous_x, previous_y = previous
            crosses = (current_y > y) != (previous_y > y)
            if crosses:
                boundary_x = (previous_x - current_x) * (y - current_y) / (
                    previous_y - current_y
                ) + current_x
                if x < boundary_x:
                    inside = not inside
            previous = current
        return inside


class RectangleZone(PolygonZone):
    def __init__(
        self, name: str, *, left: float, top: float, right: float, bottom: float
    ) -> None:
        if right <= left or bottom <= top:
            raise ValueError("rectangle edges must define a positive area")
        super().__init__(
            name=name,
            points=((left, top), (right, top), (right, bottom), (left, bottom)),
        )
