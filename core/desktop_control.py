"""Read-only inspection and explicit basic input for the Windows desktop."""
import ctypes
import time
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


def focus_window(title):
    """Focus a visible window whose title contains the supplied text."""
    if not title or len(title) > 120:
        raise ValueError("Enter a short window title to focus.")
    user32 = _user32()
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    for _attempt in range(20):
        matches = []

        def collect(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length <= 0:
                return True
            buffer = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buffer, length + 1)
            if title.casefold() in buffer.value.casefold():
                matches.append(hwnd)
                return False
            return True

        callback = callback_type(collect)
        user32.EnumWindows(callback, 0)
        if matches:
            if not user32.SetForegroundWindow(matches[0]):
                raise RuntimeError(f"Windows would not focus the window matching '{title}'.")
            return matches[0]
        time.sleep(0.25)

    raise RuntimeError(f"No visible window title contains '{title}' after waiting 5 seconds.")


def type_into_focused_window(text):
    """Type literal Unicode text into the currently focused window."""
    if not text or len(text) > 2000:
        raise ValueError("Text must contain between 1 and 2000 characters.")
    user32 = _user32()
    target = foreground_window_title()
    if not target:
        raise RuntimeError("There is no titled foreground window to type into.")
    if "astra desktop" in target.casefold():
        raise RuntimeError(
            "ASTRA is currently focused. Use 'type in Notepad :: your text' to target another app safely."
        )

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

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_size_t),
        ]

    class INPUTUNION(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]

    encoded = text.encode("utf-16-le")
    for index in range(0, len(encoded), 2):
        code_unit = encoded[index] | (encoded[index + 1] << 8)
        down = INPUT(type=1, union=INPUTUNION(ki=KEYBDINPUT(0, code_unit, keyeventf_unicode, 0, 0)))
        up = INPUT(type=1, union=INPUTUNION(ki=KEYBDINPUT(0, code_unit, keyeventf_unicode | keyeventf_keyup, 0, 0)))
        if send_input(1, ctypes.byref(down), ctypes.sizeof(INPUT)) != 1:
            raise OSError("Windows rejected keyboard input.")
        if send_input(1, ctypes.byref(up), ctypes.sizeof(INPUT)) != 1:
            raise OSError("Windows rejected keyboard input.")
    return target


def type_into_window(window_title, text):
    """Focus a named visible window, then type text into it."""
    focus_window(window_title)
    return type_into_focused_window(text)


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


def press_desktop_key(key, window_title=None):
    """Press one explicitly supported key or shortcut, optionally in a named window."""
    user32 = _user32()
    if window_title:
        focus_window(window_title)
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


def _run_uia_script(script, timeout=20):
    """Run a fixed, ASTRA-authored Windows UI Automation script."""
    import base64
    import subprocess

    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    completed = subprocess.run(
        ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
        capture_output=True, text=True, timeout=timeout, creationflags=flags
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Windows UI Automation failed.")
    output = completed.stdout.strip()
    if not output:
        return []
    import json
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Windows UI Automation returned unreadable data.") from exc


def inspect_window_controls(window_title):
    """Read accessible UI control names/text for a visible window; password fields are excluded."""
    import base64
    if not window_title or len(window_title) > 120:
        raise ValueError("Enter a short window title.")
    encoded_title = base64.b64encode(window_title.encode("utf-8")).decode("ascii")
    script = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$title = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_title}'))
$root = [System.Windows.Automation.AutomationElement]::RootElement
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
$target = $null
foreach ($window in $windows) {{
  if ($window.Current.Name -like "*$title*") {{ $target = $window; break }}
}}
if ($null -eq $target) {{ throw "No visible window matched '$title'." }}
$items = [System.Collections.Generic.List[object]]::new()
$queue = [System.Collections.Generic.Queue[object]]::new()
$queue.Enqueue(@($target, 0))
while ($queue.Count -gt 0 -and $items.Count -lt 120) {{
  $entry = $queue.Dequeue()
  $element = $entry[0]
  $depth = [int]$entry[1]
  $current = $element.Current
  if ($depth -gt 0 -and -not $current.IsPassword -and -not $current.IsOffscreen) {{
    $items.Add([pscustomobject]@{{
      name = $current.Name
      type = $current.ControlType.ProgrammaticName
      automation_id = $current.AutomationId
      enabled = $current.IsEnabled
      value = ""
    }})
    $pattern = $null
    if ($element.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)) {{
      if (-not $pattern.Current.IsReadOnly) {{ $items[$items.Count - 1].value = $pattern.Current.Value.Substring(0, [Math]::Min(1200, $pattern.Current.Value.Length)) }}
      else {{ $items[$items.Count - 1].value = $pattern.Current.Value.Substring(0, [Math]::Min(1200, $pattern.Current.Value.Length)) }}
    }} else {{
      $textPattern = $null
      if ($element.TryGetCurrentPattern([System.Windows.Automation.TextPattern]::Pattern, [ref]$textPattern)) {{
        $textValue = $textPattern.DocumentRange.GetText(1200)
        $items[$items.Count - 1].value = $textValue
      }}
    }}
  }}
  if ($depth -lt 4) {{
    $children = $element.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($child in $children) {{ $queue.Enqueue(@($child, $depth + 1)) }}
  }}
}}
ConvertTo-Json -InputObject @($items) -Depth 4 -Compress
"""
    return _run_uia_script(script)


def click_named_control(window_title, control_name):
    """Invoke a visible, enabled button by its accessible name."""
    import base64
    if not window_title or not control_name or len(window_title) > 120 or len(control_name) > 120:
        raise ValueError("Enter a window title and a short control name.")
    encoded_title = base64.b64encode(window_title.encode("utf-8")).decode("ascii")
    encoded_control = base64.b64encode(control_name.encode("utf-8")).decode("ascii")
    script = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$title = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_title}'))
$name = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_control}'))
$root = [System.Windows.Automation.AutomationElement]::RootElement
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
$target = $null
foreach ($window in $windows) {{ if ($window.Current.Name -like "*$title*") {{ $target = $window; break }} }}
if ($null -eq $target) {{ throw "Window not found." }}
$condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty, $name)
$controls = $target.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
foreach ($control in $controls) {{
  if ($control.Current.IsPassword -or -not $control.Current.IsEnabled -or $control.Current.IsOffscreen) {{ continue }}
  if ($control.Current.ControlType -eq [System.Windows.Automation.ControlType]::Button) {{
    $pattern = $null
    if ($control.TryGetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern, [ref]$pattern)) {{
      $pattern.Invoke()
      "Clicked '$name' in '$title'."
      exit 0
    }}
  }}
}}
throw "No enabled visible button named '$name' was found."
"""
    result = _run_uia_script(script)
    return result if isinstance(result, str) else f"Clicked '{control_name}' in '{window_title}'."


def set_named_control_value(window_title, control_name, value):
    """Set a non-password accessible text field without submitting its form."""
    import base64
    if not window_title or not control_name or len(window_title) > 120 or len(control_name) > 120:
        raise ValueError("Enter a window title and a short field name.")
    if value is None or len(value) > 4000:
        raise ValueError("Field text must be no longer than 4000 characters.")
    encoded_title = base64.b64encode(window_title.encode("utf-8")).decode("ascii")
    encoded_control = base64.b64encode(control_name.encode("utf-8")).decode("ascii")
    encoded_value = base64.b64encode(value.encode("utf-8")).decode("ascii")
    script = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$title = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_title}'))
$name = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_control}'))
$value = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{encoded_value}'))
$root = [System.Windows.Automation.AutomationElement]::RootElement
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
$target = $null
foreach ($window in $windows) {{ if ($window.Current.Name -like "*$title*") {{ $target = $window; break }} }}
if ($null -eq $target) {{ throw "Window not found." }}
$condition = [System.Windows.Automation.PropertyCondition]::new([System.Windows.Automation.AutomationElement]::NameProperty, $name)
$controls = $target.FindAll([System.Windows.Automation.TreeScope]::Descendants, $condition)
foreach ($control in $controls) {{
  if ($control.Current.IsPassword -or -not $control.Current.IsEnabled -or $control.Current.IsOffscreen) {{ continue }}
  $pattern = $null
  if ($control.TryGetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern, [ref]$pattern)) {{
    if ($pattern.Current.IsReadOnly) {{ continue }}
    $pattern.SetValue($value)
    "Filled '$name' in '$title'. The form was not submitted."
    exit 0
  }}
}}
throw "No editable non-password field named '$name' was found."
"""
    result = _run_uia_script(script)
    return result if isinstance(result, str) else f"Filled '{control_name}' in '{window_title}'. The form was not submitted."
