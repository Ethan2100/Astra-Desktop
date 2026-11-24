import unittest
from core.browser_agent import _validate_url


class BrowserAgentTests(unittest.TestCase):
    def test_accepts_http_and_https(self):
        self.assertEqual(_validate_url("https://example.com"), "https://example.com")
        self.assertEqual(_validate_url("http://localhost:3000"), "http://localhost:3000")

    def test_rejects_non_web_schemes(self):
        for url in ("file:///C:/Windows/win.ini", "javascript:alert(1)", "ftp://example.com"):
            with self.assertRaises(ValueError):
                _validate_url(url)

    def test_rejects_urls_with_embedded_credentials(self):
        with self.assertRaises(ValueError):
            _validate_url("https://user:password@example.com")


if __name__ == "__main__":
    unittest.main()
