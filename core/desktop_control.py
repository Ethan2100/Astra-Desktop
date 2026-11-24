"""Read-only Windows desktop inspection helpers."""
import ctypes
from ctypes import wintypes


def list_visible_windows(limit=30):
    """Return titles and process IDs for visible top-level windows."""
    if not hasattr(ctypes, "windll"):
        raise RuntimeError("Laptop window inspection is available on Windows only.")

    user32 = ctypes.windll.user32
    windows = []

    enum_callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def collect(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        title = buffer.value.strip()
        if title:
            process_id = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
            windows.append({"title": title, "process_id": int(process_id.value)})
        return len(windows) < limit

    callback = enum_callback_type(collect)
    user32.EnumWindows(callback, 0)
    return windows
