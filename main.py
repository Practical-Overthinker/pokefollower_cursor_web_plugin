"""Fase 4: Settings (escala, velocidad, distancia, sleep) con efecto en vivo."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

import config
import single_instance
from follower import FollowerWindow
from pokemon import PackLoadError, load_pack
from selector import PokemonSelectorDialog
from settings import SettingsDialog
from tray import Tray


def main() -> int:
    # Instancia única: un segundo lanzamiento (Startup + menú Inicio + doble clic al .exe)
    # sale en silencio con éxito, sin abrir otra ventana ni otro icono de bandeja.
    if single_instance.already_running():
        return 0

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    cfg = config.load()

    try:
        pack = load_pack(cfg.pokemon)
    except PackLoadError as exc:
        QMessageBox.critical(
            None,
            "PokéFollower",
            f"Could not load the Pokémon '{cfg.pokemon}':\n{exc}",
        )
        return 1

    window = FollowerWindow(
        pack,
        scale=cfg.scale,
        offset=cfg.offset,
        lerp=cfg.lerp,
        sleep_enabled=cfg.sleep,
        sleep_after=cfg.sleep_after,
    )
    window.show()
    window.set_frame("idle", 0, 0)
    window.place_at_startup_position()

    tray = Tray(enabled=cfg.enabled)
    tray.show_startup_message()

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
            QMessageBox.warning(
                None,
                "PokéFollower",
                f"Could not load the Pokémon '{new_id}':\n{exc}\n\nKeeping the previous one.",
            )
            return
        cfg.pokemon = new_id
        config.save(cfg)
        window.set_pack(new_pack)

    def on_settings_requested() -> None:
        dialog = SettingsDialog(cfg)

        def _on_scale(v: float) -> None:
            cfg.scale = v
            window.set_scale(v)
            config.save(cfg)

        def _on_speed(v: float) -> None:
            cfg.lerp = v
            window.set_speed_config(v)
            config.save(cfg)

        def _on_offset(v: float) -> None:
            cfg.offset = v
            window.set_offset(v)
            config.save(cfg)

        def _on_sleep_config(enabled: bool, sleep_after: int) -> None:
            cfg.sleep = enabled
            cfg.sleep_after = sleep_after
            window.set_sleep_config(enabled, sleep_after)
            config.save(cfg)

        dialog.scale_changed.connect(_on_scale)
        dialog.speed_changed.connect(_on_speed)
        dialog.offset_changed.connect(_on_offset)
        dialog.sleep_config_changed.connect(_on_sleep_config)
        dialog.exec()

    def on_exit_requested() -> None:
        window.stop()
        app.quit()

    tray.enabled_toggled.connect(on_enabled_toggled)
    tray.choose_pokemon_requested.connect(on_choose_pokemon)
    tray.settings_requested.connect(on_settings_requested)
    tray.exit_requested.connect(on_exit_requested)

    if cfg.enabled:
        window.start()
    else:
        window.hide()

    return app.exec()


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        import selfcheck

        sys.exit(selfcheck.main())
    sys.exit(main())
