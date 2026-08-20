"""Diagnóstico: carga todos los packs del índice y reporta fallos.

Uso: python check_packs.py
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication  # QPixmap requiere una QGuiApplication activa

from pokemon import PackLoadError, load_index, load_pack


def main() -> int:
    app = QApplication(sys.argv)  # noqa: F841 (necesaria para que QPixmap funcione)

    entries = load_index()
    failures: list[tuple[str, str]] = []
    for entry in entries:
        try:
            load_pack(entry.id)
        except PackLoadError as exc:
            failures.append((entry.id, str(exc)))

    print(f"{len(entries)} packs en el índice, {len(failures)} fallos")
    for pack_id, msg in failures:
        print(f"  FAIL {pack_id}: {msg}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
