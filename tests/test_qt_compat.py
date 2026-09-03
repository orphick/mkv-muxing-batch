import unittest

from packages.qt_compat import (
    QT_BINDING_NAME,
    QT_MAJOR_VERSION,
    QtCore,
    QtGui,
    QtWidgets,
    qt_enum_value,
)


class QtCompatibilityTests(unittest.TestCase):
    def test_loaded_binding_is_supported(self):
        self.assertIn(QT_BINDING_NAME, {"PySide2", "PySide6"})
        self.assertIn(QT_MAJOR_VERSION, {5, 6})

    def test_shared_qt6_import_surface_is_available(self):
        self.assertTrue(hasattr(QtGui, "QShortcut"))
        self.assertTrue(hasattr(QtWidgets.QApplication, "exec"))
        self.assertTrue(hasattr(QtWidgets.QDialog, "exec"))

    def test_check_state_value_is_compatible_with_both_bindings(self):
        self.assertEqual(2, qt_enum_value(QtCore.Qt.CheckState.Checked))

    def test_subtitle_track_checkbox_accepts_checked_state(self):
        from packages.Tabs.GlobalSetting import GlobalSetting
        from packages.Tabs.MuxSetting.Widgets.SubtitleTracksCheckableComboBox import (
            SubtitleTracksCheckableComboBox,
        )

        class FakeComboBox:
            def __init__(self):
                self.tracks_language = ["eng"]
                self.tracks_id = [1]
                self.tracks_name = ["English"]
                self.disabled = None
                self.tooltip_updated = False

            def setDisabled(self, disabled):
                self.disabled = disabled

            def set_tool_tip_hint(self):
                self.tooltip_updated = True

        setting_names = (
            "MUX_SETTING_ONLY_KEEP_THOSE_SUBTITLES_ENABLED",
            "MUX_SETTING_ONLY_KEEP_THOSE_SUBTITLES_TRACKS_LANGUAGES",
            "MUX_SETTING_ONLY_KEEP_THOSE_SUBTITLES_TRACKS_IDS",
            "MUX_SETTING_ONLY_KEEP_THOSE_SUBTITLES_TRACKS_NAMES",
        )
        for name in setting_names:
            self.addCleanup(setattr, GlobalSetting, name, getattr(GlobalSetting, name))

        combo_box = FakeComboBox()
        SubtitleTracksCheckableComboBox.check_box_state_changed(
            combo_box, qt_enum_value(QtCore.Qt.CheckState.Checked)
        )

        self.assertFalse(combo_box.disabled)
        self.assertTrue(combo_box.tooltip_updated)
        self.assertTrue(GlobalSetting.MUX_SETTING_ONLY_KEEP_THOSE_SUBTITLES_ENABLED)


if __name__ == "__main__":
    unittest.main()
