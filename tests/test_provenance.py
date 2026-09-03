import unittest
from pathlib import Path

from packages.Startup.Version import ProvenanceID


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROVENANCE = "ORPHICK-MRM-20260903-2C42BF7"


class ProvenanceTests(unittest.TestCase):
    def test_provenance_marker_is_stable_across_public_notices(self):
        self.assertEqual(EXPECTED_PROVENANCE, ProvenanceID)
        for relative_path in ("CHANGELOG.md", "COPYRIGHT.md"):
            text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn(EXPECTED_PROVENANCE, text)
            self.assertIn("Mohammadreza Mahdavi", text)

    def test_release_packages_carry_license_and_provenance_notices(self):
        for relative_path in (
            "packaging/windows/MkvMuxingBatch.spec",
            "packaging/windows/MkvMuxingBatchQt5.spec",
        ):
            text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn('project_root / "LICENSE"', text)
            self.assertIn('project_root / "COPYRIGHT.md"', text)
            self.assertIn('project_root / "CHANGELOG.md"', text)

    def test_windows_metadata_carries_provenance_marker(self):
        metadata = (PROJECT_ROOT / "packaging/windows/VersionFile.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn(EXPECTED_PROVENANCE, metadata)
        self.assertIn("Copyright (C) 2026 Mohammadreza Mahdavi", metadata)


if __name__ == "__main__":
    unittest.main()
