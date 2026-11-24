# ASTRA Desktop

A local-first Windows desktop assistant built with Python, PySide6, SQLite and Ollama.

## Capabilities

- Floating animated desktop orb and Astra/JARVIS/Nova profiles.
- Local Ollama chat, separate histories and offline Windows speech.
- Live DuckDuckGo search and direct Google search.
- Visible browser automation through Selenium: open pages, read page text, click links and fill non-password fields.
- Windows UI Automation: inspect accessible controls, click named buttons and fill named non-password fields.
- User-file workspace: list/search/read/create/append/copy text and code files under the current Windows user's home folder.
- Basic keyboard/mouse input and allowlisted app launching.

## Setup

Requirements: Windows, Python, Ollama, and an installed copy of Microsoft Edge or Google Chrome.

Open PowerShell in the repository folder:

~~~powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
~~~

If PowerShell blocks activation:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
~~~

Selenium Manager automatically obtains a matching browser driver when first used. That first browser action requires internet access.

## Example commands

### Search and browser
- **google Python 3.15** — open real Google results in the default browser.
- **search official Python release** — search the web and return source URLs.
- **browse https://example.com** — open a visible ASTRA browser and read the page.
- **read page https://example.com**
- **click link Documentation on https://example.com**
- **fill field Search with ASTRA on https://example.com** — fills a field but never submits the form.

### Windows desktop
- **check my laptop** — list visible window titles.
- **inspect window Notepad** — read accessible UI controls and their names.
- **click button Save in Notepad**
- **type into field File name in Save As :: report.txt**
- **type in Notepad :: Hello from ASTRA**
- **press Ctrl+L in Chrome**
- **click 500, 300**
- **open Calculator**, **open Notepad**, **open File Explorer**, **open Task Manager**, **open Chrome**, **open Edge**

### Multi-step tasks
- **task: list files in Downloads || search official Python release** — runs up to eight supported commands in order and stops if a step fails.

### Files
- **list files in Downloads**
- **show me files in Documents**
- **list files recursively in Downloads**
- **find files named *.py in Downloads**
- **read file Downloads/notes.txt**
- **create file Documents/notes.txt :: Hello from ASTRA**
- **append to file Documents/notes.txt :: Another line**
- **copy file Downloads/report.txt to Documents/report.txt**

Relative file paths are resolved from the current Windows user's home folder. Absolute paths inside that home folder are also accepted.

## File and action boundaries

ASTRA currently allows text/code file operations inside the current user's home folder. It blocks Windows/AppData areas, hidden folders, browser data, credential-like files, private keys and password stores. It will not overwrite an existing file during file creation or copy. Recursive searches prune blocked folders.

Browser automation uses a separate ASTRA browser profile under %LOCALAPPDATA%\ASTRA\browser-profile; it does not read or reuse your personal Chrome/Edge saved passwords or cookies. Browser field filling does not submit forms.

ASTRA does not currently delete files, install software, make purchases, submit forms, run arbitrary shell commands, or bypass Windows security. Those high-impact actions require a separate explicit confirmation workflow before they are added. Some custom-drawn apps do not expose controls to Windows UI Automation, so inspection may be incomplete.

## Tests

~~~powershell
python -m unittest discover -s tests -v
~~~

## Local data

Database: %LOCALAPPDATA%\ASTRA\astra.db

Logs: %LOCALAPPDATA%\ASTRA\logs\astra.log

Ollama chat and Windows speech synthesis are local. Web search sends search queries to DuckDuckGo; browser navigation connects to the websites you request.
