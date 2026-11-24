# ASTRA Desktop — Phase 1 Foundation

A lightweight Windows desktop foundation built with Python, PySide6 and SQLite.

## Requirements
- Windows 10/11
- Python 3.11+ (use a Python version with an available PySide6 wheel)
- PowerShell

## Setup
Open PowerShell in this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Tests
```powershell
python -m unittest discover -s tests -v
```

## Data and privacy
The SQLite database is stored outside this source folder:
`%LOCALAPPDATA%\ASTRA\astra.db`

Logs are stored in:
`%LOCALAPPDATA%\ASTRA\logs\astra.log`

This phase does not connect to the internet, call cloud APIs, use the microphone,
or inspect desktop contents. Those features will be added in later phases with
explicit controls.

## Backup
Close ASTRA, then copy `%LOCALAPPDATA%\ASTRA` somewhere safe to back up local
memory and settings. Back up the source repository separately with Git.
