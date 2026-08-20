"""Fase 3: catálogo completo, selector de Pokémon, persistencia."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QDialog

import config
from follower import FollowerWindow
from pokemon import PackLoadError, load_pack
from selector import PokemonSelectorDialog
from tray import Tray


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    cfg = config.load()

    try:
        pack = load_pack(cfg.pokemon)
    except PackLoadError as exc:
        print(f"Error cargando pack '{cfg.pokemon}': {exc}", file=sys.stderr)
        return 1

    window = FollowerWindow(pack, scale=cfg.scale, offset=cfg.offset, lerp=cfg.lerp)
    window.show()
    window.set_frame("idle", 0, 0)
    window.place_at_startup_position()

    tray = Tray(enabled=cfg.enabled)

    def on_enabled_toggled(enabled: bool) -> None:
        cfg.enabled = enabled
        config.save(cfg)
        if enabled:
            window.show()
            window.start()
        else:
            window.stop()
            window.hide()

    def on_choose_pokemon() -> None:
        dialog = PokemonSelectorDialog(cfg.pokemon)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        new_id = dialog.selected_pack_id()
        if not new_id or new_id == cfg.pokemon:
            return
        try:
            new_pack = load_pack(new_id)
        except PackLoadError as exc:
            print(f"Error cargando pack '{new_id}': {exc}", file=sys.stderr)
            return
        cfg.pokemon = new_id
        config.save(cfg)
        window.set_pack(new_pack)

    def on_exit_requested() -> None:
        window.stop()
        app.quit()

    tray.enabled_toggled.connect(on_enabled_toggled)
    tray.choose_pokemon_requested.connect(on_choose_pokemon)
    tray.exit_requested.connect(on_exit_requested)

    if cfg.enabled:
        window.start()
    else:
        window.hide()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
