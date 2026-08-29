"""Fuente única de la versión. La consumen: PokeFollower.spec (metadatos del .exe),
installer/PokeFollower.iss (vía tools/build.ps1), tray.py (tooltip) y selfcheck.py.
No debería haber otro string de versión mantenido a mano en ningún otro sitio.
"""
from __future__ import annotations

# Versión semántica / de producto / de tag (el tag git es "v" + esto).
__version__ = "0.1.0-beta.1"

# Equivalente numérico para los recursos PE de Windows (FILEVERSION / PRODUCTVERSION),
# que deben ser cuatro enteros de 16 bits. "beta.1" -> ".1" en el cuarto campo:
#   0.1.0-beta.1  ->  0.1.0.1
#   0.1.0-beta.2  ->  0.1.0.2
#   0.1.0 (final) ->  0.1.0.0
# El string visible en la app y el instalador sigue siendo __version__.
__version_tuple__ = (0, 1, 0, 1)
