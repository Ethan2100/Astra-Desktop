"""Deterministic, permission-bounded commands for ASTRA."""
import re
import subprocess
import webbrowser
from urllib.parse import urlparse, quote_plus
from core.web_search import WebSearch
from core.desktop_control import (
    list_visible_windows, foreground_window_title,
    type_into_focused_window, type_into_window, press_desktop_key, click_screen
)


APP_ALLOWLIST = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
}
POLITE_PREFIX = r"(?:(?:please|can you|could you|would you)\s+)?"


class ToolRouter:
    def __init__(self):
        self.web = WebSearch()

    def is_command(self, text):
        value = (text or "").strip()
        patterns = (
            rf"^{POLITE_PREFIX}(?:search(?: the web)?(?: for)?|look up(?: online)?|find online)\s+.+$",
            rf"^{POLITE_PREFIX}(?:google|search google for|search on google for)\s+.+$",
            rf"^{POLITE_PREFIX}(?:open|launch|start)\s+.+$",
            rf"^{POLITE_PREFIX}(?:check my laptop|check this laptop|what(?:'s| is) open(?: on my laptop)?|show open windows|list open apps)$",
            rf"^{POLITE_PREFIX}type\s+.+$",
            rf"^{POLITE_PREFIX}press\s+.+$",
            rf"^{POLITE_PREFIX}click\s+\d+\s*[, ]\s*\d+$",
        )
        return any(re.match(pattern, value, re.I) for pattern in patterns)

    def handle(self, text):
        """Return a result for a recognized command, otherwise None."""
        value = (text or "").strip()

        google_match = re.match(
            rf"^{POLITE_PREFIX}(?:google|search google for|search on google for)\s+(.+)$",
            value, re.I
        )
        if google_match:
            query = google_match.group(1).strip()
            url = "https://www.google.com/search?q=" + quote_plus(query)
            opened = webbrowser.open(url)
            if opened:
                return f"Opened Google search results for: {query}\n{url}\nYou can inspect the results in your browser."
            return f"I couldn't open your browser automatically. Open this Google search link:\n{url}"

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
            lines.append(
                "These are search leads, not verified conclusions. Open the original sources "
                "and check their dates before relying on them."
            )
            return "\n".join(lines)

        laptop_match = re.match(
            rf"^{POLITE_PREFIX}(?:check my laptop|check this laptop|what(?:'s| is) open(?: on my laptop)?|show open windows|list open apps)$",
            value, re.I
        )
        if laptop_match:
            windows = list_visible_windows()
            if not windows:
                return "I checked the visible desktop windows, but Windows returned no titled windows."
            lines = ["Visible windows on your laptop:"]
            lines.extend(f"- {item['title']} (process ID {item['process_id']})" for item in windows)
            lines.append("\nI can currently inspect window titles, not read every app's private content.")
            return "\n".join(lines)

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
