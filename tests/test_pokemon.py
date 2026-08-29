"""Parseo de packs (pokemon.py). Usa packs reales del repo como datos de referencia.

No carga los 493 — eso es trabajo de check_packs.py / selfcheck.py. Aquí solo se cubre
el contrato de parseo con unos pocos packs representativos y los caminos de error.
"""
from __future__ import annotations

import json

import pytest

from pokemon import PackLoadError, StateDef, _parse_state, load_index, load_pack

BLASTOISE = "retro/gen-1/009-blastoise"
DRAGONAIR = "retro/gen-1/148-dragonair"


def test_load_index_has_the_full_catalog():
    entries = load_index()
    assert len(entries) == 493
    ids = {e.id for e in entries}
    assert BLASTOISE in ids and DRAGONAIR in ids


def test_load_pack_blastoise_states(qapp):
    pack = load_pack(BLASTOISE)
    assert set(pack.states) == {"idle", "walk", "sleep"}
    assert pack.has_state("sleep")
    assert not pack.has_state("attack")
    idle = pack.states["idle"]
    assert idle.frames == 8 and idle.fps == 8
    assert idle.rows["front"] == 0 and idle.rows["frontLeft"] == 7


def test_dragonair_idle_sheet_is_read_from_json_not_derived(qapp):
    # 148-dragonair no tiene Idle-Anim.webp: su estado idle declara "sheet": "Walk-Anim.webp".
    # pokemon.py nunca debe derivar el sheet del nombre del estado (gotcha de CLAUDE.md).
    pack = load_pack(DRAGONAIR)
    assert pack.states["idle"].sheet == "Walk-Anim.webp"
    assert pack.states["walk"].sheet == "Walk-Anim.webp"


def test_frame_pixmap_decodes_a_real_sprite(qapp):
    pack = load_pack(BLASTOISE)
    pm = pack.frame_pixmap("idle", 0, 0)
    assert not pm.isNull()
    assert pm.width() == pack.states["idle"].frame_w


def test_load_pack_unknown_id_raises():
    with pytest.raises(PackLoadError):
        load_pack("retro/gen-1/999-missingno")


# --- _parse_state (sin Qt) --------------------------------------------------

def _raw_state(**over):
    base = {
        "sheet": "Idle-Anim.webp",
        "frame": {"w": 32, "h": 32},
        "fps": 8,
        "frames": 8,
        "rows": {"front": 0, "back": 4},
    }
    base.update(over)
    return base


def test_parse_state_ok():
    st = _parse_state("p", "idle", _raw_state())
    assert isinstance(st, StateDef)
    assert st.frame_w == 32 and st.frames == 8


@pytest.mark.parametrize("bad", [{"fps": 0}, {"frames": 0}, {"frame": {"w": 0, "h": 32}}])
def test_parse_state_rejects_non_positive_dimensions(bad):
    with pytest.raises(PackLoadError):
        _parse_state("p", "idle", _raw_state(**bad))


def test_parse_state_requires_front_fallback_when_diagonals_missing():
    with pytest.raises(PackLoadError):
        _parse_state("p", "idle", _raw_state(rows={"right": 2, "left": 6}))


def test_parse_state_missing_key_raises():
    raw = _raw_state()
    del raw["rows"]
    with pytest.raises(PackLoadError):
        _parse_state("p", "idle", raw)


def test_sleep_state_with_all_rows_zero_is_valid():
    # Habitual (Blastoise): sleep mapea las 8 direcciones a la fila 0. No es un bug.
    st = _parse_state("p", "sleep", _raw_state(frames=2, fps=1, rows={k: 0 for k in (
        "front", "frontRight", "right", "backRight", "back", "backLeft", "left", "frontLeft"
    )}))
    assert set(st.rows.values()) == {0}
