import logging
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTextEdit, QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QMessageBox, QCheckBox
)
from providers.ollama_provider import OllamaProvider, OllamaError
from core.tool_router import ToolRouter
from core.voice import SpeechWorker
from datetime import datetime

log = logging.getLogger(__name__)

ASSISTANT_PROMPTS = {
    "astra": (
        "You are Astra, a capable, natural, warm and witty desktop assistant. Be helpful first. "
        "Use occasional playful teasing and subtle tsundere energy, but never be hostile, repetitive, "
        "theatrical, or pretend to have human feelings. Be concise unless detail is useful. "
        "You run inside a Windows desktop app. You can use built-in tools when the user asks you to "
        "search/google something, open an app or website, or check visible laptop windows. "
        "Tell the user to start a tool request with 'google ...', 'search ...', 'open ...', or "
        "'check my laptop' when needed. Never claim you inspected the screen, searched, opened, "
        "changed, saved, or completed anything unless the tool result confirms it. "
        "You can type literal text into the focused window, press a small allowlist of keys, and click a user-specified screen coordinate. You cannot yet read all screen contents or edit arbitrary files."
    ),
    "jarvis": (
        "You are JARVIS, a composed, precise and professional Windows desktop assistant. "
        "Be courteous, practical and concise. You can use built-in tools for Google searches, "
        "web search, opening allowlisted apps/sites and listing visible laptop windows. "
        "Never claim an action succeeded without a tool result. Do not imply unrestricted desktop access."
    ),
    "nova": (
        "You are Nova, a friendly, curious and creative desktop assistant. Be encouraging, imaginative "
        "and clear. You can use built-in tools for Google searches, web search, opening allowlisted "
        "apps/sites and listing visible laptop windows. Never claim an action succeeded without a tool result."
    )
}


class ChatWorker(QThread):
    finished_text = Signal(str)
    failed = Signal(str)

    def __init__(self, provider, messages, model):
        super().__init__()
        self.provider = provider
        self.messages = messages
        self.model = model

    def run(self):
        try:
            self.finished_text.emit(self.provider.chat(self.messages, self.model))
        except Exception as exc:
            self.failed.emit(str(exc))


class ToolWorker(QThread):
    finished_text = Signal(str)
    failed = Signal(str)

    def __init__(self, router, command):
        super().__init__()
        self.router = router
        self.command = command

    def run(self):
        try:
            result = self.router.handle(self.command)
            self.finished_text.emit(result or "I didn't recognize that tool command.")
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QWidget):
    state_changed = Signal(str)

    def __init__(self, database):
        super().__init__()
        self.database = database
        self.provider = OllamaProvider()
        self.tool_router = ToolRouter()
        self.tool_worker = None
        self.speech_worker = None
        self.last_assistant_text = ""
        self.assistant_id = "astra"
        self.conversation_id = None
        self.worker = None
        self.setWindowTitle("ASTRA Desktop")
        self.resize(1050, 720)
        self.setMinimumSize(780, 560)
        self.setStyleSheet("""
            QWidget { background:#0b1020; color:#e8f0ff; font-family:'Segoe UI'; }
            QFrame#Panel { background:#10182b; border:1px solid #243653; border-radius:13px; }
            QLabel#Brand { color:#7dd3fc; font-size:22px; font-weight:700; }
            QLabel#Muted { color:#91a4c2; }
            QPushButton { background:#172943; color:#e8f0ff; border:1px solid #294466; border-radius:8px; padding:9px 12px; }
            QPushButton:hover { background:#214064; }
            QPushButton:disabled { color:#718096; background:#111a2a; }
            QLineEdit, QTextEdit, QComboBox, QListWidget { background:#0c1527; border:1px solid #263b5c; border-radius:8px; padding:9px; selection-background-color:#17618a; }
            QTextEdit#Transcript { font-size:14px; }
            QComboBox QAbstractItemView { background:#10182b; selection-background-color:#17618a; }
            QCheckBox { color:#c6d5eb; spacing:7px; }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(16,16,16,16)
        root.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("Panel")
        sidebar.setFixedWidth(235)
        side = QVBoxLayout(sidebar)
        brand = QLabel("✦ ASTRA")
        brand.setObjectName("Brand")
        side.addWidget(brand)
        tagline = QLabel("LOCAL DESKTOP ASSISTANT")
        tagline.setObjectName("Muted")
        side.addWidget(tagline)
        side.addSpacing(12)

        side.addWidget(QLabel("ASSISTANT"))
        self.assistant_picker = QComboBox()
        self.assistant_picker.addItem("Astra", "astra")
        self.assistant_picker.addItem("JARVIS", "jarvis")
        self.assistant_picker.addItem("Nova", "nova")
        self.assistant_picker.currentIndexChanged.connect(self._assistant_changed)
        side.addWidget(self.assistant_picker)

        side.addWidget(QLabel("MODEL"))
        self.model_picker = QComboBox()
        self.model_picker.setEditable(True)
        self.model_picker.addItem("qwen3.5:2b")
        self.model_picker.addItem("gemma3:1b")
        self.model_picker.setCurrentText("qwen3.5:2b")
        side.addWidget(self.model_picker)
        self.refresh_button = QPushButton("Refresh local models")
        self.refresh_button.clicked.connect(self.refresh_models)
        side.addWidget(self.refresh_button)

        self.new_chat_button = QPushButton("+  New chat")
        self.new_chat_button.clicked.connect(self.new_chat)
        side.addWidget(self.new_chat_button)
        side.addWidget(QLabel("RECENT CHATS"))
        self.history = QListWidget()
        self.history.itemClicked.connect(self._load_conversation)
        side.addWidget(self.history, 1)

        self.connection_label = QLabel("● Checking Ollama…")
        self.connection_label.setObjectName("Muted")
        side.addWidget(self.connection_label)

        content = QFrame()
        content.setObjectName("Panel")
        body = QVBoxLayout(content)
        body.setContentsMargins(18,16,18,16)
        header = QHBoxLayout()
        self.heading = QLabel("Astra")
        self.heading.setStyleSheet("font-size:20px;font-weight:650;")
        header.addWidget(self.heading)
        header.addStretch(1)
        self.status = QLabel("LOCAL AI")
        self.status.setObjectName("Muted")
        header.addWidget(self.status)
        body.addLayout(header)

        self.transcript = QTextEdit()
        self.transcript.setObjectName("Transcript")
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("Your conversation will appear here.")
        body.addWidget(self.transcript, 1)

        composer = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Message Astra…")
        self.message_input.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        composer.addWidget(self.message_input, 1)
        composer.addWidget(self.send_button)
        body.addLayout(composer)

        voice_row = QHBoxLayout()
        self.auto_speak = QCheckBox("Speak replies")
        self.auto_speak.setChecked(True)
        self.speak_button = QPushButton("Speak latest")
        self.speak_button.clicked.connect(self.speak_latest)
        self.stop_speech_button = QPushButton("Stop voice")
        self.stop_speech_button.clicked.connect(self.stop_speech)
        voice_row.addWidget(self.auto_speak)
        voice_row.addStretch(1)
        voice_row.addWidget(self.speak_button)
        voice_row.addWidget(self.stop_speech_button)
        body.addLayout(voice_row)

        note = QLabel("Local AI · Offline voice · Google search · Laptop window checks")
        note.setObjectName("Muted")
        body.addWidget(note)

        root.addWidget(sidebar)
        root.addWidget(content, 1)
        self._create_conversation()
        self.refresh_models()

    def _create_conversation(self):
        self.conversation_id = self.database.create_conversation(self.assistant_id)
        self.transcript.clear()
        self._append("ASTRA", "Hey! I'm ready. Send me a message when you're set.")
        self._refresh_history()

    def _append(self, speaker, text):
        safe = (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self.transcript.append(f'<p><b style="color:#7dd3fc">{speaker}</b><br>{safe}</p>')

    def _refresh_history(self):
        self.history.clear()
        for row in self.database.list_conversations(self.assistant_id):
            item = QListWidgetItem(row["title"])
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.history.addItem(item)

    def _assistant_changed(self, index):
        if (self.worker and self.worker.isRunning()) or (self.tool_worker and self.tool_worker.isRunning()):
            return
        assistant = self.assistant_picker.currentData()
        if not assistant:
            return
        self.assistant_id = assistant
        self.heading.setText(self.assistant_picker.currentText())
        self.message_input.setPlaceholderText(f"Message {self.assistant_picker.currentText()}…")
        self._create_conversation()

    def new_chat(self):
        if (self.worker and self.worker.isRunning()) or (self.tool_worker and self.tool_worker.isRunning()):
            return
        self._create_conversation()

    def _load_conversation(self, item):
        if (self.worker and self.worker.isRunning()) or (self.tool_worker and self.tool_worker.isRunning()):
            return
        self.conversation_id = item.data(Qt.ItemDataRole.UserRole)
        self.transcript.clear()
        with self.database.connect() as db:
            rows = db.execute(
                "SELECT role, content FROM chat_messages WHERE conversation_id=? ORDER BY id",
                (self.conversation_id,)
            ).fetchall()
        for row in rows:
            self._append("You" if row["role"] == "user" else self.heading.text(), row["content"])
            if row["role"] == "assistant":
                self.last_assistant_text = row["content"]

    def refresh_models(self):
        try:
            models = self.provider.list_models()
            current = self.model_picker.currentText().strip() or "qwen3.5:2b"
            self.model_picker.clear()
            self.model_picker.addItems(models)
            if current not in models:
                self.model_picker.setEditText(current)
            else:
                self.model_picker.setCurrentText(current)
            self.connection_label.setText(f"● Ollama connected · {len(models)} model(s)")
            self.connection_label.setStyleSheet("color:#75e0b0;")
        except OllamaError as exc:
            self.connection_label.setText("● Ollama offline")
            self.connection_label.setStyleSheet("color:#f0a0a0;")
            self.status.setText("OFFLINE")
            log.warning("Ollama connection failed: %s", exc)

    def send_message(self):
        text = self.message_input.text().strip()
        if not text or (self.worker and self.worker.isRunning()) or (self.tool_worker and self.tool_worker.isRunning()):
            return

        if self.tool_router.is_command(text):
            self.message_input.clear()
            self._append("You", text)
            self.database.add_message(self.conversation_id, "user", text)
            self.send_button.setEnabled(False)
            self.message_input.setEnabled(False)
            self.status.setText("USING TOOLS")
            self.state_changed.emit("thinking")
            self.tool_worker = ToolWorker(self.tool_router, text)
            self.tool_worker.finished_text.connect(self._tool_reply_received)
            self.tool_worker.failed.connect(self._tool_reply_failed)
            self.tool_worker.start()
            return

        model = self.model_picker.currentText().strip()
        if not model:
            QMessageBox.warning(self, "Choose a model", "Enter an installed Ollama model name.")
            return

        self.message_input.clear()
        self._append("You", text)
        self.database.add_message(self.conversation_id, "user", text)
        self.send_button.setEnabled(False)
        self.message_input.setEnabled(False)
        self.status.setText("THINKING")
        self.state_changed.emit("thinking")

        system = ASSISTANT_PROMPTS[self.assistant_id]
        system += (
            f"\n\nCurrent local date and time: {datetime.now().astimezone().isoformat(timespec='minutes')}. "
            "Do not invent current events, tool results, or actions. "
            "For Google, tell the user they can say 'google [query]'. "
            "For web research, they can say 'search [query]'. "
            "For checking visible laptop windows, they can say 'check my laptop'. "
            "For opening apps or URLs, they can say 'open [app or URL]'. "
  "For explicit keyboard input, they can say 'type [text]' or 'press [key]'. "
  "For a screen coordinate, they can say 'click [x], [y]'.\n"
        )
        memories = self.database.list_memories(self.assistant_id)
        if memories:
            system += "\n\nRemember these user-approved notes when relevant:\n" + "\n".join(
                f"- {row['content']}" for row in memories
            )
        messages = [{"role": "system", "content": system}]
        with self.database.connect() as db:
            rows = db.execute(
                "SELECT role, content FROM chat_messages WHERE conversation_id=? ORDER BY id DESC LIMIT 20",
                (self.conversation_id,)
            ).fetchall()
        messages.extend({"role": row["role"], "content": row["content"]} for row in reversed(rows))

        self.worker = ChatWorker(self.provider, messages, model)
        self.worker.finished_text.connect(self._reply_received)
        self.worker.failed.connect(self._reply_failed)
        self.worker.start()

    def _tool_reply_received(self, result):
        self._append(self.heading.text(), result)
        self.database.add_message(self.conversation_id, "assistant", result)
        self.last_assistant_text = result
        self.status.setText("TOOL COMPLETE")
        self.state_changed.emit("idle")
        self._finish_request()
        self._refresh_history()
        if self.auto_speak.isChecked():
            self._speak_text(result)

    def _tool_reply_failed(self, error):
        message = f"Tool failed; I did not verify the request. {error}"
        self._append(self.heading.text(), message)
        self.database.add_message(self.conversation_id, "assistant", message)
        self.last_assistant_text = message
        self.status.setText("TOOL ERROR")
        self.state_changed.emit("error")
        self._finish_request()
        self._refresh_history()
        if self.auto_speak.isChecked():
            self._speak_text(message)

    def _finish_request(self):
        self.send_button.setEnabled(True)
        self.message_input.setEnabled(True)
        self.message_input.setFocus()

    def _reply_received(self, answer):
        answer = answer or "(The model returned an empty response.)"
        self._append(self.heading.text(), answer)
        self.database.add_message(self.conversation_id, "assistant", answer)
        self.last_assistant_text = answer
        self.status.setText("LOCAL AI")
        self.state_changed.emit("idle")
        self._finish_request()
        self._refresh_history()
        if self.auto_speak.isChecked():
            self._speak_text(answer)

    def _reply_failed(self, error):
        message = f"I couldn't reach the local model. {error}"
        self._append("ASTRA", message)
        self.status.setText("ERROR")
        self.state_changed.emit("error")
        self._finish_request()
        self.refresh_models()

    def speak_latest(self):
        if self.last_assistant_text:
            self._speak_text(self.last_assistant_text)
        else:
            self.status.setText("NOTHING TO SPEAK")

    def _speak_text(self, text):
        if self.speech_worker and self.speech_worker.isRunning():
            self.stop_speech()
            self.speech_worker.wait(500)
        self.speech_worker = SpeechWorker(text)
        self.speech_worker.started.connect(lambda: self.status.setText("SPEAKING"))
        self.speech_worker.completed.connect(self._speech_completed)
        self.speech_worker.failed.connect(self._speech_failed)
        self.speech_worker.start()

    def stop_speech(self):
        if self.speech_worker and self.speech_worker.isRunning():
            self.speech_worker.stop()
            self.status.setText("VOICE STOPPING")

    def _speech_completed(self):
        if not (self.speech_worker and self.speech_worker.isRunning()):
            self.status.setText("READY")

    def _speech_failed(self, error):
        self.status.setText("VOICE ERROR")
        self._append("ASTRA", error)
        log.warning("Speech output failed: %s", error)

    def closeEvent(self, event):
        self.stop_speech()
        if self.speech_worker and self.speech_worker.isRunning():
            self.speech_worker.wait(1500)
        event.accept()
