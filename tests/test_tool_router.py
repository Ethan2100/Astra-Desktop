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

    def test_unknown_app_returns_supported_list_without_launching(self):
        response = self.router.handle("open an unknown application")
        self.assertIn("Notepad", response)
        self.assertIn("Chrome", response)


if __name__ == "__main__":
    unittest.main()
