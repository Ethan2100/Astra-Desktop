"""Deterministic, permission-bounded commands for ASTRA Phase 4."""
import re
import subprocess
import webbrowser
from urllib.parse import urlparse
from core.web_search import WebSearch


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

    def handle(self, text):
        """Return a result for a recognized command, otherwise None."""
        value = (text or "").strip()
        lower = value.lower()

        search_match = re.match(r"^(?:search(?: the web)? for|google|look up online|find online)\\s+(.+)$", value, re.I)
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
            lines.append("These are search results, not verified conclusions. Open the sources and check publication dates before relying on them.")
            return "\\n".join(lines)

        app_match = re.match(r"^(?:open|launch|start)\\s+(.+)$", value, re.I)
        if app_match:
            requested = app_match.group(1).strip().lower()
            if requested in APP_ALLOWLIST:
                try:
                    subprocess.Popen([APP_ALLOWLIST[requested]], shell=False)
                    return f"Opened {requested}."
                except OSError as exc:
                    return f"I couldn't launch {requested}: {exc}"
            if requested in {"chrome", "google chrome", "edge", "microsoft edge"}:
                try:
                    webbrowser.open("https://www.google.com" if "chrome" in requested else "https://www.microsoft.com/edge")
                    return f"Sent a request to open {requested} in your default browser."
                except Exception as exc:
                    return f"I couldn't open the browser: {exc}"
            if requested.startswith(("https://", "http://")):
                parsed = urlparse(requested)
                if parsed.scheme in {"http", "https"} and parsed.netloc:
                    webbrowser.open(requested)
                    return f"Opened {requested} in your default browser."
            return ("I can currently launch: Notepad, Calculator, Paint, File Explorer and Task Manager. "
                    "Browser navigation and more desktop controls are being added next.")

        return None
