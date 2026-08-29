"""Fixtures compartidas.

Dos cosas importan aquí:

1. Qt necesita un `QGuiApplication` vivo para construir `QPixmap` (lo usan
   `pokemon.load_pack` y `Pack.frame_pixmap`). Se crea una sola vez por sesión, en
   modo `offscreen` para no abrir ninguna ventana ni depender de un display real.

2. `config.CONFIG_PATH` se resuelve al importar `config` y, corriendo desde fuente,
   apunta a la raíz del repo (`paths.config_dir()`). Sin aislarlo, cualquier test de
   `config.save()` machacaría el `config.json` real del desarrollador. La fixture
   `isolated_config` lo redirige a un archivo temporal.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# En algunas máquinas el raíz temporal por defecto (`%TEMP%\pytest-of-<user>`) queda con
# permisos que impiden a pytest escanearlo. Si no es accesible, se cae a un directorio
# local del repo (`.pytmp/`, en .gitignore). No afecta a CI, donde el runner está limpio.
def _pick_temproot() -> None:
    if "PYTEST_DEBUG_TEMPROOT" in os.environ:
        return
    default_root = Path(tempfile.gettempdir())
    try:
        list(default_root.iterdir())
        probe = default_root / f"pytest-of-{os.environ.get('USERNAME', 'user')}"
        if probe.exists():
            list(probe.iterdir())
    except OSError:
        fallback = Path(__file__).resolve().parent.parent / ".pytmp"
        fallback.mkdir(exist_ok=True)
        os.environ["PYTEST_DEBUG_TEMPROOT"] = str(fallback)


_pick_temproot()

import pytest


@pytest.fixture(scope="session")
def qapp():
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication([])
    yield app


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    """Redirige config.CONFIG_PATH a un archivo temporal. Devuelve esa ruta."""
    import config

    target = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", target)
    return target
