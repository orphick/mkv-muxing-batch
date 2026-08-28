import unittest

from packages.qt_compat import QT_BINDING_NAME, QT_MAJOR_VERSION, QtGui, QtWidgets


class QtCompatibilityTests(unittest.TestCase):
    def test_loaded_binding_is_supported(self):
        self.assertIn(QT_BINDING_NAME, {"PySide2", "PySide6"})
        self.assertIn(QT_MAJOR_VERSION, {5, 6})

    def test_shared_qt6_import_surface_is_available(self):
        self.assertTrue(hasattr(QtGui, "QShortcut"))
        self.assertTrue(hasattr(QtWidgets.QApplication, "exec"))
        self.assertTrue(hasattr(QtWidgets.QDialog, "exec"))


if __name__ == "__main__":
    unittest.main()
