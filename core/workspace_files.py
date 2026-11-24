"""Permission-bounded file operations inside the current Windows user's home."""
from pathlib import Path
import fnmatch
import shutil


BLOCKED_PARTS = {
    "appdata", ".ssh", ".aws", ".azure", ".gnupg", ".config",
    "cookies", "login data", "web data", "browser profile",
    "credential", "credentials", "passwords", "secrets",
}
BLOCKED_NAMES = {
    "ntuser.dat", "ntuser.ini", "desktop.ini",
}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".kdbx", ".keystore"}
TEXT_SUFFIXES = {
    ".txt", ".md", ".py", ".js", ".jsx", ".ts", ".tsx", ".json",
    ".csv", ".html", ".htm", ".css", ".yaml", ".yml", ".toml",
    ".ini", ".log", ".xml", ".sql", ".ps1", ".bat", ".sh",
}
MAX_TEXT_BYTES = 1_000_000


class WorkspaceFiles:
    """Operate on user files while excluding Windows/app secrets and system areas."""

    def __init__(self, home=None):
        self.home = Path(home or Path.home()).expanduser().resolve()

    def _safe_path(self, raw, must_exist=False):
        if not raw or len(str(raw)) > 1000:
            raise ValueError("Enter a valid file or folder path.")
        candidate = Path(str(raw)).expanduser()
        if not candidate.is_absolute():
            candidate = self.home / candidate
        path = candidate.resolve(strict=must_exist)
        try:
            relative = path.relative_to(self.home)
        except ValueError as exc:
            raise PermissionError("ASTRA can only access files inside your Windows user folder.") from exc

        parts = [part.casefold() for part in relative.parts]
        if any(part in BLOCKED_PARTS or part.startswith(".") for part in parts):
            raise PermissionError("That folder is private or restricted and is not available to ASTRA.")
        if path.name.casefold() in BLOCKED_NAMES or path.suffix.casefold() in BLOCKED_SUFFIXES:
            raise PermissionError("That file type or system file is restricted.")
        if any(token in path.name.casefold() for token in ("password", "credential", "secret", "token", "id_rsa")):
            raise PermissionError("Files that appear to contain credentials are not available to ASTRA.")
        return path

    def list_files(self, folder, recursive=False, limit=100):
        path = self._safe_path(folder, must_exist=True)
        if not path.is_dir():
            raise ValueError("That path is not a folder.")
        iterator = path.rglob("*") if recursive else path.iterdir()
        results = []
        for item in iterator:
            try:
                safe = self._safe_path(str(item), must_exist=True)
            except (PermissionError, OSError, ValueError):
                continue
            if safe.is_file():
                results.append(f"[FILE] {safe.name}")
            elif safe.is_dir():
                results.append(f"[DIR]  {safe.name}/")
            if len(results) >= max(1, min(limit, 200)):
                break
        return f"Contents of {path}:\n" + ("\n".join(results) if results else "(No accessible items found.)")

    def read_file(self, raw_path):
        path = self._safe_path(raw_path, must_exist=True)
        if not path.is_file():
            raise ValueError("That path is not a file.")
        if path.suffix.casefold() not in TEXT_SUFFIXES:
            raise PermissionError("ASTRA currently reads text/code formats only.")
        if path.stat().st_size > MAX_TEXT_BYTES:
            raise ValueError("That file is larger than the 1 MB reading limit.")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = path.read_text(encoding="utf-8-sig")
        return f"File: {path}\n\n{content[:18000]}"

    def create_file(self, raw_path, content):
        path = self._safe_path(raw_path)
        if path.suffix.casefold() not in TEXT_SUFFIXES:
            raise PermissionError("ASTRA currently creates text/code files only.")
        if len(content.encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("New file content is larger than the 1 MB limit.")
        if not path.parent.exists() or not path.parent.is_dir():
            raise ValueError("The parent folder does not exist. Create the folder first.")
        if path.exists():
            raise FileExistsError("That file already exists. ASTRA will not overwrite it automatically.")
        path.write_text(content, encoding="utf-8", newline="\n")
        return f"Created file: {path} ({path.stat().st_size} bytes)."

    def append_file(self, raw_path, content):
        path = self._safe_path(raw_path, must_exist=True)
        if not path.is_file() or path.suffix.casefold() not in TEXT_SUFFIXES:
            raise PermissionError("ASTRA can append only to an existing text/code file.")
        if path.stat().st_size + len(content.encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("The updated file would exceed the 1 MB limit.")
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        return f"Appended {len(content)} characters to {path}."

    def find_files(self, pattern, folder, limit=100):
        path = self._safe_path(folder, must_exist=True)
        if not path.is_dir():
            raise ValueError("That path is not a folder.")
        results = []
        for item in path.rglob("*"):
            try:
                safe = self._safe_path(str(item), must_exist=True)
            except (PermissionError, OSError, ValueError):
                continue
            if safe.is_file() and fnmatch.fnmatch(safe.name.casefold(), pattern.casefold()):
                results.append(str(safe))
                if len(results) >= max(1, min(limit, 200)):
                    break
        return f"Files matching '{pattern}' in {path}:\n" + ("\n".join(results) if results else "(No matches.)")

    def copy_file(self, source, destination):
        src = self._safe_path(source, must_exist=True)
        dst = self._safe_path(destination)
        if not src.is_file():
            raise ValueError("Copy source must be a file.")
        if dst.exists():
            raise FileExistsError("Destination already exists; ASTRA will not overwrite it.")
        if not dst.parent.exists():
            raise ValueError("Destination folder does not exist.")
        shutil.copy2(src, dst)
        return f"Copied {src} to {dst}."
