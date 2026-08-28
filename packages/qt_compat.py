"""Load PySide6 normally or expose PySide2 through the existing import surface."""

from __future__ import annotations

import os
import sys


def _load_pyside6():
    import PySide6
    from PySide6 import QtCore, QtGui, QtWidgets

    return PySide6, QtCore, QtGui, QtWidgets, 6


def _load_pyside2():
    import PySide2
    from PySide2 import QtCore, QtGui, QtWidgets

    # These classes moved from QtWidgets to QtGui in Qt 6. Keep the current
    # source imports valid when the separately packaged Qt 5 build is used.
    for class_name in ("QAction", "QActionGroup", "QShortcut", "QWidgetAction"):
        if not hasattr(QtGui, class_name) and hasattr(QtWidgets, class_name):
            setattr(QtGui, class_name, getattr(QtWidgets, class_name))

    # PySide2 follows Python's reserved-word convention and exposes exec_().
    # PySide6 keeps exec_() as an alias, so source code can use exec() while the
    # compatibility bootstrap supplies the same spelling for Qt 5.
    for class_name in ("QApplication", "QDialog", "QMenu"):
        qt_class = getattr(QtWidgets, class_name)
        if not hasattr(qt_class, "exec") and hasattr(qt_class, "exec_"):
            qt_class.exec = qt_class.exec_

    # Existing modules intentionally continue importing the PySide6 namespace.
    # Registering aliases before any of them load avoids a risky 199-file port.
    sys.modules["PySide6"] = PySide2
    sys.modules["PySide6.QtCore"] = QtCore
    sys.modules["PySide6.QtGui"] = QtGui
    sys.modules["PySide6.QtWidgets"] = QtWidgets
    return PySide2, QtCore, QtGui, QtWidgets, 5


_requested_binding = os.environ.get("MKV_MUXING_BATCH_QT_API", "auto").casefold()
if _requested_binding not in {"auto", "pyside2", "pyside6"}:
    raise RuntimeError(
        "MKV_MUXING_BATCH_QT_API must be 'auto', 'pyside2', or 'pyside6'"
    )

if _requested_binding == "pyside2":
    QtBinding, QtCore, QtGui, QtWidgets, QT_MAJOR_VERSION = _load_pyside2()
elif _requested_binding == "pyside6":
    QtBinding, QtCore, QtGui, QtWidgets, QT_MAJOR_VERSION = _load_pyside6()
else:
    try:
        QtBinding, QtCore, QtGui, QtWidgets, QT_MAJOR_VERSION = _load_pyside6()
    except ModuleNotFoundError as error:
        if error.name != "PySide6":
            raise
        QtBinding, QtCore, QtGui, QtWidgets, QT_MAJOR_VERSION = _load_pyside2()

QT_BINDING_NAME = QtBinding.__name__
