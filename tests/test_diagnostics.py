import logging
import tempfile
import time
import unittest
from pathlib import Path

from packages.diagnostics import DiagnosticsRuntime, rotate_diagnostic_log
from packages.Startup import GlobalFiles


class DiagnosticsTests(unittest.TestCase):
    def test_diagnostic_log_has_a_stable_user_facing_name(self):
        self.assertEqual(
            Path(GlobalFiles.DiagnosticsLogFilePath).name, "diagnostics.log"
        )

    def test_full_diagnostic_log_is_rotated_before_a_new_session(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "diagnostics.log"
            log_path.write_text("current", encoding="utf-8")
            log_path.with_name("diagnostics.log.1").write_text(
                "previous", encoding="utf-8"
            )

            rotate_diagnostic_log(log_path, max_bytes=1, backup_count=3)

            self.assertFalse(log_path.exists())
            self.assertEqual(
                log_path.with_name("diagnostics.log.1").read_text(encoding="utf-8"),
                "current",
            )
            self.assertEqual(
                log_path.with_name("diagnostics.log.2").read_text(encoding="utf-8"),
                "previous",
            )

    def test_gui_hang_writes_one_thread_dump_until_heartbeat_recovers(self):
        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "diagnostics.log"
            runtime = DiagnosticsRuntime(
                log_path=log_path,
                version="test",
                qt_core=None,
                qt_binding_name="test",
                qt_major_version=5,
                hang_timeout_seconds=10,
            )
            with open(log_path, "a", encoding="utf-8") as fault_stream:
                runtime._fault_stream = fault_stream
                runtime._last_heartbeat = time.monotonic() - 11.0
                now = time.monotonic()
                self.assertTrue(runtime.check_gui_hang(now=now))
                self.assertFalse(runtime.check_gui_hang(now=now + 9.0))

                runtime.record_heartbeat()
                self.assertFalse(runtime._hang_reported)
                self.assertIsNone(runtime._hang_started)
            runtime._fault_stream = None
            logging.shutdown()
            diagnostic_text = log_path.read_text(encoding="utf-8")
            self.assertEqual(diagnostic_text.count("GUI HANG THREAD DUMP"), 2)
            self.assertIn("Current thread", diagnostic_text)


if __name__ == "__main__":
    unittest.main()
