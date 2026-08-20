"""Ventana transparente, click-through, always-on-top que dibuja el sprite."""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

from pokemon import Pack

WINDOW_FLAGS = (
    Qt.FramelessWindowHint
    | Qt.WindowStaysOnTopHint
    | Qt.Tool
    | Qt.WindowTransparentForInput
    | Qt.WindowDoesNotAcceptFocus
    | Qt.NoDropShadowWindowHint
)


class FollowerWindow(QWidget):
    def __init__(self, pack: Pack, scale: float):
        super().__init__()
        self._pack = pack
        self._scale = scale
        self._state_name = "idle"
        self._row = 0
        self._frame = 0
        self._pixmap = QPixmap()

        self.setWindowFlags(WINDOW_FLAGS)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self.set_frame(self._state_name, self._row, self._frame)

    def set_frame(self, state_name: str, row: int, frame: int) -> None:
        """Actualiza el frame mostrado, redimensiona la ventana y repinta."""
        state = self._pack.states[state_name]
        raw_pixmap = self._pack.frame_pixmap(state_name, row, frame)

        dpr = self.devicePixelRatioF() if self.windowHandle() else 1.0
        physical_w = max(1, round(state.frame_w * self._scale * dpr))
        physical_h = max(1, round(state.frame_h * self._scale * dpr))
        scaled = raw_pixmap.scaled(
            physical_w, physical_h, Qt.IgnoreAspectRatio, Qt.FastTransformation
        )
        scaled.setDevicePixelRatio(dpr)

        self._pixmap = scaled
        self._state_name = state_name
        self._row = row
        self._frame = frame

        logical_w = math.ceil(state.frame_w * self._scale)
        logical_h = math.ceil(state.frame_h * self._scale)
        if self.width() != logical_w or self.height() != logical_h:
            self.resize(logical_w, logical_h)
        self.update()

    def move_center_to(self, center: QPoint) -> None:
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)

    def paintEvent(self, event) -> None:  # noqa: N802 (nombre impuesto por Qt)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        painter.drawPixmap(0, 0, self._pixmap)
        painter.end()

    def place_at_startup_position(self) -> None:
        cursor_pos = QCursor.pos()
        self.move_center_to(QPoint(cursor_pos.x(), cursor_pos.y() - 30))
