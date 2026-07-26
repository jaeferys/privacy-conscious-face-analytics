"""Command-line entry points for privacy-conscious analytics workflows."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np

from face_analytics.benchmark import benchmark_detector
from face_analytics.demo import generate_synthetic_windows
from face_analytics.detection import MediaPipeDetector, OpenCVHaarDetector
from face_analytics.detection.base import FaceDetector
from face_analytics.evaluation import run_manifest_evaluation, write_report
from face_analytics.frame_sources import (
    FrameSource,
    IterableFrameSource,
    VideoFrameSource,
    WebcamFrameSource,
)
from face_analytics.storage import AggregateStore


def _detector(name: str, threshold: float) -> FaceDetector:
    if name == "mediapipe":
        return MediaPipeDetector(confidence_threshold=threshold)
    if name == "opencv-haar":
        return OpenCVHaarDetector(confidence_threshold=threshold)
    raise ValueError(f"unsupported detector: {name}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="face-analytics",
        description="Privacy-conscious aggregate face analytics",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    benchmark = subparsers.add_parser(
        "benchmark-detector",
        help="measure detector latency and throughput without saving frames",
    )
    benchmark.add_argument(
        "--detector", choices=("mediapipe", "opencv-haar"), default="mediapipe"
    )
    benchmark.add_argument("--frames", type=int, default=30)
    benchmark.add_argument("--width", type=int, default=640)
    benchmark.add_argument("--height", type=int, default=480)
    benchmark.add_argument("--confidence", type=float, default=0.5)

    inspect = subparsers.add_parser(
        "inspect-source",
        help="count detections from a consented source without saving frames",
    )
    inspect.add_argument(
        "--detector", choices=("mediapipe", "opencv-haar"), default="mediapipe"
    )
    source = inspect.add_mutually_exclusive_group(required=True)
    source.add_argument("--webcam", type=int)
    source.add_argument("--video", type=Path)
    inspect.add_argument("--max-frames", type=int, default=300)
    inspect.add_argument("--confidence", type=float, default=0.5)

    init_db = subparsers.add_parser(
        "init-db", help="initialize an aggregate-only SQLite database"
    )
    init_db.add_argument("--db", type=Path, default=Path("artifacts/analytics.sqlite3"))
    clear = subparsers.add_parser(
        "clear-aggregates", help="delete generated aggregate rows"
    )
    clear.add_argument("--db", type=Path, default=Path("artifacts/analytics.sqlite3"))

    evaluate = subparsers.add_parser(
        "evaluate", help="evaluate a detector against an ignored local manifest"
    )
    evaluate.add_argument("--manifest", type=Path, required=True)
    evaluate.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("reports/evaluation/detector"),
    )
    evaluate.add_argument(
        "--detector", choices=("mediapipe", "opencv-haar"), default="mediapipe"
    )
    evaluate.add_argument("--confidence", type=float, default=0.5)
    evaluate.add_argument("--iou", type=float, default=0.5)
    evaluate.add_argument("--max-images", type=int)

    synthetic = subparsers.add_parser(
        "generate-synthetic", help="write aggregate-only synthetic demo windows"
    )
    synthetic.add_argument(
        "--db", type=Path, default=Path("artifacts/analytics.sqlite3")
    )
    synthetic.add_argument("--windows", type=int, default=48)
    synthetic.add_argument("--seed", type=int, default=7)

    dashboard = subparsers.add_parser("dashboard", help="start the Streamlit dashboard")
    dashboard.add_argument(
        "--db", type=Path, default=Path("artifacts/analytics.sqlite3")
    )
    dashboard.add_argument("--port", type=int, default=8501)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "init-db":
        store = AggregateStore(args.db)
        store.initialize()
        print(f"initialized aggregate-only database: {args.db}")
        return 0
    if args.command == "clear-aggregates":
        store = AggregateStore(args.db)
        store.initialize()
        deleted = store.clear()
        print(f"deleted aggregate windows: {deleted}")
        return 0
    if args.command == "generate-synthetic":
        store = AggregateStore(args.db)
        store.initialize()
        windows = generate_synthetic_windows(count=args.windows, seed=args.seed)
        for window in windows:
            store.save(window)
        print(f"wrote synthetic aggregate windows: {len(windows)}")
        return 0
    if args.command == "dashboard":
        environment = os.environ.copy()
        environment["FACE_ANALYTICS_DB_PATH"] = str(args.db)
        app_path = Path(__file__).parent / "dashboard" / "app.py"
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_path),
                "--server.port",
                str(args.port),
            ],
            check=False,
            env=environment,
        )
        return completed.returncode

    detector = _detector(args.detector, args.confidence)
    try:
        if args.command == "evaluate":
            report = run_manifest_evaluation(
                args.manifest,
                detector,
                confidence_threshold=args.confidence,
                iou_threshold=args.iou,
                max_images=args.max_images,
            )
            json_path, markdown_path = write_report(report, args.output_prefix)
            print(f"wrote evaluation: {json_path} and {markdown_path}")
            return 0
        source: FrameSource
        if args.command == "benchmark-detector":
            if args.width <= 0 or args.height <= 0:
                raise ValueError("width and height must be positive")
            blank = np.zeros((args.height, args.width, 3), dtype=np.uint8)
            source = IterableFrameSource(blank.copy() for _ in range(args.frames))
            result = benchmark_detector(detector, source, args.frames)
        else:
            source = (
                WebcamFrameSource(args.webcam)
                if args.webcam is not None
                else VideoFrameSource(args.video)
            )
            try:
                result = benchmark_detector(detector, source, args.max_frames)
            finally:
                source.close()
    finally:
        detector.close()
    print(
        f"frames={result.frames} detections={result.detections} "
        f"elapsed_seconds={result.elapsed_seconds:.4f} "
        f"fps={result.frames_per_second:.2f} "
        f"mean_latency_ms={result.mean_latency_ms:.2f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
