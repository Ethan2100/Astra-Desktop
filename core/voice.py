"""Offline speech output for ASTRA using the Windows system voice."""
import threading
from PySide6.QtCore import QThread, Signal


class SpeechWorker(QThread):
    completed = Signal()
    failed = Signal(str)

    def __init__(self, text):
        super().__init__()
        self.text = (text or "").strip()
        self._stop_requested = threading.Event()
        self._engine = None

    def run(self):
        try:
            import pyttsx3

            engine = pyttsx3.init("sapi5")
            self._engine = engine
            engine.setProperty("rate", 178)
            engine.setProperty("volume", 1.0)

            # Prefer a Windows-installed female voice when one is available.
            voices = engine.getProperty("voices") or []
            for voice in voices:
                description = f"{getattr(voice, 'name', '')} {getattr(voice, 'id', '')}".lower()
                if "female" in description or "zira" in description or "hazel" in description:
                    engine.setProperty("voice", voice.id)
                    break

            if not self._stop_requested.is_set():
                engine.say(self.text[:6000])
                engine.runAndWait()
            engine.stop()
            self.completed.emit()
        except Exception as exc:
            self.failed.emit(
                "Speech could not start. Check that pyttsx3 is installed and Windows has a speech voice. "
                f"Details: {exc}"
            )
        finally:
            self._engine = None

    def stop(self):
        self._stop_requested.set()
        if self._engine is not None:
            try:
                self._engine.stop()
            except Exception:
                pass
