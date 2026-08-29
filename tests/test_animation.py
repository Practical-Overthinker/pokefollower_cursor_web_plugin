"""Lógica pura de animación (animation.py). Sin Qt.

Los vectores de `pick_dir8_from_vector` están cruzados contra
`reference/content.js::pickDir8FromVector` (mismo algoritmo, coords de pantalla: +y abajo).
"""
from __future__ import annotations

import pytest

from animation import (
    AnimationState,
    pick_dir8_from_vector,
    pick_row_for_state,
    pick_state_by_speed,
)
from pokemon import StateDef


# --- pick_dir8_from_vector -------------------------------------------------------

@pytest.mark.parametrize(
    "vx, vy, expected",
    [
        (1.0, 0.0, "right"),
        (0.0, 1.0, "front"),        # +y abajo => "front"
        (-1.0, 0.0, "left"),
        (0.0, -1.0, "back"),
        (1.0, 1.0, "frontRight"),
        (-1.0, 1.0, "frontLeft"),
        (1.0, -1.0, "backRight"),
        (-1.0, -1.0, "backLeft"),
    ],
)
def test_dir8_cardinals_and_diagonals(vx, vy, expected):
    assert pick_dir8_from_vector(vx, vy) == expected


@pytest.mark.parametrize("vx, vy", [(0.0, 0.0), (0.3, -0.3), (-0.29, 0.1), (0.2, 0.2)])
def test_dir8_dead_zone_returns_front(vx, vy):
    assert pick_dir8_from_vector(vx, vy) == "front"


def test_dir8_just_outside_dead_zone_is_not_forced_front():
    # |vy| > 0.3 rompe la zona muerta; el vector apunta claramente "front" igualmente,
    # pero por el ángulo, no por el atajo de la zona muerta.
    assert pick_dir8_from_vector(0.0, 0.4) == "front"
    assert pick_dir8_from_vector(0.0, -0.4) == "back"


def test_dir8_magnitude_does_not_matter_only_angle():
    assert pick_dir8_from_vector(1000.0, 0.0) == pick_dir8_from_vector(0.5, 0.0)


# --- pick_row_for_state ---------------------------------------------------------

def test_row_direct_hit():
    rows = {"front": 0, "right": 2, "back": 4, "left": 6}
    assert pick_row_for_state(rows, 1.0, 0.0) == 2      # right


def test_row_diagonal_falls_back_to_cardinal():
    # frontRight ausente -> front
    rows = {"front": 0, "back": 4}
    assert pick_row_for_state(rows, 1.0, 1.0) == 0
    # backLeft ausente -> back
    assert pick_row_for_state(rows, -1.0, -1.0) == 4


def test_row_missing_everything_falls_back_to_front_then_zero():
    assert pick_row_for_state({"front": 7}, 1.0, 0.0) == 7   # 'right' ausente -> front
    assert pick_row_for_state({}, 1.0, 0.0) == 0             # nada -> 0


def test_row_uses_cursor_vector_argument():
    rows = {"front": 0, "back": 4}
    assert pick_row_for_state(rows, 0.0, -1.0) == 4          # hacia arriba => back


# --- pick_state_by_speed ------------------------------------------------------

def test_state_walk_when_walking():
    assert pick_state_by_speed(1000.0, 900.0, is_walking=True, has_sleep=True) == "walk"


def test_state_idle_when_not_walking_and_recent_movement():
    assert pick_state_by_speed(1000.0, 900.0, is_walking=False, has_sleep=True) == "idle"


def test_state_sleep_after_timeout():
    # now - last_move = 40s > 30s por defecto
    assert pick_state_by_speed(40_000.0, 0.0, is_walking=False, has_sleep=True) == "sleep"


def test_state_no_sleep_when_disabled():
    assert pick_state_by_speed(40_000.0, 0.0, is_walking=False, has_sleep=False) == "idle"


def test_state_sleep_timeout_has_priority_over_walking():
    # El chequeo de sleep va primero: si se cumple el timeout, gana aunque is_walking
    # sea True. En la práctica no coincide (si el cursor no se movió en 40s, el sprite
    # ya llegó a su destino y is_walking es False), pero se fija la semántica real.
    assert pick_state_by_speed(40_000.0, 0.0, is_walking=True, has_sleep=True) == "sleep"


def test_state_custom_sleep_timeout():
    assert pick_state_by_speed(
        10_000.0, 0.0, is_walking=False, has_sleep=True, sleep_timeout_ms=5_000.0
    ) == "sleep"
    assert pick_state_by_speed(
        4_000.0, 0.0, is_walking=False, has_sleep=True, sleep_timeout_ms=5_000.0
    ) == "idle"


# --- AnimationState.advance --------------------------------------------------

def _states():
    common = dict(sheet="x.webp", frame_w=1, frame_h=1, rows={"front": 0})
    return {
        "idle": StateDef(fps=1000, frames=4, **common),   # ms_per_frame = 1
        "walk": StateDef(fps=1000, frames=2, **common),
    }


def test_advance_same_state_advances_frames():
    anim = AnimationState(name="idle", frame=0)
    anim.advance(3.0, _states(), "idle", now_ms=0.0, vel_avg=(0.0, 0.0))
    assert anim.name == "idle"
    assert anim.frame == 3


def test_advance_frame_wraps_modulo_frames():
    anim = AnimationState(name="walk", frame=0)
    anim.advance(5.0, _states(), "walk", now_ms=0.0, vel_avg=(0.0, 0.0))
    assert anim.frame == 5 % 2


def test_advance_state_switch_waits_for_cycle_end_or_timeout():
    anim = AnimationState(name="idle", frame=1)   # no está al final del ciclo (frames=4)
    anim.advance(0.0, _states(), "walk", now_ms=0.0, vel_avg=(0.0, 0.0))
    assert anim.name == "idle"                    # aún no conmuta
    assert anim.pending is not None and anim.pending.name == "walk"


def test_advance_state_switch_on_timeout_does_not_reset_frame():
    anim = AnimationState(name="idle", frame=2)
    anim.advance(0.0, _states(), "walk", now_ms=0.0, vel_avg=(0.0, 0.0))
    anim.advance(0.0, _states(), "walk", now_ms=301.0, vel_avg=(0.0, 0.0))  # > 300 ms
    assert anim.name == "walk"
    assert anim.frame == 2                        # fidelidad literal: no se resetea (D-001)


def test_advance_state_switch_at_cycle_end_is_immediate():
    anim = AnimationState(name="idle", frame=3)   # frames-1 => fin de ciclo
    anim.advance(0.0, _states(), "walk", now_ms=0.0, vel_avg=(0.0, 0.0))
    assert anim.name == "walk"


def test_advance_recomputes_row_every_tick():
    anim = AnimationState(name="idle", frame=0)
    states = _states()
    states["idle"] = StateDef(
        sheet="x.webp", frame_w=1, frame_h=1, fps=1000, frames=4,
        rows={"front": 0, "back": 4},
    )
    anim.advance(0.0, states, "idle", now_ms=0.0, vel_avg=(0.0, -1.0))
    assert anim.row == 4
