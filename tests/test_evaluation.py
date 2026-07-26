"""Synthetic tests for evaluation metrics and reports."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from face_analytics.detection.base import BoundingBox
from face_analytics.evaluation import (
    EvaluationSample,
    ScoredBox,
    evaluate_samples,
    write_report,
)


def test_precision_recall_f1_and_conditions_are_calculated() -> None:
    truth = BoundingBox(10, 10, 20, 20)
    samples = (
        EvaluationSample(
            ground_truth=(truth,),
            predictions=(
                ScoredBox(BoundingBox(10, 10, 20, 20), 0.9),
                ScoredBox(BoundingBox(60, 60, 10, 10), 0.8),
            ),
            conditions=("hard", "small-face", "occlusion"),
            latency_ms=10,
        ),
        EvaluationSample(
            ground_truth=(truth,),
            predictions=(),
            conditions=("hard", "low-light"),
            latency_ms=20,
        ),
    )

    report = evaluate_samples(samples)

    assert report.overall.true_positives == 1
    assert report.overall.false_positives == 1
    assert report.overall.false_negatives == 1
    assert report.overall.precision == pytest.approx(0.5)
    assert report.overall.recall == pytest.approx(0.5)
    assert report.overall.f1 == pytest.approx(0.5)
    assert report.by_condition["hard"] == report.overall
    assert report.by_condition["small-face"].recall == 1.0
    assert report.by_condition["low-light"].recall == 0.0
    assert report.mean_latency_ms == 15
    assert report.throughput_fps == pytest.approx(1000 / 15)
    assert not report.demographic_fairness_measured


def test_confidence_threshold_filters_predictions() -> None:
    sample = EvaluationSample(
        ground_truth=(BoundingBox(0, 0, 10, 10),),
        predictions=(ScoredBox(BoundingBox(0, 0, 10, 10), 0.4),),
    )
    report = evaluate_samples((sample,), confidence_threshold=0.5)
    assert report.overall.true_positives == 0
    assert report.overall.false_negatives == 1


def test_invalid_threshold_is_rejected() -> None:
    with pytest.raises(ValueError, match="iou_threshold"):
        evaluate_samples((), iou_threshold=1.1)


def test_machine_and_human_reports_are_written(tmp_path: Path) -> None:
    report = evaluate_samples(
        (
            EvaluationSample(
                ground_truth=(),
                predictions=(),
                conditions=("easy",),
                latency_ms=5,
            ),
        )
    )
    json_path, markdown_path = write_report(report, tmp_path / "evaluation")

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["samples"] == 1
    assert payload["demographic_fairness_measured"] is False
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Demographic fairness measured: no" in markdown
    assert "do not" in markdown
