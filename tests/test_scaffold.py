"""Validation for the Step 1 project scaffold."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import face_analytics  # noqa: E402


class ScaffoldTests(unittest.TestCase):
    def test_package_has_version(self) -> None:
        self.assertEqual(face_analytics.__version__, "0.5.0")

    def test_architecture_states_required_discard_flow(self) -> None:
        architecture = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
        required_flow = (
            "frame -> detection -> ephemeral tracking -> aggregation "
            "-> frame and track discarded"
        )
        self.assertIn(required_flow, architecture)

    def test_gitignore_blocks_sensitive_artifact_locations(self) -> None:
        patterns = set((ROOT / ".gitignore").read_text(encoding="utf-8").splitlines())
        required_patterns = {
            ".env",
            ".venv/",
            "weights/",
            "footage/",
            "frames/",
            "face_crops/",
            "embeddings/",
            "datasets/",
            "*.sqlite3",
        }
        self.assertTrue(required_patterns.issubset(patterns))


if __name__ == "__main__":
    unittest.main()
