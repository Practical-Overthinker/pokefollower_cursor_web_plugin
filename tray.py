"""System tray: icono, menú, acciones. No toca posición ni frames, solo emite señales."""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

import paths

ICON_PATH = paths.assets_dir() / "icons" / "pokeball-32.png"


class Tray(QObject):
    enabled_toggled = Signal(bool)
    choose_pokemon_requested = Signal()
    settings_requested = Signal()
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

        choose_action = QAction("Choose Pokémon...", menu)
        choose_action.triggered.connect(self.choose_pokemon_requested)
        menu.addAction(choose_action)

        settings_action = QAction("Settings...", menu)
        settings_action.triggered.connect(self.settings_requested)
        menu.addAction(settings_action)

        menu.addSeparator()

        exit_action = QAction("Exit", menu)
        exit_action.triggered.connect(self.exit_requested)
        menu.addAction(exit_action)

        self._icon.setContextMenu(menu)
        self._icon.show()

    def hide(self) -> None:
        self._icon.hide()
