"""Natural-language, permission-bounded tools for ASTRA."""
import re
import subprocess
import webbrowser
from urllib.parse import urlparse, quote_plus

from core.web_search import WebSearch
from core.browser_agent import BrowserAgent
from core.workspace_files import WorkspaceFiles
from core.desktop_control import (
    list_visible_windows, foreground_window_title,
    type_into_focused_window, type_into_window, press_desktop_key, click_screen,
    inspect_window_controls, click_named_control, set_named_control_value,
)


APP_ALLOWLIST = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
}
POLITE_PREFIX = r"(?:(?:please|can you|could you|would you)\s+)?"


class ToolRouter:
    def __init__(self):
        self.web = WebSearch()
        self.browser = BrowserAgent()
        self.files = WorkspaceFiles()

    def _task_steps(self, text):
        value = (text or "").strip()
        match = re.match(rf"^{POLITE_PREFIX}(?:run task|task|do these steps)\s*:\s*(.*)$", value, re.I | re.S)
        if not match:
            return []
        steps = []
        for line in re.split(r"\s*\|\|\s*|\r?\n", match.group(1)):
            line = re.sub(r"^\s*(?:\d+[.)]|[-*])\s*", "", line).strip()
            if line:
                steps.append(line)
        return steps if 1 <= len(steps) <= 8 else []

    def is_command(self, text):
        value = (text or "").strip()
        steps = self._task_steps(value)
        if steps:
            return all(self.is_command(step) for step in steps)
        patterns = (
            rf"^{POLITE_PREFIX}(?:search(?: the web)?(?: for)?|look up(?: online)?|find online)\s+.+$",
            rf"^{POLITE_PREFIX}(?:google|search google for|search on google for)\s+.+$",
            rf"^{POLITE_PREFIX}(?:open|launch|start)\s+.+$",
            rf"^{POLITE_PREFIX}(?:check my laptop|check this laptop|what(?:'s| is) open(?: on my laptop)?|show open windows|list open apps)$",
            rf"^{POLITE_PREFIX}type\s+.+$",
            rf"^{POLITE_PREFIX}press\s+.+$",
            rf"^{POLITE_PREFIX}click\s+\d+\s*[, ]\s*\d+$",
            rf"^{POLITE_PREFIX}(?:(?:browse|read page)\s+https?://\S+|open browser to\s+https?://\S+)$",
            rf"^{POLITE_PREFIX}click link\s+.+\s+on\s+https?://\S+$",
            rf"^{POLITE_PREFIX}fill field\s+.+\s+with\s+.+\s+on\s+https?://\S+$",
            rf"^{POLITE_PREFIX}(?:inspect window|read controls in)\s+.+$",
            rf"^{POLITE_PREFIX}click button\s+.+\s+in\s+.+$",
            rf"^{POLITE_PREFIX}type into field\s+.+\s+in\s+.+::.+$",
            rf"^{POLITE_PREFIX}(?:list|show)(?: me)? files in\s+.+$",
            rf"^{POLITE_PREFIX}what files are in\s+.+$",
            rf"^{POLITE_PREFIX}list files recursively in\s+.+$",
            rf"^{POLITE_PREFIX}(?:read|open)(?: the)? file\s+.+$",
            rf"^{POLITE_PREFIX}(?:create|make|write new)(?: a)? file\s+.+::.*$",
            rf"^{POLITE_PREFIX}append to file\s+.+::.*$",
            rf"^{POLITE_PREFIX}find files named\s+.+\s+in\s+.+$",
            rf"^{POLITE_PREFIX}copy file\s+.+\s+to\s+.+$",
            rf"^{POLITE_PREFIX}create folder\s+.+$",
            rf"^{POLITE_PREFIX}replace in file\s+.+::.+=>.*$",
        )
        return any(re.match(pattern, value, re.I | re.S) for pattern in patterns)

    def handle(self, text):
        """Return a result for a recognized command, otherwise None."""
        value = (text or "").strip()
        steps = self._task_steps(value)
        if steps:
            reports = []
            for index, step in enumerate(steps, 1):
                try:
                    result = self.handle(step)
                    if result is None:
                        raise RuntimeError("This step is not a supported ASTRA action.")
                    reports.append(f"Step {index}: {step}\n{result}")
                except Exception as exc:
                    reports.append(
                        f"Step {index} failed: {step}\n{exc}\n"
                        "The task stopped here; later steps were not run."
                    )
                    break
            return "\n\n".join(reports)

        google_match = re.match(
            rf"^{POLITE_PREFIX}(?:google|search google for|search on google for)\s+(.+)$",
            value, re.I
        )
        if google_match:
            query = google_match.group(1).strip()
            url = "https://www.google.com/search?q=" + quote_plus(query)
            opened = webbrowser.open(url)
            return (
                f"Opened Google search results for: {query}\n{url}"
                if opened else f"I couldn't open your browser. Search manually: {url}"
            )

        search_match = re.match(
            rf"^{POLITE_PREFIX}(?:search(?: the web)?(?: for)?|look up(?: online)?|find online)\s+(.+)$",
            value, re.I
        )
        if search_match:
            query = search_match.group(1).strip()
            results = self.web.search(query)
            lines = [f"Live web search results for: {query}", ""]
            for index, result in enumerate(results, 1):
                lines.append(f"{index}. {result.title}")
                if result.snippet:
                    lines.append(f"   {result.snippet}")
                lines.append(f"   Source: {result.url}")
                lines.append("")
            lines.append("Search results are leads. Open original sources and check their dates before relying on them.")
            return "\n".join(lines)

        browse_match = re.match(rf"^{POLITE_PREFIX}(?:(?:browse|read page)\s+|open browser to\s+)(https?://\S+)$", value, re.I)
        if browse_match:
            return self.browser.open_and_read(browse_match.group(1))

        click_link = re.match(
            rf"^{POLITE_PREFIX}click link\s+(.+?)\s+on\s+(https?://\S+)$", value, re.I
        )
        if click_link:
            return self.browser.click_link_and_read(click_link.group(2), click_link.group(1).strip())

        fill_field = re.match(
            rf"^{POLITE_PREFIX}fill field\s+(.+?)\s+with\s+(.+?)\s+on\s+(https?://\S+)$",
            value, re.I | re.S
        )
        if fill_field:
            return self.browser.fill_field(
                fill_field.group(3), fill_field.group(1).strip(), fill_field.group(2)
            )

        laptop_match = re.match(
            rf"^{POLITE_PREFIX}(?:check my laptop|check this laptop|what(?:'s| is) open(?: on my laptop)?|show open windows|list open apps)$",
            value, re.I
        )
        if laptop_match:
            windows = list_visible_windows()
            if not windows:
                return "I checked visible windows, but Windows returned no titled windows."
            lines = ["Visible windows on your laptop:"]
            lines.extend(f"- {item['title']} (process ID {item['process_id']})" for item in windows)
            lines.append("\nTo inspect accessible controls, use: inspect window [part of title].")
            return "\n".join(lines)

        inspect_match = re.match(
            rf"^{POLITE_PREFIX}(?:inspect window|read controls in)\s+(.+)$", value, re.I
        )
        if inspect_match:
            title = inspect_match.group(1).strip()
            controls = inspect_window_controls(title)
            if isinstance(controls, dict):
                controls = [controls]
            lines = [f"Accessible controls in window matching '{title}':"]
            for item in controls[:120]:
                name = item.get("name") or "(unnamed)"
                lines.append(
                    f"- {item.get('type', 'Control')}: {name}"
                    f" [id={item.get('automation_id', '')}; enabled={item.get('enabled', False)}]"
                )
            return "\n".join(lines) if len(lines) > 1 else f"No readable controls were exposed by '{title}'."

        click_button = re.match(
            rf"^{POLITE_PREFIX}click button\s+(.+?)\s+in\s+(.+)$", value, re.I
        )
        if click_button:
            return click_named_control(click_button.group(2).strip(), click_button.group(1).strip())

        type_control = re.match(
            rf"^{POLITE_PREFIX}type into field\s+(.+?)\s+in\s+(.+?)\s*::\s*(.+)$",
            value, re.I | re.S
        )
        if type_control:
            return set_named_control_value(
                type_control.group(2).strip(), type_control.group(1).strip(), type_control.group(3)
            )

        recursive_list = re.match(
            rf"^{POLITE_PREFIX}list files recursively in\s+(.+)$", value, re.I
        )
        if recursive_list:
            return self.files.list_files(recursive_list.group(1).strip(), recursive=True)

        list_files = re.match(rf"^{POLITE_PREFIX}(?:list|show)(?: me)? files in\s+(.+)$", value, re.I)
        if not list_files:
            list_files = re.match(rf"^{POLITE_PREFIX}what files are in\s+(.+)$", value, re.I)
        if list_files:
            return self.files.list_files(list_files.group(1).strip())

        read_file = re.match(rf"^{POLITE_PREFIX}(?:read|open)(?: the)? file\s+(.+)$", value, re.I)
        if read_file:
            return self.files.read_file(read_file.group(1).strip().strip('"'))

        create_file = re.match(
            rf"^{POLITE_PREFIX}(?:create|make|write new)(?: a)? file\s+(.+?)\s*::\s*(.*)$", value, re.I | re.S
        )
        if create_file:
            return self.files.create_file(create_file.group(1).strip().strip('"'), create_file.group(2))

        append_file = re.match(
            rf"^{POLITE_PREFIX}append to file\s+(.+?)\s*::\s*(.*)$", value, re.I | re.S
        )
        if append_file:
            return self.files.append_file(append_file.group(1).strip().strip('"'), append_file.group(2))

        find_files = re.match(
            rf"^{POLITE_PREFIX}find files named\s+(.+?)\s+in\s+(.+)$", value, re.I
        )
        if find_files:
            return self.files.find_files(find_files.group(1).strip(), find_files.group(2).strip())

        create_folder = re.match(rf"^{POLITE_PREFIX}create folder\s+(.+)$", value, re.I)
        if create_folder:
            return self.files.create_folder(create_folder.group(1).strip().strip('"'))

        replace_file = re.match(
            rf"^{POLITE_PREFIX}replace in file\s+(.+?)\s*::\s*(.*?)\s*=>\s*(.*)$",
            value, re.I | re.S
        )
        if replace_file:
            return self.files.replace_text(
                replace_file.group(1).strip().strip('"'),
                replace_file.group(2), replace_file.group(3)
            )

        copy_file = re.match(
            rf"^{POLITE_PREFIX}copy file\s+(.+?)\s+to\s+(.+)$", value, re.I
        )
        if copy_file:
            return self.files.copy_file(
                copy_file.group(1).strip().strip('"'), copy_file.group(2).strip().strip('"')
            )

        named_type = re.match(
            rf"^{POLITE_PREFIX}type in (.+?)\s*::\s*(.+)$", value, re.I | re.S
        )
        if named_type:
            target = type_into_window(named_type.group(1).strip(), named_type.group(2))
            return f"Typed the requested text into: {target}"

        type_match = re.match(rf"^{POLITE_PREFIX}type\s+(.+)$", value, re.I | re.S)
        if type_match:
            target = type_into_focused_window(type_match.group(1))
            return f"Typed the requested text into the focused window: {target}"

        press_match = re.match(
            rf"^{POLITE_PREFIX}press\s+(.+?)(?:\s+in\s+(.+))?$", value, re.I
        )
        if press_match:
            key = press_desktop_key(press_match.group(1), press_match.group(2))
            target = foreground_window_title() or "the desktop"
            return f"Pressed {key} while focused on: {target}"

        click_match = re.match(rf"^{POLITE_PREFIX}click\s+(\d+)\s*[, ]\s*(\d+)$", value, re.I)
        if click_match:
            x, y = click_screen(click_match.group(1), click_match.group(2))
            return f"Clicked screen position ({x}, {y})."

        app_match = re.match(rf"^{POLITE_PREFIX}(?:open|launch|start)\s+(.+)$", value, re.I)
        if app_match:
            requested = app_match.group(1).strip().lower()
            if requested in {"google", "google.com"}:
                webbrowser.open("https://www.google.com")
                return "Opened Google in your default browser."
            if requested in APP_ALLOWLIST:
                try:
                    subprocess.Popen([APP_ALLOWLIST[requested]], shell=False)
                    return f"Opened {requested}."
                except OSError as exc:
                    return f"I couldn't launch {requested}: {exc}"
            if requested in {"chrome", "google chrome", "edge", "microsoft edge"}:
                executable = "chrome.exe" if "chrome" in requested else "msedge.exe"
                try:
                    subprocess.Popen([executable], shell=False)
                    return f"Opened {requested}."
                except OSError as exc:
                    return f"I couldn't launch {requested}: {exc}"
            if requested.startswith(("https://", "http://")):
                parsed = urlparse(requested)
                if parsed.scheme in {"http", "https"} and parsed.netloc and not parsed.username:
                    opened = webbrowser.open(requested)
                    return f"Opened {requested}." if opened else f"Try opening this link manually: {requested}"
            return (
                "I can currently launch: Notepad, Calculator, Paint, File Explorer, "
                "Task Manager, Chrome, Edge and Google. More desktop controls are being added."
            )

        return None
