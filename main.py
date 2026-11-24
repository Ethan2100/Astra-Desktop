import logging
import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.orb import AstraOrb
from core.logging_config import configure_logging
from core.database import Database
from core.config import APP_NAME

def main():
    configure_logging()
    log = logging.getLogger(__name__)
    database = Database()
    database.initialize()

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow(database)
    orb = AstraOrb()

    def open_chat():
        window.show()
        window.raise_()
        window.activateWindow()

    window.state_changed.connect(orb.set_state)
    orb.open_chat_requested.connect(open_chat)
    window.show()
    orb.show()
    log.info("ASTRA Phase 3 started")
    app.aboutToQuit.connect(orb.stop)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
