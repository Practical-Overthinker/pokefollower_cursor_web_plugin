"""Resolución de rutas: dónde están las cosas, tanto corriendo desde fuente como congelado
(PyInstaller). Único módulo del repo que conoce sys.frozen/sys._MEIPASS. Sin Qt.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "PokeFollower"


def app_dir() -> Path:
    """Directorio base de la app: carpeta del bundle si está congelada, carpeta del
    código fuente si no. sys._MEIPASS (no sys.executable) porque apunta a donde
    PyInstaller deposita los `datas` tanto en modo onedir como onefile.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent


def assets_dir() -> Path:
    return app_dir() / "assets"


def config_dir() -> Path:
    """Directorio de persistencia del usuario. Congelada: %APPDATA%\\PokeFollower
    (se crea si no existe). Desde fuente: la raíz del repo, igual que siempre —
    no se migra el config.json de desarrollo, ver decision.log.
    """
    if not getattr(sys, "frozen", False):
        return Path(__file__).parent

    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    target = base / APP_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target
