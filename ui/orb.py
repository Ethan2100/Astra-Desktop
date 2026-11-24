import math
from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtGui import QColor, QPainter, QRadialGradient, QPen, QAction
from PySide6.QtWidgets import QWidget, QApplication, QMenu

class AstraOrb(QWidget):
    """Lightweight floating orb. It drifts along screen edges and remains draggable."""
    open_chat_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(92, 92)
        self.setToolTip("ASTRA — double-click to open")
        self._phase = 0.0
        self._drag_offset = None
        self._manual_pause = 0
        self._movement_enabled = True
        self._route_position = 0.0
        self._moving = False
        self._wait_ticks = 0
        self._tick_count = 0
        self._state = "idle"

        screen = QApplication.primaryScreen()
        area = screen.availableGeometry() if screen else None
        if area:
            self.move(area.right() - self.width() - 28, area.bottom() - self.height() - 35)
        else:
            self.move(900, 600)

        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate)
        self.animation_timer.start(40)

        self.motion_timer = QTimer(self)
        self.motion_timer.timeout.connect(self._autonomous_motion)
        self.motion_timer.start(100)

    def stop(self):
        self.animation_timer.stop()
        self.motion_timer.stop()

    def _animate(self):
        self._phase += 0.045
        if self._phase > math.tau:
            self._phase = 0.0
        self.update()

    def set_state(self, state):
        if state in {"idle", "listening", "thinking", "speaking", "offline", "error"}:
            self._state = state
            self.update()

    def _autonomous_motion(self):
        if not self._movement_enabled or self._drag_offset is not None:
            return
        if self._manual_pause > 0:
            self._manual_pause -= 1
            return

        self._tick_count += 1
        # Rest between short, slow journeys so the orb is not distracting.
        if not self._moving:
            self._wait_ticks += 1
            if self._wait_ticks >= 220:  # about 22 seconds
                self._moving = True
                self._wait_ticks = 0
                self._route_position = 0.0
            return

        screen = QApplication.screenAt(self.frameGeometry().center()) or QApplication.primaryScreen()
        if not screen:
            self._moving = False
            return
        area = screen.availableGeometry().adjusted(12, 12, -12, -12)
        w, h = self.width(), self.height()
        left, top = area.left(), area.top()
        right, bottom = area.right() - w, area.bottom() - h
        # A rectangular perimeter route keeps the orb near screen edges,
        # away from the center of the user's working area.
        lengths = [max(1, right-left), max(1, bottom-top),
                   max(1, right-left), max(1, bottom-top)]
        perimeter = sum(lengths)
        self._route_position += 0.0018  # slow, calm drift
        if self._route_position >= 1.0:
            self._route_position = 0.0
            self._moving = False
            return
        distance = self._route_position * perimeter
        if distance < lengths[0]:
            x, y = left + distance, top
        elif distance < lengths[0] + lengths[1]:
            x, y = right, top + distance - lengths[0]
        elif distance < lengths[0] + lengths[1] + lengths[2]:
            x, y = right - (distance - lengths[0] - lengths[1]), bottom
        else:
            x, y = left, bottom - (distance - lengths[0] - lengths[1] - lengths[2])
        self.move(round(x), round(y))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pulse = (math.sin(self._phase) + 1.0) / 2.0
        colors = {
            "idle": QColor(70, 190, 255),
            "listening": QColor(80, 255, 210),
            "thinking": QColor(150, 125, 255),
            "speaking": QColor(70, 220, 255),
            "offline": QColor(120, 140, 160),
            "error": QColor(255, 105, 105),
        }
        color = colors[self._state]
        center = self.rect().center()
        radius = 27 + pulse * 3
        glow = QRadialGradient(center, 44 + pulse * 5)
        glow.setColorAt(0.0, QColor(color.red(), color.green(), color.blue(), 145))
        glow.setColorAt(0.55, QColor(color.red(), color.green(), color.blue(), 55))
        glow.setColorAt(1.0, QColor(color.red(), color.green(), color.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(center, 44 + pulse * 5, 44 + pulse * 5)

        core = QRadialGradient(center.x()-9, center.y()-11, radius*1.5)
        core.setColorAt(0.0, QColor(235, 252, 255, 255))
        core.setColorAt(0.28, color.lighter(155))
        core.setColorAt(1.0, color.darker(170))
        painter.setBrush(core)
        painter.drawEllipse(center, radius, radius)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(210, 245, 255, 170), 1.2))
        painter.drawEllipse(center, radius, radius)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._moving = False
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_menu(event.globalPosition().toPoint())
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_offset is not None:
            self._drag_offset = None
            self._manual_pause = 600  # give the user a minute before drifting again
            event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_chat_requested.emit()

    def _show_menu(self, position):
        menu = QMenu()
        open_action = QAction("Open ASTRA", self)
        open_action.triggered.connect(self.open_chat_requested.emit)
        menu.addAction(open_action)

        movement_action = QAction("Pause autonomous movement" if self._movement_enabled else "Enable autonomous movement", self)
        movement_action.triggered.connect(self._toggle_movement)
        menu.addAction(movement_action)

        menu.addSeparator()
        exit_action = QAction("Exit ASTRA", self)
        exit_action.triggered.connect(QApplication.quit)
        menu.addAction(exit_action)
        menu.exec(position)

    def _toggle_movement(self):
        self._movement_enabled = not self._movement_enabled
        self._moving = False
        self._wait_ticks = 0
