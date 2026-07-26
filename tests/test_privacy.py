"""Privacy regression tests tied to actual source and SQLite boundaries."""

from __future__ import annotations

from pathlib import Path

from face_analytics.privacy_checks import audit_repository, audit_schema

ROOT = Path(__file__).resolve().parents[1]


def test_repository_has_no_prohibited_persistent_artifacts_or_write_apis() -> None:
    assert audit_repository(ROOT) == ()


def test_aggregate_schema_has_no_person_level_fields(tmp_path: Path) -> None:
    assert audit_schema(tmp_path / "privacy.sqlite3") == ()


def test_gitignore_names_sensitive_artifact_categories() -> None:
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for expected in (
        ".env",
        "datasets/",
        "face_crops/",
        "embeddings/",
        "footage/",
        "frames/",
        "weights/",
        "*.sqlite3",
    ):
        assert expected in ignore
