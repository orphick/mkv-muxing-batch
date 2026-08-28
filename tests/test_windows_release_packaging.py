import importlib.util
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = PROJECT_ROOT / "packaging" / "windows" / "verify_packaged_runtime.py"
SPEC = importlib.util.spec_from_file_location("verify_packaged_runtime", VERIFIER_PATH)
VERIFIER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(VERIFIER)


class PackagedRuntimeVerificationTests(unittest.TestCase):
    def _create_required_runtime(
        self, application_directory: Path, qt_major: int = 6
    ) -> None:
        relative_paths = {
            5: (
                "_internal/PySide2/QtCore.pyd",
                "_internal/PySide2/Qt5Core.dll",
                "_internal/PySide2/pyside2.abi3.dll",
                "_internal/shiboken2/shiboken2.abi3.dll",
            ),
            6: (
                "_internal/PySide6/QtCore.pyd",
                "_internal/PySide6/Qt6Core.dll",
                "_internal/PySide6/pyside6.abi3.dll",
                "_internal/shiboken6/shiboken6.abi3.dll",
            ),
        }
        for relative_path in relative_paths[qt_major]:
            path = application_directory / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    def test_clean_qt_runtime_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            application_directory = Path(directory)
            self._create_required_runtime(application_directory)

            self.assertEqual(VERIFIER.verify(application_directory), [])

    def test_clean_qt5_runtime_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            application_directory = Path(directory)
            self._create_required_runtime(application_directory, qt_major=5)

            self.assertEqual(
                VERIFIER.verify(application_directory, qt_major=5), []
            )

    def test_top_level_icu_runtime_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            application_directory = Path(directory)
            self._create_required_runtime(application_directory)
            foreign_icu = application_directory / "_internal" / "icuuc.dll"
            foreign_icu.touch()

            errors = VERIFIER.verify(application_directory)

            self.assertEqual(len(errors), 1)
            self.assertIn("Shadowing ICU DLL", errors[0])
            self.assertIn("icuuc.dll", errors[0])


if __name__ == "__main__":
    unittest.main()
