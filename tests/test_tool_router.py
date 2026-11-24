import unittest
from unittest.mock import patch
from core.tool_router import ToolRouter
from core.web_search import SearchResult


class ToolRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = ToolRouter()

    def test_recognizes_natural_search_commands(self):
        self.assertTrue(self.router.is_command("search Re:Zero season 5"))
        self.assertTrue(self.router.is_command("search the web for Python release"))
        self.assertTrue(self.router.is_command("google Crunchyroll Kenya"))
        self.assertTrue(self.router.is_command("search on Google for weather"))

    def test_recognizes_laptop_inspection(self):
        self.assertTrue(self.router.is_command("check my laptop"))
        self.assertTrue(self.router.is_command("what's open on my laptop"))

    def test_unrecognized_chat_is_not_routed(self):
        self.assertFalse(self.router.is_command("What do you think about Re:Zero?"))

    @patch("core.tool_router.WebSearch.search")
    def test_search_result_includes_real_source_url(self, mocked_search):
        mocked_search.return_value = [
            SearchResult("Official announcement", "https://example.com/news", "A source snippet.")
        ]
        response = self.router.handle("search Re:Zero season 5")
        self.assertIn("Official announcement", response)
        self.assertIn("https://example.com/news", response)
        self.assertIn("not verified conclusions", response)

    @patch("core.tool_router.webbrowser.open", return_value=True)
    def test_google_opens_real_google_search(self, mocked_open):
        response = self.router.handle("google Python 3.15")
        self.assertIn("Google search results", response)
        self.assertIn("https://www.google.com/search?q=Python+3.15", mocked_open.call_args.args[0])

    @patch("core.tool_router.list_visible_windows")
    def test_laptop_check_reports_visible_windows(self, mocked_windows):
        mocked_windows.return_value = [{"title": "ASTRA Desktop", "process_id": 1234}]
        response = self.router.handle("check my laptop")
        self.assertIn("ASTRA Desktop", response)
        self.assertIn("1234", response)

    def test_unknown_app_returns_supported_list_without_launching(self):
        response = self.router.handle("open an unknown application")
        self.assertIn("Notepad", response)
        self.assertIn("Chrome", response)


if __name__ == "__main__":
    unittest.main()
