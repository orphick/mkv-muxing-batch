import ctypes
import sys
import unittest
from unittest.mock import patch


@unittest.skipUnless(sys.platform == "win32", "Windows native handle tests")
class WindowsNativeHandleTests(unittest.TestCase):
    def test_dwm_signature_uses_pointer_sized_hwnd_and_windows_bool(self):
        from ctypes import wintypes

        from packages.Widgets.WindowsDarkMode import load_dwm_set_window_attribute

        function = load_dwm_set_window_attribute()

        self.assertIs(function.argtypes[0], wintypes.HWND)
        self.assertEqual(
            ctypes.sizeof(ctypes.c_void_p), ctypes.sizeof(function.argtypes[0])
        )
        self.assertEqual(4, ctypes.sizeof(wintypes.BOOL))

    def test_large_window_handle_reaches_dwm_as_pointer(self):
        from ctypes import wintypes

        from packages.Widgets.WindowsDarkMode import set_immersive_dark_mode

        large_handle = (1 << 40) + 123
        captured = {}

        class Window:
            @staticmethod
            def winId():
                return large_handle

        def recorder(hwnd, attribute, enabled, enabled_size):
            captured["hwnd"] = hwnd.value
            captured["attribute"] = attribute.value
            captured["enabled"] = ctypes.cast(
                enabled, ctypes.POINTER(wintypes.BOOL)
            ).contents.value
            captured["enabled_size"] = enabled_size.value
            return 0

        applied = set_immersive_dark_mode(Window(), recorder, 20, True)

        self.assertTrue(applied)
        self.assertEqual(large_handle, captured["hwnd"])
        self.assertEqual(20, captured["attribute"])
        self.assertEqual(1, captured["enabled"])
        self.assertEqual(ctypes.sizeof(wintypes.BOOL), captured["enabled_size"])

    def test_taskbar_overlay_reuses_and_releases_native_icon_handles(self):
        from packages.Widgets.WindowsTaskBar import WindowsTaskBar

        class FakeTaskbar:
            def __init__(self):
                self.overlay_calls = []

            def SetOverlayIcon(self, *args):
                self.overlay_calls.append(args)

        taskbar = WindowsTaskBar.__new__(WindowsTaskBar)
        taskbar.window_id = 123
        taskbar.taskbar = FakeTaskbar()
        taskbar._overlay_icon_handle = None
        taskbar._overlay_icon_path = None
        taskbar._progress_value = None

        with (
            patch(
                "packages.Widgets.WindowsTaskBar.create_icon",
                side_effect=(1001, 1002),
            ) as create_icon,
            patch("packages.Widgets.WindowsTaskBar.destroy_icon") as destroy_icon,
        ):
            for _ in range(10_000):
                taskbar.setOverlayIcon("running.png")
            taskbar.setOverlayIcon("paused.png")
            taskbar.clearOverlayIcon()

        self.assertEqual(2, create_icon.call_count)
        self.assertEqual(3, len(taskbar.taskbar.overlay_calls))
        destroy_icon.assert_any_call(1001)
        destroy_icon.assert_any_call(1002)


if __name__ == "__main__":
    unittest.main()
