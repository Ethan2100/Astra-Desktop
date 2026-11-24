"""Offline speech output using Windows' built-in .NET Speech API."""
import base64
import subprocess
from PySide6.QtCore import QThread, Signal


class SpeechWorker(QThread):
    completed = Signal()
    failed = Signal(str)

    def __init__(self, text):
        super().__init__()
        self.text = (text or "").strip()
        self._process = None

    def run(self):
        if not self.text:
            self.completed.emit()
            return

        try:
            encoded_text = base64.b64encode(self.text[:6000].encode("utf-8")).decode("ascii")
            script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 0
$synth.Volume = 100
$female = $synth.GetInstalledVoices() | Where-Object {{ $_.VoiceInfo.Gender -eq 'Female' }} | Select-Object -First 1
if ($female) {{ $synth.SelectVoice($female.VoiceInfo.Name) }}
$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String('{encoded_text}'))
$synth.Speak($text)
$synth.Dispose()
"""
            encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self._process = subprocess.Popen(
                [
                    "powershell.exe", "-NoLogo", "-NoProfile",
                    "-NonInteractive", "-EncodedCommand", encoded_script
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=flags,
            )
            _stdout, stderr = self._process.communicate()
            if self._process.returncode != 0:
                raise RuntimeError(stderr.strip() or "Windows speech synthesis returned an error.")
            self.completed.emit()
        except Exception as exc:
            self.failed.emit(
                "Windows could not speak this reply. Check that Windows has a speech voice installed. "
                f"Details: {exc}"
            )
        finally:
            self._process = None

    def stop(self):
        if self._process is not None and self._process.poll() is None:
            try:
                self._process.terminate()
            except OSError:
                pass
