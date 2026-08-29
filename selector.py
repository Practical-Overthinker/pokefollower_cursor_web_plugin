"""Diálogo de selección de Pokémon: rejilla de miniaturas + búsqueda por nombre."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from pokemon import load_index

THUMBNAIL_SIZE = QSize(48, 48)


class PokemonSelectorDialog(QDialog):
    def __init__(self, current_pack_id: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Pokémon")
        self.resize(420, 520)

        self._entries = load_index()
        self._selected_id: Optional[str] = None

        layout = QVBoxLayout(self)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search by name…")
        self._search.textChanged.connect(self._apply_filter)
        layout.addWidget(self._search)

        self._list = QListWidget()
        self._list.setViewMode(QListWidget.ViewMode.IconMode)
        self._list.setIconSize(THUMBNAIL_SIZE)
        self._list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self._list.setSpacing(6)
        self._list.itemDoubleClicked.connect(self._accept_item)
        layout.addWidget(self._list)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate(current_pack_id)
        self._search.setFocus()

    def _populate(self, current_pack_id: str) -> None:
        self._list.clear()
        for entry in self._entries:
            item = QListWidgetItem(entry.name)
            item.setData(Qt.ItemDataRole.UserRole, entry.id)
            if entry.thumbnail.exists():
                item.setIcon(QIcon(str(entry.thumbnail)))
            self._list.addItem(item)
            if entry.id == current_pack_id:
                self._list.setCurrentItem(item)

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(bool(needle) and needle not in item.text().lower())

    def _accept_item(self, item: QListWidgetItem) -> None:
        self._selected_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def _on_accept(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self._selected_id = item.data(Qt.ItemDataRole.UserRole)
        self.accept()

    def selected_pack_id(self) -> Optional[str]:
        return self._selected_id
