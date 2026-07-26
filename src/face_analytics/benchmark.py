"""Small detector throughput benchmark without accuracy claims."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from face_analytics.detection.base import FaceDetector, Frame
from face_analytics.frame_sources import FrameSource


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    frames: int
    detections: int
    elapsed_seconds: float
    frames_per_second: float
    mean_latency_ms: float


def benchmark_detector(
    detector: FaceDetector, source: FrameSource, max_frames: int
) -> BenchmarkResult:
    if max_frames <= 0:
        raise ValueError("max_frames must be positive")
    processed = 0
    detections = 0
    start = perf_counter()
    while processed < max_frames:
        frame: Frame | None = source.read()
        if frame is None:
            break
        detections += len(detector.detect(frame))
        processed += 1
    elapsed = perf_counter() - start
    effective_elapsed = max(elapsed, 1e-12)
    return BenchmarkResult(
        frames=processed,
        detections=detections,
        elapsed_seconds=elapsed,
        frames_per_second=processed / effective_elapsed,
        mean_latency_ms=(effective_elapsed / processed * 1000) if processed else 0.0,
    )
