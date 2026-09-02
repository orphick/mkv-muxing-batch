import signal
import sys

import psutil

from packages import qt_compat
from packages.diagnostics import setup_diagnostics
# MainApplication constructs QApplication during import. It must precede
# GlobalIcons, because Qt5 aborts if QIcon objects are created without qApp.
from packages.Startup.MainApplication import MainApplication
from packages.Startup import GlobalFiles, GlobalIcons
from packages.Startup.Version import Version
from packages.Widgets.WarningDialog import WarningDialog

QApplication = qt_compat.QtWidgets.QApplication
QFont = qt_compat.QtGui.QFont
QFontDatabase = qt_compat.QtGui.QFontDatabase

if sys.platform == "win32":
    import ctypes

    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
    from packages.MainWindow import MainWindow
else:
    from packages.MainWindowNonWindowsSystem import (
        MainWindowNonWindowsSystem as MainWindow,
    )

window: MainWindow
app: QApplication
diagnostics = None


def setup_application_font():
    try:
        font_id = QFontDatabase.addApplicationFont(GlobalFiles.MyFontPath)
        font_name = QFontDatabase.applicationFontFamilies(font_id)[0]
        font = QFont(font_name, 10)
        app.setFont(font)
    except Exception:
        warning_dialog = WarningDialog(
            window_title="Missing Fonts",
            info_message="Can't find 'OpenSans' font at "
            "../Resources/Fonts/OpenSans.ttf\n" + "application will use default font",
        )
        warning_dialog.execute()


def create_application():
    global app
    app = MainApplication
    app.setWindowIcon(GlobalIcons.AppIcon)


def create_window():
    global window
    window = MainWindow(sys.argv)


def run_application():
    try:
        app_execute = app.exec()
    finally:
        kill_all_children()
        if diagnostics is not None:
            diagnostics.stop()
    sys.exit(app_execute)


def kill_all_children():
    current_process = psutil.Process()
    children = current_process.children(recursive=True)
    for child in children:
        child.send_signal(signal.SIGTERM)


def setup_logger():
    global diagnostics
    diagnostics = setup_diagnostics(
        log_path=GlobalFiles.DiagnosticsLogFilePath,
        version=Version,
        qt_core=qt_compat.QtCore,
        qt_binding_name=qt_compat.QT_BINDING_NAME,
        qt_major_version=qt_compat.QT_MAJOR_VERSION,
    )


if __name__ == "__main__":
    setup_logger()
    create_application()
    setup_application_font()
    create_window()
    diagnostics.start_gui_watchdog()
    run_application()
