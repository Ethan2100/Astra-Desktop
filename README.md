# ASTRA Desktop

A local-first Windows desktop assistant built with Python, PySide6, SQLite and Ollama.

## Current capabilities
- Floating animated desktop orb.
- Astra, JARVIS and Nova assistant profiles.
- Local Ollama chat with separate conversation histories.
- SQLite storage for conversations and assistant-specific memory notes.
- Phase 4 live DuckDuckGo web search with source URLs.
- Safe launch commands for selected Windows applications and browsers.

## Requirements
- Windows 10 or 11
- Python with a compatible PySide6 wheel
- Ollama installed and running for local AI chat
- An Ollama model such as \`gemma3:1b\`

## Setup
Open PowerShell in the repository folder:

\`\`\`powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
\`\`\`

If PowerShell blocks activation:

\`\`\`powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\\.venv\\Scripts\\Activate.ps1
\`\`\`

## Phase 4 commands
Enter these directly in the ASTRA chat:

- \`search Re:Zero season 5 official announcement\`
- \`search the web for Crunchyroll Kenya Re:Zero\`
- \`google latest Python release\`
- \`open Notepad\`
- \`open Calculator\`
- \`open Paint\`
- \`open File Explorer\`
- \`open Task Manager\`
- \`open Chrome\`
- \`open Edge\`
- \`open https://example.com\`

Search results are live links from DuckDuckGo. They are not automatically verified facts: inspect the original pages and publication dates before relying on them.

## Tests
\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

## Local data and privacy
The SQLite database is stored outside the source folder:
\`%LOCALAPPDATA%\\ASTRA\\astra.db\`

Logs are stored in:
\`%LOCALAPPDATA%\\ASTRA\\logs\\astra.log\`

Ollama chat is local. Web search sends the search query to DuckDuckGo. This phase does not provide unrestricted shell access, file deletion, or arbitrary mouse/keyboard automation.

## Safety direction
Desktop actions are being introduced through a bounded tool registry. Destructive or consequential actions will require explicit confirmation. Do not store API keys, passwords or other secrets in the repository.
