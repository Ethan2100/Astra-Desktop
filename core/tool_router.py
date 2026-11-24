"""Deterministic, permission-bounded commands for ASTRA."""
import re
import subprocess
import webbrowser
from urllib.parse import urlparse, quote_plus
from core.web_search import WebSearch
from core.desktop_control import list_visible_windows


APP_ALLOWLIST = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
}


class ToolRouter:
    def __init__(self):
        self.web = WebSearch()

    def is_command(self, text):
        value = (text or "").strip()
        patterns = (
            r"^(?:search(?: the web)?(?: for)?|look up(?: online)?|find online)\s+.+$",
            r"^(?:google|search google for|search on google for)\s+.+$",
            r"^(?:open|launch|start)\s+.+$",
            r"^(?:check my laptop|check this laptop|what(?:'s| is) open(?: on my laptop)?|show open windows|list open apps)$",
        )
        return any(re.match(pattern, value, re.I) for pattern in patterns)

    def handle(self, text):
        """Return a result for a recognized command, otherwise None."""
        value = (text or "").strip()

        google_match = re.match(
            r"^(?:google|search google for|search on google for)\s+(.+)$", value, re.I
        )
        if google_match:
            query = google_match.group(1).strip()
            if not query:
                return "Tell me what you want me to search for."
            url = "https://www.google.com/search?q=" + quote_plus(query)
            opened = webbrowser.open(url)
            if opened:
                return f"Opened Google search results for: {query}\n{url}\nYou can inspect the results in your browser."
            return f"I couldn't open your browser automatically. Open this Google search link:\n{url}"

        search_match = re.match(
            r"^(?:search(?: the web)?(?: for)?|look up(?: online)?|find online)\s+(.+)$",
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

        if re.match(
            r"^(?:check my laptop|check this laptop|what(?:'s| is) open(?: on my laptop)?|show open windows|list open apps)$",
            value, re.I
        ):
            windows = list_visible_windows()
            if not windows:
                return "I checked the visible desktop windows, but Windows returned no titled windows."
            lines = ["Visible windows on your laptop:"]
            lines.extend(f"- {item['title']} (process ID {item['process_id']})" for item in windows)
            lines.append("\nI can currently inspect window titles, not read every app's private content.")
            return "\n".join(lines)

        app_match = re.match(r"^(?:open|launch|start)\s+(.+)$", value, re.I)
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
