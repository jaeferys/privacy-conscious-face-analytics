"""Condition-aware detector evaluation with honest, reproducible outputs."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

import cv2

from face_analytics.detection.base import BoundingBox, FaceDetector


@dataclass(frozen=True, slots=True)
class ScoredBox:
    box: BoundingBox
    confidence: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between zero and one")


@dataclass(frozen=True, slots=True)
class EvaluationSample:
    ground_truth: tuple[BoundingBox, ...]
    predictions: tuple[ScoredBox, ...]
    conditions: tuple[str, ...] = ()
    latency_ms: float = 0.0


@dataclass(frozen=True, slots=True)
class Metrics:
    true_positives: int
    false_positives: int
    false_negatives: int
    precision: float
    recall: float
    f1: float


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    overall: Metrics
    by_condition: dict[str, Metrics]
    confidence_threshold: float
    iou_threshold: float
    samples: int
    mean_latency_ms: float
    throughput_fps: float
    demographic_fairness_measured: bool = False


def evaluate_samples(
    samples: tuple[EvaluationSample, ...],
    *,
    confidence_threshold: float = 0.5,
    iou_threshold: float = 0.5,
) -> EvaluationReport:
    _validate_threshold("confidence_threshold", confidence_threshold)
    _validate_threshold("iou_threshold", iou_threshold)
    overall_counts = [0, 0, 0]
    condition_counts: dict[str, list[int]] = {}
    total_latency = 0.0
    for sample in samples:
        counts = _match_sample(sample, confidence_threshold, iou_threshold)
        for index, value in enumerate(counts):
            overall_counts[index] += value
        for condition in sample.conditions:
            condition_values = condition_counts.setdefault(condition, [0, 0, 0])
            for index, value in enumerate(counts):
                condition_values[index] += value
        total_latency += sample.latency_ms

    mean_latency = total_latency / len(samples) if samples else 0.0
    throughput = 1000.0 / mean_latency if mean_latency > 0 else 0.0
    return EvaluationReport(
        overall=_metrics(*overall_counts),
        by_condition={
            condition: _metrics(*counts)
            for condition, counts in sorted(condition_counts.items())
        },
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
        samples=len(samples),
        mean_latency_ms=mean_latency,
        throughput_fps=throughput,
    )


def run_manifest_evaluation(
    manifest_path: Path,
    detector: FaceDetector,
    *,
    confidence_threshold: float = 0.5,
    iou_threshold: float = 0.5,
    max_images: int | None = None,
) -> EvaluationReport:
    """Evaluate local ignored images described by a JSON Lines manifest."""

    if not manifest_path.is_file():
        raise FileNotFoundError(f"evaluation manifest not found: {manifest_path}")
    if max_images is not None and max_images <= 0:
        raise ValueError("max_images must be positive")
    samples: list[EvaluationSample] = []
    with manifest_path.open(encoding="utf-8") as manifest:
        for line_number, line in enumerate(manifest, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            image_path = manifest_path.parent / str(payload["image"])
            frame = cv2.imread(str(image_path))
            if frame is None:
                raise ValueError(
                    f"unable to load manifest image on line {line_number}: {image_path}"
                )
            start = perf_counter()
            detections = detector.detect(frame)
            latency_ms = (perf_counter() - start) * 1000
            ground_truth = tuple(
                BoundingBox(
                    x=int(box[0]),
                    y=int(box[1]),
                    width=int(box[2]),
                    height=int(box[3]),
                )
                for box in payload["boxes"]
            )
            conditions = tuple(str(item) for item in payload.get("conditions", ()))
            samples.append(
                EvaluationSample(
                    ground_truth=ground_truth,
                    predictions=tuple(
                        ScoredBox(detection.box, detection.confidence)
                        for detection in detections
                    ),
                    conditions=conditions,
                    latency_ms=latency_ms,
                )
            )
            del frame
            if max_images is not None and len(samples) >= max_images:
                break
    return evaluate_samples(
        tuple(samples),
        confidence_threshold=confidence_threshold,
        iou_threshold=iou_threshold,
    )


def write_report(report: EvaluationReport, output_prefix: Path) -> tuple[Path, Path]:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_prefix.with_suffix(".json")
    markdown_path = output_prefix.with_suffix(".md")
    json_path.write_text(
        json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    rows = [
        "# Detector evaluation report",
        "",
        f"- Samples: {report.samples}",
        f"- Confidence threshold: {report.confidence_threshold:.2f}",
        f"- IoU threshold: {report.iou_threshold:.2f}",
        f"- Mean latency: {report.mean_latency_ms:.2f} ms",
        f"- Throughput: {report.throughput_fps:.2f} frames/second",
        "- Demographic fairness measured: no",
        "",
        "## Metrics",
        "",
        "| Condition | Precision | Recall | F1 | TP | FP | FN |",
        "|---|---:|---:|---:|---:|---:|---:|",
        _metric_row("overall", report.overall),
    ]
    rows.extend(
        _metric_row(condition, metrics)
        for condition, metrics in report.by_condition.items()
    )
    rows.extend(
        [
            "",
            "These values are measured only on the supplied manifest. They do not",
            "establish deployment accuracy, demographic fairness, or anonymity.",
            "",
        ]
    )
    markdown_path.write_text("\n".join(rows), encoding="utf-8")
    return json_path, markdown_path


def _match_sample(
    sample: EvaluationSample, confidence_threshold: float, iou_threshold: float
) -> tuple[int, int, int]:
    unmatched_truth = set(range(len(sample.ground_truth)))
    true_positives = 0
    false_positives = 0
    predictions = sorted(
        (
            prediction
            for prediction in sample.predictions
            if prediction.confidence >= confidence_threshold
        ),
        key=lambda prediction: prediction.confidence,
        reverse=True,
    )
    for prediction in predictions:
        candidates = [
            (_iou(prediction.box, sample.ground_truth[index]), index)
            for index in unmatched_truth
        ]
        overlap, truth_index = max(candidates, default=(0.0, -1))
        if overlap >= iou_threshold:
            true_positives += 1
            unmatched_truth.remove(truth_index)
        else:
            false_positives += 1
    return true_positives, false_positives, len(unmatched_truth)


def _metrics(
    true_positives: int, false_positives: int, false_negatives: int
) -> Metrics:
    precision_denominator = true_positives + false_positives
    recall_denominator = true_positives + false_negatives
    precision = true_positives / precision_denominator if precision_denominator else 0.0
    recall = true_positives / recall_denominator if recall_denominator else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return Metrics(
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1=f1,
    )


def _iou(first: BoundingBox, second: BoundingBox) -> float:
    left = max(first.x, second.x)
    top = max(first.y, second.y)
    right = min(first.right, second.right)
    bottom = min(first.bottom, second.bottom)
    intersection = max(0, right - left) * max(0, bottom - top)
    if intersection == 0:
        return 0.0
    union = first.width * first.height + second.width * second.height - intersection
    return intersection / union


def _validate_threshold(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _metric_row(name: str, metrics: Metrics) -> str:
    return (
        f"| {name} | {metrics.precision:.3f} | {metrics.recall:.3f} | "
        f"{metrics.f1:.3f} | {metrics.true_positives} | "
        f"{metrics.false_positives} | {metrics.false_negatives} |"
    )
