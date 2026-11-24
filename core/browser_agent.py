"""Visible Selenium browser automation with an ASTRA-only persistent profile."""
import os
from pathlib import Path
from urllib.parse import urlparse


def _validate_url(url):
    parsed = urlparse((url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username:
        raise ValueError("Use a complete public http:// or https:// URL.")
    return parsed.geturl()


def _xpath_literal(value):
    if "'" not in value:
        return "'" + value + "'"
    if '"' not in value:
        return '"' + value + '"'
    pieces = value.split("'")
    return "concat(" + ", \"'\", ".join("'" + piece + "'" for piece in pieces) + ")"


class BrowserAgent:
    """Open a visible browser using a separate ASTRA profile, not personal browser data."""

    def __init__(self):
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        self.edge_profile = base / "ASTRA" / "edge-profile"
        self.chrome_profile = base / "ASTRA" / "chrome-profile"
        self.edge_profile.mkdir(parents=True, exist_ok=True)
        self.chrome_profile.mkdir(parents=True, exist_ok=True)

    def _open(self):
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options as EdgeOptions
            from selenium.webdriver.chrome.options import Options as ChromeOptions
        except ImportError as exc:
            raise RuntimeError("Browser automation is not installed. Run: pip install selenium") from exc

        errors = []
        edge_options = EdgeOptions()
        edge_options.add_argument(f"--user-data-dir={self.edge_profile}")
        edge_options.add_argument("--profile-directory=Default")
        edge_options.add_argument("--start-maximized")
        edge_options.add_argument("--disable-notifications")
        try:
            return webdriver.Edge(options=edge_options)
        except Exception as exc:
            errors.append(f"Edge: {exc}")

        chrome_options = ChromeOptions()
        chrome_options.add_argument(f"--user-data-dir={self.chrome_profile}")
        chrome_options.add_argument("--profile-directory=Default")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        try:
            return webdriver.Chrome(options=chrome_options)
        except Exception as exc:
            errors.append(f"Chrome: {exc}")
        raise RuntimeError(
            "ASTRA could not start Edge or Chrome. Make sure one is installed and connected to the internet "
            "so Selenium Manager can obtain its matching driver. " + " | ".join(errors)
        )

    @staticmethod
    def _page_summary(driver, heading):
        from selenium.webdriver.common.by import By
        try:
            title = driver.title
        except Exception:
            title = "(title unavailable)"
        try:
            body = driver.find_element(By.TAG_NAME, "body").text
        except Exception:
            body = ""
        body = "\n".join(line.strip() for line in body.splitlines() if line.strip())
        return (
            f"{heading}\nTitle: {title}\nURL: {driver.current_url}\n\n"
            f"{body[:14000] or '(No readable page text was found.)'}"
        )

    def open_and_read(self, url):
        from selenium.webdriver.support.ui import WebDriverWait
        url = _validate_url(url)
        driver = self._open()
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                lambda browser: browser.execute_script("return document.readyState") in ("interactive", "complete")
            )
            return self._page_summary(driver, "Opened the page in ASTRA's visible browser:")
        finally:
            driver.quit()

    def click_link_and_read(self, url, link_text):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        url = _validate_url(url)
        if not link_text or len(link_text) > 180:
            raise ValueError("Enter a short link name.")
        driver = self._open()
        try:
            driver.get(url)
            xpath = f"//a[contains(normalize-space(string(.)), {_xpath_literal(link_text)})]"
            link = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, xpath)))
            link.click()
            WebDriverWait(driver, 20).until(
                lambda browser: browser.execute_script("return document.readyState") in ("interactive", "complete")
            )
            return self._page_summary(driver, f"Clicked the link '{link_text}' and opened:")
        finally:
            driver.quit()

    def fill_field(self, url, field_name, value):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        url = _validate_url(url)
        if not field_name or len(field_name) > 120:
            raise ValueError("Enter the field label or placeholder.")
        if len(value) > 4000:
            raise ValueError("Text is too long for one field operation.")
        driver = self._open()
        try:
            driver.get(url)
            literal = _xpath_literal(field_name)
            xpath = (
                f"//input[contains(@placeholder, {literal}) or @aria-label={literal}]"
                f" | //textarea[contains(@placeholder, {literal}) or @aria-label={literal}]"
                f" | //label[contains(normalize-space(string(.)), {literal})]/following::input[1]"
                f" | //label[contains(normalize-space(string(.)), {literal})]/following::textarea[1]"
            )
            field = WebDriverWait(driver, 15).until(EC.visibility_of_element_located((By.XPATH, xpath)))
            field.clear()
            field.send_keys(value)
            return f"Filled the '{field_name}' field on {driver.current_url}. I did not submit the form."
        finally:
            driver.quit()
