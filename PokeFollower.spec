# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec para PokéFollower Desktop.

Build: pyinstaller PokeFollower.spec
Resultado: dist/PokeFollower/PokeFollower.exe (onedir — ver decision.log del ciclo de
empaquetado: onefile descomprimiría ~2967 archivos en %TEMP% en cada arranque).
"""
from pathlib import Path

REPO_ROOT = Path(SPECPATH)  # noqa: F821 (SPECPATH lo inyecta PyInstaller al ejecutar el .spec)

# Recolectar todo assets/ EXCEPTO los .xml de authoring (AnimData, solo los lee
# add_pokemon.py; nunca el runtime — ver decision.log D-006). No se lista a mano: el
# catálogo crece con add_pokemon.py.
ASSETS_SRC = REPO_ROOT / "assets"
datas = []
for f in ASSETS_SRC.rglob("*"):
    if f.is_file() and f.suffix.lower() != ".xml":
        rel_dir = f.relative_to(REPO_ROOT).parent
        datas.append((str(f), str(rel_dir)))

# Superficie real de PySide6 usada por la app: solo QtCore, QtGui, QtWidgets (ver
# exploración del ciclo de empaquetado). Se excluyen los módulos Qt no utilizados para
# reducir tamaño. NO se toca imageformats/plugins de imagen bajo ninguna circunstancia:
# los sprites son .webp y excluir qwebp rompería el render por completo sin error visible.
EXCLUDED_QT_MODULES = [
    "PySide6.QtNetwork",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtSql",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtDesigner",
    "PySide6.QtTest",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtBluetooth",
    "PySide6.QtPositioning",
    "PySide6.QtSerialPort",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
]

a = Analysis(
    ["main.py"],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDED_QT_MODULES,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PokeFollower",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(REPO_ROOT / "assets" / "icons" / "pokeball.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PokeFollower",
)
