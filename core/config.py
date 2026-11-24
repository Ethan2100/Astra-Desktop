import os
from pathlib import Path

APP_NAME = "ASTRA"
APP_VERSION = "0.1.0"
APP_DATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
DATABASE_PATH = APP_DATA_DIR / "astra.db"
LOG_PATH = APP_DATA_DIR / "logs" / "astra.log"
