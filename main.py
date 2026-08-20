"""Fase 1: ventana transparente click-through con un sprite estático.

Sin tray, sin movimiento. Cerrar con Ctrl+C en la consola.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication

import config
from follower import FollowerWindow
from pokemon import PackLoadError, load_pack


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    cfg = config.load()

    try:
        pack = load_pack(cfg.pokemon)
    except PackLoadError as exc:
        print(f"Error cargando pack '{cfg.pokemon}': {exc}", file=sys.stderr)
        return 1

    window = FollowerWindow(pack, scale=cfg.scale)
    window.show()
    # Tras show(), la ventana ya tiene un windowHandle real y devicePixelRatioF()
    # refleja el monitor correcto; se recalcula el frame para nitidez en DPI fraccional.
    window.set_frame("idle", 0, 0)
    window.place_at_startup_position()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
