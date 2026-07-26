"""Typed, identity-free detector contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, TypeAlias

import numpy as np
from numpy.typing import NDArray

Frame: TypeAlias = NDArray[np.uint8]


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """An image-space bounding box with validated positive dimensions."""

    x: int
    y: int
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.x < 0 or self.y < 0:
            raise ValueError("bounding-box coordinates must be non-negative")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("bounding-box dimensions must be positive")

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height

    @property
    def centroid(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)


@dataclass(frozen=True, slots=True)
class RelativeBox:
    """Frame-relative geometry in the inclusive range zero to one."""

    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if not all(0.0 <= value <= 1.0 for value in values):
            raise ValueError("relative geometry must be between zero and one")
        if self.width <= 0.0 or self.height <= 0.0:
            raise ValueError("relative dimensions must be positive")
        if self.x + self.width > 1.0 + 1e-9:
            raise ValueError("relative box exceeds frame width")
        if self.y + self.height > 1.0 + 1e-9:
            raise ValueError("relative box exceeds frame height")


@dataclass(frozen=True, slots=True)
class Detection:
    """Identity-free detector output for one frame."""

    box: BoundingBox
    confidence: float
    relative_box: RelativeBox

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between zero and one")


class FaceDetector(Protocol):
    """Substitutable detector that must not retain or write input frames."""

    def detect(self, frame: Frame) -> tuple[Detection, ...]:
        """Return validated detections without identity or appearance features."""

    def close(self) -> None:
        """Release volatile detector resources."""
