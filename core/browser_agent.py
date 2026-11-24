"""Visible, persistent-profile browser automation for ASTRA."""
import os
from pathlib import Path
from urllib.parse import urlparse


def _validate_url(url):
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
        raise ValueError("Use a complete public http:// or https:// URL.")
    return parsed.geturl()


class BrowserAgent:
    """Launch a visible ASTRA-managed browser profile for each operation.

    Cookies are stored in ASTRA's own profile, not copied from the user's
    personal Chrome/Edge profile. Each call opens and closes the browser cleanly.
    """

    def __init__(self):
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        self.profile_dir = base / "ASTRA" / "browser-profile"
        self.profile_dir.mkdir(parents=True, exist_ok=True)

    def _open(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError(
                "Browser automation is not installed. Run: pip install playwright "
                "then python -m playwright install chromium"
            ) from exc

        playwright = sync_playwright().start()
        try:
            try:
                context = playwright.chromium.launch_persistent_context(
                    str(self.profile_dir), channel="msedge", headless=False,
                    viewport=None, args=["--start-maximized"]
                )
            except Exception:
                context = playwright.chromium.launch_persistent_context(
                    str(self.profile_dir), headless=False, viewport=None,
                    args=["--start-maximized"]
                )
        except Exception as exc:
            playwright.stop()
            raise RuntimeError(
                "ASTRA could not start its browser. Install the browser with "
                "'python -m playwright install chromium'."
            ) from exc
        page = context.pages[0] if context.pages else context.new_page()
        return playwright, context, page

    @staticmethod
    def _page_summary(page, heading):
        try:
            title = page.title()
        except Exception:
            title = "(title unavailable)"
        try:
            body = page.locator("body").inner_text(timeout=8000)
        except Exception:
            body = ""
        body = "\n".join(line.strip() for line in body.splitlines() if line.strip())
        return f"{heading}\nTitle: {title}\nURL: {page.url}\n\n{body[:14000] or '(No readable page text was found.)'}"

    def open_and_read(self, url):
        url = _validate_url(url)
        playwright, context, page = self._open()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(900)
            return self._page_summary(page, "Opened the page in ASTRA's visible browser:")
        finally:
            context.close()
            playwright.stop()

    def click_link_and_read(self, url, link_text):
        url = _validate_url(url)
        if not link_text or len(link_text) > 180:
            raise ValueError("Enter a short link name.")
        playwright, context, page = self._open()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            link = page.get_by_role("link", name=link_text, exact=False).first
            link.click(timeout=10000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            page.wait_for_timeout(500)
            return self._page_summary(page, f"Clicked the link '{link_text}' and opened:")
        finally:
            context.close()
            playwright.stop()

    def fill_field(self, url, field_name, value):
        url = _validate_url(url)
        if not field_name or len(field_name) > 120:
            raise ValueError("Enter the field label or placeholder.")
        if len(value) > 4000:
            raise ValueError("Text is too long for one field operation.")
        playwright, context, page = self._open()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            field = page.get_by_label(field_name, exact=False).first
            if field.count() == 0:
                field = page.get_by_placeholder(field_name, exact=False).first
            field.fill(value, timeout=10000)
            return (
                f"Filled the '{field_name}' field on {page.url}. "
                "I did not submit the form."
            )
        finally:
            context.close()
            playwright.stop()
