"""Read-only inspection and explicit basic input for the Windows desktop."""
import ctypes
from ctypes import wintypes


def _user32():
    if not hasattr(ctypes, "windll"):
        raise RuntimeError("Desktop control is available on Windows only.")
    return ctypes.windll.user32


def list_visible_windows(limit=30):
    """Return titles and process IDs for visible top-level windows."""
    user32 = _user32()
    windows = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

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

    callback = callback_type(collect)
    user32.EnumWindows(callback, 0)
    return windows


def foreground_window_title():
    """Return the title of the currently focused top-level window."""
    user32 = _user32()
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)
    return buffer.value.strip()


def type_into_focused_window(text):
    """Type literal Unicode text into the currently focused window."""
    if not text or len(text) > 2000:
        raise ValueError("Text must contain between 1 and 2000 characters.")
    user32 = _user32()
    target = foreground_window_title()
    if not target:
        raise RuntimeError("There is no titled foreground window to type into.")

    keyeventf_keyup = 0x0002
    keyeventf_unicode = 0x0004
    send_input = user32.SendInput

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class INPUTUNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]

    sent = 0
    for unit in text.encode("utf-16-le"):
        # Process UTF-16 code units below, not individual bytes.
        pass
    encoded = text.encode("utf-16-le")
    for index in range(0, len(encoded), 2):
        code_unit = encoded[index] | (encoded[index + 1] << 8)
        down = INPUT(type=1, union=INPUTUNION(ki=KEYBDINPUT(0, code_unit, keyeventf_unicode, 0, 0)))
        up = INPUT(type=1, union=INPUTUNION(ki=KEYBDINPUT(0, code_unit, keyeventf_unicode | keyeventf_keyup, 0, 0)))
        if send_input(1, ctypes.byref(down), ctypes.sizeof(INPUT)) != 1:
            raise OSError("Windows rejected keyboard input.")
        if send_input(1, ctypes.byref(up), ctypes.sizeof(INPUT)) != 1:
            raise OSError("Windows rejected keyboard input.")
        sent += 1
    return target


SAFE_KEYS = {
    "ENTER": 0x0D, "TAB": 0x09, "ESC": 0x1B, "ESCAPE": 0x1B,
    "BACKSPACE": 0x08, "SPACE": 0x20, "UP": 0x26, "DOWN": 0x28,
    "LEFT": 0x25, "RIGHT": 0x27, "HOME": 0x24, "END": 0x23,
    "PAGEUP": 0x21, "PAGEDOWN": 0x22,
}
SAFE_COMBOS = {
    "CTRL+L": (0x11, 0x4C),
    "CTRL+T": (0x11, 0x54),
    "CTRL+W": (0x11, 0x57),
    "CTRL+C": (0x11, 0x43),
    "CTRL+V": (0x11, 0x56),
    "CTRL+S": (0x11, 0x53),
    "ALT+TAB": (0x12, 0x09),
    "WIN+E": (0x5B, 0x45),
}


def press_desktop_key(key):
    """Press one explicitly supported key or shortcut."""
    user32 = _user32()
    normalized = (key or "").strip().upper().replace(" ", "")
    if normalized in SAFE_KEYS:
        user32.keybd_event(SAFE_KEYS[normalized], 0, 0, 0)
        user32.keybd_event(SAFE_KEYS[normalized], 0, 0x0002, 0)
        return normalized
    if normalized in SAFE_COMBOS:
        modifier, virtual_key = SAFE_COMBOS[normalized]
        user32.keybd_event(modifier, 0, 0, 0)
        user32.keybd_event(virtual_key, 0, 0, 0)
        user32.keybd_event(virtual_key, 0, 0x0002, 0)
        user32.keybd_event(modifier, 0, 0x0002, 0)
        return normalized
    raise ValueError(
        "That key is not in ASTRA's safe key list. Supported keys include Enter, Tab, Escape, "
        "Backspace, arrows, Ctrl+L, Ctrl+T, Ctrl+W, Ctrl+C, Ctrl+V, Ctrl+S, Alt+Tab and Win+E."
    )


def click_screen(x, y):
    """Click a screen coordinate supplied explicitly by the user."""
    user32 = _user32()
    x, y = int(x), int(y)
    width = user32.GetSystemMetrics(0)
    height = user32.GetSystemMetrics(1)
    if not (0 <= x < width and 0 <= y < height):
        raise ValueError(f"Coordinates must be within this screen: 0..{width - 1}, 0..{height - 1}.")
    if not user32.SetCursorPos(x, y):
        raise OSError("Windows could not move the pointer to that position.")
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    return x, y
