import tempfile
import unittest
from pathlib import Path

from core.workspace_files import WorkspaceFiles


class WorkspaceFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.files = WorkspaceFiles(self.home)

    def tearDown(self):
        self.temp.cleanup()

    def test_create_read_and_append_text_file(self):
        folder = self.home / "Documents"
        folder.mkdir()
        target = folder / "notes.md"
        self.files.create_file(str(target), "Hello ASTRA")
        self.assertIn("Hello ASTRA", self.files.read_file(str(target)))
        self.files.append_file(str(target), "\nSecond line")
        self.assertIn("Second line", target.read_text(encoding="utf-8"))

    def test_refuses_to_overwrite_existing_file(self):
        target = self.home / "already.txt"
        target.write_text("keep me", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            self.files.create_file(str(target), "replace me")
        self.assertEqual(target.read_text(encoding="utf-8"), "keep me")

    def test_refuses_paths_outside_home(self):
        outside = self.home.parent / "outside.txt"
        with self.assertRaises(PermissionError):
            self.files.read_file(str(outside))

    def test_blocks_appdata_and_hidden_directories(self):
        private = self.home / "AppData" / "secret.txt"
        private.parent.mkdir()
        private.write_text("private", encoding="utf-8")
        with self.assertRaises(PermissionError):
            self.files.read_file(str(private))
        hidden = self.home / ".ssh" / "id_rsa"
        hidden.parent.mkdir()
        hidden.write_text("private key", encoding="utf-8")
        with self.assertRaises(PermissionError):
            self.files.read_file(str(hidden))

    def test_blocks_credential_named_files(self):
        target = self.home / "passwords.txt"
        target.write_text("not for ASTRA", encoding="utf-8")
        with self.assertRaises(PermissionError):
            self.files.read_file(str(target))

    def test_lists_and_finds_files(self):
        folder = self.home / "Downloads"
        folder.mkdir()
        (folder / "report.txt").write_text("data", encoding="utf-8")
        listing = self.files.list_files("Downloads")
        self.assertIn("report.txt", listing)
        found = self.files.find_files("*.txt", "Downloads")
        self.assertIn("report.txt", found)

    def test_copy_file_without_overwriting(self):
        source = self.home / "source.txt"
        destination = self.home / "copy.txt"
        source.write_text("copy me", encoding="utf-8")
        self.files.copy_file(str(source), str(destination))
        self.assertEqual(destination.read_text(encoding="utf-8"), "copy me")
        with self.assertRaises(FileExistsError):
            self.files.copy_file(str(source), str(destination))


if __name__ == "__main__":
    unittest.main()
