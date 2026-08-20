"""System tray: icono, menú, acciones. No toca posición ni frames, solo emite señales."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

ICON_PATH = Path(__file__).parent / "assets" / "icons" / "pokeball-32.png"


class Tray(QObject):
    enabled_toggled = Signal(bool)
    exit_requested = Signal()

    def __init__(self, enabled: bool = True):
        super().__init__()
        self._icon = QSystemTrayIcon(QIcon(str(ICON_PATH)))
        self._icon.setToolTip("PokéFollower")

        menu = QMenu()

        self._enabled_action = QAction("Enabled", menu)
        self._enabled_action.setCheckable(True)
        self._enabled_action.setChecked(enabled)
        self._enabled_action.toggled.connect(self.enabled_toggled)
        menu.addAction(self._enabled_action)

        menu.addSeparator()

        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_requested)
        menu.addAction(exit_action)

        self._icon.setContextMenu(menu)
        self._icon.show()

    def hide(self) -> None:
        self._icon.hide()
