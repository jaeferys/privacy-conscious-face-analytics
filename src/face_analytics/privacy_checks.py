"""Repository and schema privacy regression checks."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from face_analytics.storage import AggregateStore

PROHIBITED_SUFFIXES = {
    ".avi",
    ".ckpt",
    ".db",
    ".engine",
    ".mkv",
    ".mov",
    ".mp4",
    ".onnx",
    ".parquet",
    ".pt",
    ".pth",
    ".sqlite",
    ".sqlite3",
    ".tflite",
    ".webm",
}
PROHIBITED_DIRECTORIES = {
    "crops",
    "datasets",
    "embeddings",
    "face_crops",
    "footage",
    "frames",
    "identities",
    "models",
    "videos",
    "weights",
}
RISKY_SOURCE_TOKENS = {
    "cv2.imwrite(": "frame/image write API",
    "cv2.VideoWriter(": "video write API",
    "face_crop": "face-crop implementation symbol",
    "embedding_vector": "embedding implementation symbol",
    "CREATE TABLE tracks": "persistent track table",
    "track_id INTEGER": "persistent track identifier column",
}
FORBIDDEN_SCHEMA_TOKENS = {
    "bounding_box",
    "crop",
    "embedding",
    "face",
    "identity",
    "image",
    "path",
    "track",
    "trajectory",
}


def audit_repository(root: Path) -> tuple[str, ...]:
    issues: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_ignored_working_file(root, path):
            continue
        relative = path.relative_to(root)
        if path.name.startswith(".env") and path.name != ".env.example":
            issues.append(f"secret-like environment file: {relative}")
        if path.suffix.lower() in PROHIBITED_SUFFIXES:
            issues.append(f"prohibited generated/binary file: {relative}")
        if PROHIBITED_DIRECTORIES.intersection(relative.parts):
            issues.append(f"prohibited sensitive-data directory: {relative}")
        if path.stat().st_size > 5 * 1024 * 1024:
            issues.append(f"oversized tracked candidate: {relative}")
        if path.suffix == ".py" and "tests" not in relative.parts:
            text = path.read_text(encoding="utf-8")
            for token, description in RISKY_SOURCE_TOKENS.items():
                if token in text and path.name != "privacy_checks.py":
                    issues.append(f"{description}: {relative}")
    return tuple(issues)


def audit_schema(database_path: Path) -> tuple[str, ...]:
    store = AggregateStore(database_path)
    store.initialize()
    columns = store.aggregate_columns()
    issues = [
        f"forbidden aggregate schema column: {column}"
        for column in columns
        if any(token in column.lower() for token in FORBIDDEN_SCHEMA_TOKENS)
    ]
    with sqlite3.connect(database_path) as connection:
        tables = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    if any("track" in table.lower() or "person" in table.lower() for table in tables):
        issues.append("forbidden persistent track/person table")
    return tuple(issues)


def run_privacy_audit(root: Path, database_path: Path) -> tuple[str, ...]:
    return audit_repository(root) + audit_schema(database_path)


def _is_ignored_working_file(root: Path, path: Path) -> bool:
    relative = path.relative_to(root)
    ignored_roots = {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "artifacts",
        "__pycache__",
    }
    return bool(ignored_roots.intersection(relative.parts)) or (
        path.suffix == ".pyc"
        or relative.parts[:1] == ("src",)
        and path.parent.name.endswith(".egg-info")
    )
