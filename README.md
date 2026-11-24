# ASTRA Desktop

A local-first Windows desktop assistant built with Python, PySide6, SQLite and Ollama.

## Current capabilities
- Floating animated desktop orb.
- Astra, JARVIS and Nova assistant profiles.
- Local Ollama chat with separate conversation histories.
- SQLite storage for conversations and assistant-specific memory notes.
- Live DuckDuckGo web search with source URLs.
- Google search opens real Google results in the default browser.
- Safe launch commands for selected Windows applications and websites.
- Read-only inspection of visible top-level laptop window titles.
- Offline spoken replies using installed Windows SAPI5 voices.

## Requirements
- Windows 10 or 11
- Python with a compatible PySide6 wheel
- Ollama installed and running for local AI chat
- An Ollama model such as \`qwen3.5:2b\` or \`gemma3:1b\`
- Windows speech voices for offline speech output

## Setup
Open PowerShell in the repository folder:

\`\`\`powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
\`\`\`

If PowerShell blocks activation:

\`\`\`powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
\`\`\`

## Commands in ASTRA
- \`google Python 3.15\` — opens a Google results page in your browser.
- \`search Re:Zero season 5 official announcement\` — returns live DuckDuckGo results with source URLs.
- \`search the web for Crunchyroll Kenya\`
- \`check my laptop\` — lists visible window titles and process IDs.
- \`what's open on my laptop\`
- \`open Notepad\`
- \`open Calculator\`
- \`open Paint\`
- \`open File Explorer\`
- \`open Task Manager\`
- \`open Chrome\`
- \`open Edge\`
- \`open https://example.com\`

Turn on **Speak replies** to hear assistant and tool replies. **Speak latest** repeats the last reply; **Stop voice** requests playback cancellation. Speech uses the local Windows voice engine and does not send text to a cloud TTS service.

## Tests
\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

## Local data and privacy
The SQLite database is stored outside the source folder:
\`%LOCALAPPDATA%\ASTRA\astra.db\`

Logs are stored in:
\`%LOCALAPPDATA%\ASTRA\logs\astra.log\`

Ollama chat and speech output are local. Google search opens Google in your browser. DuckDuckGo search sends the query to DuckDuckGo.

## Current limitations
Laptop inspection currently reads visible window titles only; it does not read arbitrary screen contents. ASTRA can type text into the focused window, press a limited safe key list, and click a coordinate explicitly supplied by the user. App launching is allowlisted. It does not yet have full browser DOM control, arbitrary file editing, or autonomous multi-step desktop workflows. Those need a separate permission-aware automation layer and tests. Never give a small language model unrestricted shell access or permission to delete files without confirmation.
