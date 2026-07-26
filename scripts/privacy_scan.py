"""Run privacy regressions against the repository and aggregate schema."""

from __future__ import annotations

import argparse
from pathlib import Path

from face_analytics.privacy_checks import run_privacy_audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--db", type=Path, default=Path("artifacts/privacy-audit.sqlite3")
    )
    args = parser.parse_args()
    issues = run_privacy_audit(args.root.resolve(), args.db)
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        return 1
    print("Privacy audit passed: repository artifacts, source APIs, and schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
