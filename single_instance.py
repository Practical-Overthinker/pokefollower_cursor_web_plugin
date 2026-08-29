"""Protección de instancia única en Windows mediante un mutex con nombre.

Motivo: la app puede lanzarse desde el acceso directo del menú Inicio, del escritorio,
de la carpeta Startup o ejecutando el .exe a mano. Dos procesos a la vez producen dos
iconos en la bandeja, dos ventanas follower, timers duplicados y escrituras concurrentes
sobre el mismo config.json.

El nombre del mutex NO depende de la versión: debe ser idéntico entre versiones para que
el instalador (Inno Setup, `AppMutex` en PokeFollower.iss) reconozca una app en marcha
durante install/update/uninstall. Es exactamente el mismo string en ambos lados.

Módulo aislado y específico de Windows: el resto del runtime no importa ctypes.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

# Debe coincidir carácter por carácter con `AppMutex` en installer/PokeFollower.iss.
# Sin prefijo `Global\\`: el mutex vive en el espacio de nombres de la sesión, que es el
# alcance correcto para una app de bandeja por-usuario (y el que usa Inno Setup por
# defecto para su chequeo de AppMutex).
MUTEX_NAME = "PokeFollowerDesktop"

_ERROR_ALREADY_EXISTS = 183

# El handle se guarda a nivel de módulo para que viva tanto como el proceso: si el objeto
# se recolectara, el SO liberaría el mutex y una segunda instancia dejaría de detectarse.
_mutex_handle: int | None = None


def already_running() -> bool:
    """Crea (o abre) el mutex de la app. Devuelve True si ya existía otra instancia.

    Llamar una sola vez, al arrancar, antes de crear ninguna ventana o icono de bandeja.
    """
    global _mutex_handle

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (wintypes.LPCVOID, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE

    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    last_error = ctypes.get_last_error()

    if not handle:
        # No se pudo crear el mutex: no bloqueamos el arranque por esto, mejor permitir
        # que la app corra que impedirla por un fallo del propio guard.
        return False

    _mutex_handle = handle
    return last_error == _ERROR_ALREADY_EXISTS
