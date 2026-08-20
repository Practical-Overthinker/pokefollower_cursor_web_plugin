"""Carga de packs de Pokémon: JSON + spritesheets. No sabe de cursor, estados ni tiempo."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QRect
from PySide6.QtGui import QPixmap

import paths

ASSETS_DIR = paths.assets_dir()
PACKS_DIR = ASSETS_DIR / "packs"
RAW_DIR = ASSETS_DIR / "raw"
UI_DIR = ASSETS_DIR / "ui"
INDEX_PATH = PACKS_DIR / "index.json"
NAME_OVERRIDES_PATH = PACKS_DIR / "name-overrides.json"

DIRECTIONS = (
    "front", "frontRight", "right", "backRight",
    "back", "backLeft", "left", "frontLeft",
)


class PackLoadError(RuntimeError):
    pass


@dataclass
class PackEntry:
    """Una entrada del catálogo (para el selector), sin cargar sprites."""
    id: str
    name: str
    generation: str
    thumbnail: Path


def load_index() -> list[PackEntry]:
    """Lee assets/packs/index.json + name-overrides.json -> catálogo completo.

    Nota: el 'id' de cada entrada (p.ej. 'retro/gen-1/009-blastoise') lleva el
    prefijo de familia ('retro/'), a diferencia de 'rawPath' dentro de cada JSON
    de pack, que no lo lleva.
    """
    if not INDEX_PATH.exists():
        raise PackLoadError(f"índice no encontrado: {INDEX_PATH}")
    try:
        raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackLoadError(f"índice inválido: {exc}") from exc

    overrides: dict[str, str] = {}
    if NAME_OVERRIDES_PATH.exists():
        try:
            overrides = json.loads(NAME_OVERRIDES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            overrides = {}

    entries: list[PackEntry] = []
    for family, items in raw.items():
        for item in items:
            pack_id = item["id"]
            name = overrides.get(pack_id, item.get("name", pack_id))
            parts = pack_id.split("/")
            generation = parts[1] if len(parts) > 1 else ""
            slug = parts[-1]
            thumbnail = UI_DIR / generation / f"{slug}.png"
            entries.append(PackEntry(id=pack_id, name=name, generation=generation, thumbnail=thumbnail))
    return entries


@dataclass
class StateDef:
    sheet: str
    frame_w: int
    frame_h: int
    fps: int
    frames: int
    rows: dict[str, int]


class Pack:
    def __init__(self, pack_id: str, name: str, raw_path: str, states: dict[str, StateDef]):
        self.pack_id = pack_id
        self.name = name
        self.raw_path = raw_path
        self.states = states
        self._sheets: dict[str, QPixmap] = {}
        self._frame_cache: dict[tuple[str, int, int], QPixmap] = {}

    def has_state(self, state_name: str) -> bool:
        return state_name in self.states

    def _sheet_pixmap(self, state: StateDef) -> QPixmap:
        pixmap = self._sheets.get(state.sheet)
        if pixmap is None:
            sheet_path = RAW_DIR / self.raw_path / state.sheet
            if not sheet_path.exists():
                raise PackLoadError(
                    f"pack {self.pack_id}: spritesheet no encontrado: {sheet_path}"
                )
            pixmap = QPixmap(str(sheet_path))
            if pixmap.isNull():
                raise PackLoadError(
                    f"pack {self.pack_id}: no se pudo decodificar {sheet_path}"
                )
            self._sheets[state.sheet] = pixmap
        return pixmap

    def frame_pixmap(self, state_name: str, row: int, frame: int) -> QPixmap:
        state = self.states[state_name]
        cache_key = (state_name, row, frame)
        cached = self._frame_cache.get(cache_key)
        if cached is not None:
            return cached

        sheet = self._sheet_pixmap(state)
        rect = QRect(
            frame * state.frame_w,
            row * state.frame_h,
            state.frame_w,
            state.frame_h,
        )
        cropped = sheet.copy(rect)
        self._frame_cache[cache_key] = cropped
        return cropped


def _parse_state(pack_id: str, state_name: str, raw: dict) -> StateDef:
    try:
        sheet = raw["sheet"]
        frame_w = int(raw["frame"]["w"])
        frame_h = int(raw["frame"]["h"])
        fps = int(raw["fps"])
        frames = int(raw["frames"])
        rows = {k: int(v) for k, v in raw["rows"].items()}
    except (KeyError, TypeError, ValueError) as exc:
        raise PackLoadError(f"pack {pack_id}: estado '{state_name}' mal formado: {exc}") from exc

    if fps <= 0 or frames <= 0 or frame_w <= 0 or frame_h <= 0:
        raise PackLoadError(
            f"pack {pack_id}: estado '{state_name}' tiene fps/frames/frame inválidos"
        )
    missing_dirs = [d for d in DIRECTIONS if d not in rows]
    if missing_dirs and "front" not in rows:
        raise PackLoadError(
            f"pack {pack_id}: estado '{state_name}' no tiene fila 'front' de fallback"
        )

    return StateDef(sheet=sheet, frame_w=frame_w, frame_h=frame_h, fps=fps, frames=frames, rows=rows)


def load_pack(pack_id: str) -> Pack:
    """pack_id, p.ej. 'retro/gen-1/009-blastoise' -> Pack validado.

    Nota: raw_path (campo del JSON) NO lleva el prefijo 'retro/' que sí lleva pack_id.
    """
    json_path = PACKS_DIR / f"{pack_id}.json"
    if not json_path.exists():
        raise PackLoadError(f"pack no encontrado: {json_path}")

    try:
        raw = json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PackLoadError(f"pack {pack_id}: JSON inválido: {exc}") from exc

    name = raw.get("name", pack_id)
    raw_path = raw.get("rawPath")
    if not raw_path:
        raise PackLoadError(f"pack {pack_id}: falta 'rawPath'")

    states_raw = raw.get("states", {})
    if not states_raw:
        raise PackLoadError(f"pack {pack_id}: no declara 'states'")

    states: dict[str, StateDef] = {}
    for state_name, state_raw in states_raw.items():
        states[state_name] = _parse_state(pack_id, state_name, state_raw)

    pack = Pack(pack_id=pack_id, name=name, raw_path=raw_path, states=states)

    # Validar que cada sheet exista y que ninguna fila desborde su altura.
    for state_name, state in states.items():
        sheet_pixmap = pack._sheet_pixmap(state)
        max_row = max(state.rows.values())
        needed_h = (max_row + 1) * state.frame_h
        if needed_h > sheet_pixmap.height():
            raise PackLoadError(
                f"pack {pack_id}: estado '{state_name}' fila {max_row} desborda el sheet "
                f"({needed_h}px necesarios, {sheet_pixmap.height()}px disponibles)"
            )
        needed_w = state.frames * state.frame_w
        if needed_w > sheet_pixmap.width():
            raise PackLoadError(
                f"pack {pack_id}: estado '{state_name}' tiene {state.frames} frames que "
                f"desbordan el sheet ({needed_w}px necesarios, {sheet_pixmap.width()}px disponibles)"
            )

    return pack
