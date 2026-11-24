import unittest
from unittest.mock import patch

from core.tool_router import ToolRouter
from core.web_search import SearchResult


class ToolRouterTests(unittest.TestCase):
    def setUp(self):
        self.router = ToolRouter()

    def test_recognizes_search_and_google_commands(self):
        for command in (
            "search Re:Zero season 5",
            "search the web for Python release",
            "google Crunchyroll Kenya",
            "search on Google for weather",
            "Can you search Google for Python 3.15?",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.router.is_command(command))

    def test_recognizes_laptop_and_ui_automation(self):
        for command in (
            "check my laptop",
            "what's open on my laptop",
            "please check my laptop",
            "inspect window Notepad",
            "read controls in Calculator",
            "click button Save in Notepad",
            "type into field File name in Save As :: hello.txt",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.router.is_command(command))

    def test_recognizes_browser_commands(self):
        for command in (
            "browse https://example.com",
            "read page https://example.com",
            "open browser to https://example.com",
            "click link Documentation on https://example.com",
            "fill field Search with ASTRA on https://example.com",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.router.is_command(command))

    def test_recognizes_file_commands(self):
        for command in (
            "list files in Downloads",
            "show me files in Documents",
            "what files are in Desktop",
            "list files recursively in Downloads",
            "read file Downloads/notes.txt",
            "read the file Downloads/notes.txt",
            "create file Downloads/new.txt :: Hello",
            "make a file Downloads/new.txt :: Hello",
            "append to file Downloads/notes.txt :: More",
            "find files named *.py in Downloads",
            "copy file Downloads/a.txt to Documents/a.txt",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.router.is_command(command))

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
        self.assertIn("Search results are leads", response)

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

    @patch("core.tool_router.BrowserAgent.open_and_read", return_value="page contents")
    def test_browse_command_opens_and_reads_page(self, mocked_browse):
        response = self.router.handle("browse https://example.com")
        self.assertEqual(response, "page contents")
        mocked_browse.assert_called_once_with("https://example.com")

    @patch("core.tool_router.WorkspaceFiles.list_files", return_value="report.txt")
    def test_list_files_command_uses_workspace(self, mocked_list):
        response = self.router.handle("show me files in Downloads")
        self.assertEqual(response, "report.txt")
        mocked_list.assert_called_once_with("Downloads")

    @patch("core.tool_router.type_into_focused_window", return_value="Notepad")
    def test_type_command_targets_focused_window(self, mocked_type):
        response = self.router.handle("type Hello there")
        self.assertIn("Notepad", response)
        mocked_type.assert_called_once_with("Hello there")

    def test_unknown_app_returns_supported_list_without_launching(self):
        response = self.router.handle("open an unknown application")
        self.assertIn("Notepad", response)
        self.assertIn("Chrome", response)


if __name__ == "__main__":
    unittest.main()
