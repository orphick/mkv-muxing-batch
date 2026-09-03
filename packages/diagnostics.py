"""Persistent crash and GUI-hang diagnostics for the desktop application."""

from __future__ import annotations

import atexit
import faulthandler
import logging
import os
import platform
import sys
import threading
import time
from pathlib import Path
from traceback import format_exception

from packages.Startup.Version import ProvenanceID

LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 3
GUI_HEARTBEAT_INTERVAL_MS = 1_000
GUI_HANG_TIMEOUT_SECONDS = 10.0
logger = logging.getLogger(__name__)


def rotate_diagnostic_log(
    log_path: Path,
    max_bytes: int = LOG_MAX_BYTES,
    backup_count: int = LOG_BACKUP_COUNT,
) -> None:
    """Rotate completed-session logs before opening the new session log."""
    if not log_path.is_file() or log_path.stat().st_size < max_bytes:
        return
    oldest = log_path.with_name(f"{log_path.name}.{backup_count}")
    try:
        oldest.unlink()
    except FileNotFoundError:
        pass
    for index in range(backup_count - 1, 0, -1):
        source = log_path.with_name(f"{log_path.name}.{index}")
        if source.exists():
            source.replace(log_path.with_name(f"{log_path.name}.{index + 1}"))
    log_path.replace(log_path.with_name(f"{log_path.name}.1"))


class DiagnosticsRuntime:
    """Own logging hooks and a watchdog independent of the Qt event loop."""

    def __init__(
        self,
        log_path,
        version,
        qt_core,
        qt_binding_name,
        qt_major_version,
        hang_timeout_seconds=GUI_HANG_TIMEOUT_SECONDS,
    ):
        self.log_path = Path(log_path)
        self.version = version
        self.qt_core = qt_core
        self.qt_binding_name = qt_binding_name
        self.qt_major_version = qt_major_version
        self.hang_timeout_seconds = hang_timeout_seconds
        self._fault_stream = None
        self._heartbeat_timer = None
        self._watchdog_thread = None
        self._watchdog_stop = threading.Event()
        self._heartbeat_lock = threading.Lock()
        self._last_heartbeat = None
        self._hang_reported = False
        self._hang_started = None
        self._shutdown = False
        self._previous_sys_excepthook = sys.excepthook
        self._previous_threading_excepthook = getattr(threading, "excepthook", None)
        self._previous_unraisablehook = getattr(sys, "unraisablehook", None)
        self._previous_qt_message_handler = None

    def start(self):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        rotate_diagnostic_log(self.log_path)
        handlers = [logging.FileHandler(self.log_path, encoding="utf-8", mode="a")]
        if sys.stderr is not None:
            handlers.append(logging.StreamHandler())
        logging.basicConfig(
            format=(
                "%(asctime)s.%(msecs)03d %(levelname)s "
                "[%(threadName)s] %(name)s: %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
            level=logging.DEBUG,
            handlers=handlers,
            force=True,
        )
        self._fault_stream = open(  # noqa: SIM115 - intentionally session-scoped
            self.log_path, "a", encoding="utf-8", buffering=1
        )
        faulthandler.enable(file=self._fault_stream, all_threads=True)
        sys.excepthook = self._handle_exception
        if hasattr(threading, "excepthook"):
            threading.excepthook = self._handle_thread_exception
        if hasattr(sys, "unraisablehook"):
            sys.unraisablehook = self._handle_unraisable
        self._install_qt_message_handler()
        self._log_session_header()
        atexit.register(self.stop)
        return self

    def start_gui_watchdog(self):
        if self._watchdog_thread is not None:
            return
        self._heartbeat_timer = self.qt_core.QTimer()
        self._heartbeat_timer.setInterval(GUI_HEARTBEAT_INTERVAL_MS)
        self._heartbeat_timer.timeout.connect(self.record_heartbeat)
        self.record_heartbeat()
        self._heartbeat_timer.start()
        self._watchdog_thread = threading.Thread(
            target=self._watch_gui,
            name="GuiHangWatchdog",
            daemon=True,
        )
        self._watchdog_thread.start()
        logger.info(
            "GUI watchdog started (hang threshold %.1f seconds)",
            self.hang_timeout_seconds,
        )

    def record_heartbeat(self):
        now = time.monotonic()
        recovered_after = None
        with self._heartbeat_lock:
            if self._hang_reported and self._hang_started is not None:
                recovered_after = now - self._hang_started
            self._last_heartbeat = now
            self._hang_reported = False
            self._hang_started = None
        if recovered_after is not None:
            logger.warning(
                "GUI event loop recovered after %.1f seconds", recovered_after
            )

    def check_gui_hang(self, now=None):
        now = time.monotonic() if now is None else now
        with self._heartbeat_lock:
            if self._last_heartbeat is None:
                return False
            stalled_for = now - self._last_heartbeat
            if stalled_for < self.hang_timeout_seconds or self._hang_reported:
                return False
            self._hang_reported = True
            self._hang_started = self._last_heartbeat
        logger.critical(
            "GUI HANG DETECTED: no event-loop heartbeat for %.1f seconds. "
            "Dumping every Python thread.",
            stalled_for,
        )
        self.dump_all_thread_stacks("GUI HANG THREAD DUMP")
        return True

    def dump_all_thread_stacks(self, reason):
        if self._fault_stream is None:
            return
        self._fault_stream.write(
            f"\n===== {reason} at {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n"
        )
        faulthandler.dump_traceback(file=self._fault_stream, all_threads=True)
        self._fault_stream.write(f"===== END {reason} =====\n\n")
        self._fault_stream.flush()

    def stop(self):
        if self._shutdown:
            return
        self._shutdown = True
        logger.info("Diagnostic session ending")
        self._watchdog_stop.set()
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.stop()
        if self._watchdog_thread is not None and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=2)
        sys.excepthook = self._previous_sys_excepthook
        if self._previous_threading_excepthook is not None:
            threading.excepthook = self._previous_threading_excepthook
        if self._previous_unraisablehook is not None:
            sys.unraisablehook = self._previous_unraisablehook
        self.qt_core.qInstallMessageHandler(self._previous_qt_message_handler)
        if self._fault_stream is not None:
            faulthandler.disable()
            self._fault_stream.flush()
            self._fault_stream.close()
            self._fault_stream = None
        logging.shutdown()

    def _watch_gui(self):
        while not self._watchdog_stop.wait(1.0):
            self.check_gui_hang()

    def _handle_exception(self, exception_type, exception_value, traceback):
        logger.critical(
            "Uncaught exception on the GUI thread",
            exc_info=(exception_type, exception_value, traceback),
        )
        self.dump_all_thread_stacks("UNCAUGHT GUI EXCEPTION THREAD DUMP")

    def _handle_thread_exception(self, args):
        logger.critical(
            "Uncaught exception in thread %s",
            getattr(args.thread, "name", "unknown"),
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )
        self.dump_all_thread_stacks("UNCAUGHT WORKER EXCEPTION THREAD DUMP")

    def _handle_unraisable(self, unraisable):
        details = "".join(
            format_exception(
                unraisable.exc_type,
                unraisable.exc_value,
                unraisable.exc_traceback,
            )
        )
        logger.error(
            "Unraisable exception in %r: %s\n%s",
            unraisable.object,
            unraisable.err_msg,
            details,
        )

    def _install_qt_message_handler(self):
        levels = {
            getattr(self.qt_core, "QtDebugMsg", object()): logging.DEBUG,
            getattr(self.qt_core, "QtInfoMsg", object()): logging.INFO,
            getattr(self.qt_core, "QtWarningMsg", object()): logging.WARNING,
            getattr(self.qt_core, "QtCriticalMsg", object()): logging.ERROR,
            getattr(self.qt_core, "QtFatalMsg", object()): logging.CRITICAL,
        }

        def qt_message_handler(message_type, context, message):
            category = getattr(context, "category", "qt") or "qt"
            logging.getLogger(f"qt.{category}").log(
                levels.get(message_type, logging.INFO), message
            )

        self._qt_message_handler = qt_message_handler
        self._previous_qt_message_handler = self.qt_core.qInstallMessageHandler(
            qt_message_handler
        )

    def _log_session_header(self):
        qversion = getattr(self.qt_core, "qVersion", lambda: "unknown")()
        logger.info("=" * 72)
        logger.info("MKV Muxing Batch GUI v%s diagnostic session", self.version)
        logger.info("Project provenance=%s", ProvenanceID)
        logger.info(
            "PID=%s frozen=%s executable=%s",
            os.getpid(),
            bool(getattr(sys, "frozen", False)),
            sys.executable,
        )
        logger.info("Python=%s OS=%s", platform.python_version(), platform.platform())
        logger.info(
            "Qt binding=%s Qt major=%s Qt runtime=%s",
            self.qt_binding_name,
            self.qt_major_version,
            qversion,
        )
        logger.info("Diagnostic log=%s", self.log_path)


def setup_diagnostics(
    log_path,
    version,
    qt_core,
    qt_binding_name,
    qt_major_version,
    hang_timeout_seconds=GUI_HANG_TIMEOUT_SECONDS,
):
    return DiagnosticsRuntime(
        log_path=log_path,
        version=version,
        qt_core=qt_core,
        qt_binding_name=qt_binding_name,
        qt_major_version=qt_major_version,
        hang_timeout_seconds=hang_timeout_seconds,
    ).start()
