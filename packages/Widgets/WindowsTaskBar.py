import ctypes
from ctypes import wintypes
import comtypes
import comtypes.client as cc

TaskBarGUID = "{56FDF344-FD6D-11d0-958A-006097C9A090}"
comtypes.CoInitializeEx()
from packages.Widgets.WindowsTaskBarLib import ITaskbarList3

FlashWindow = ctypes.windll.user32.FlashWindow
FlashWindow.argtypes = (wintypes.HWND, wintypes.BOOL)
FlashWindow.restype = wintypes.BOOL
DestroyIcon = ctypes.windll.user32.DestroyIcon
DestroyIcon.argtypes = (wintypes.HICON,)
DestroyIcon.restype = wintypes.BOOL


def create_icon(icon_path):
    CreateIconFromResourceEx = ctypes.windll.user32.CreateIconFromResourceEx
    CreateIconFromResourceEx.restype = ctypes.wintypes.HICON
    size_x, size_y = 32, 32
    LR_DEFAULTCOLOR = 0
    with open(icon_path, "rb") as f:
        png = f.read()
    hicon = CreateIconFromResourceEx(
        png, len(png), 1, 0x30000, size_x, size_y, LR_DEFAULTCOLOR
    )
    if not hicon:
        raise ctypes.WinError()
    return hicon


def destroy_icon(icon_handle):
    if icon_handle:
        DestroyIcon(wintypes.HICON(icon_handle))


class WindowsTaskBar:
    def __init__(self, hwnd):
        super().__init__()
        self.window_id = int(hwnd)
        self._overlay_icon_handle = None
        self._overlay_icon_path = None
        self._progress_value = None
        self.taskbar = cc.CreateObject(
            TaskBarGUID, interface=ITaskbarList3, clsctx=comtypes.CLSCTX_ALL
        )
        self.taskbar.HrInit()

    def setState(self, value):
        if value == "normal":
            self.taskbar.SetProgressState(self.window_id, 0)

        elif value == "warning":
            self.taskbar.SetProgressState(self.window_id, 10)

        elif value == "error":
            self.taskbar.SetProgressState(self.window_id, 15)

        elif value == "loading":
            self.taskbar.SetProgressState(self.window_id, -15)

        elif value == "done":
            FlashWindow(wintypes.HWND(self.window_id), True)

    def setProgress(self, value: int):
        value = min(value, 100)
        value = max(0, value)
        if value == self._progress_value:
            return
        self.taskbar.setProgressValue(self.window_id, value, 100)
        self._progress_value = value

    def setOverlayIcon(self, icon_path):
        if icon_path == self._overlay_icon_path and self._overlay_icon_handle:
            return

        new_icon_handle = create_icon(icon_path=icon_path)
        try:
            self.taskbar.SetOverlayIcon(
                self.window_id, new_icon_handle, "MKV Muxing Batch GUI status"
            )
        except Exception:
            destroy_icon(new_icon_handle)
            raise

        old_icon_handle = self._overlay_icon_handle
        self._overlay_icon_handle = new_icon_handle
        self._overlay_icon_path = icon_path
        destroy_icon(old_icon_handle)

    def clearOverlayIcon(self):
        self.taskbar.SetOverlayIcon(self.window_id, 0, "MKV Muxing Batch GUI status")
        old_icon_handle = self._overlay_icon_handle
        self._overlay_icon_handle = None
        self._overlay_icon_path = None
        destroy_icon(old_icon_handle)
