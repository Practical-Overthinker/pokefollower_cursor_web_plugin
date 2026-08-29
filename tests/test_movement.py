"""Lógica pura de movimiento: mapeo del slider de velocidad (config.py) y las funciones
a nivel de módulo de follower.py (compute_target, step_position). Sin Qt, sin FollowerWindow.
"""
from __future__ import annotations

import math

import pytest

import config
from follower import (
    ARRIVE_RADIUS_PX,
    DRAG_SPEED_THRESHOLD_PXPS,
    OFFSET_DIR_LERP,
    SLOW_RADIUS_PX,
    compute_target,
    step_position,
)


# --- walk_speed_from_config ---------------------------------------------------

def test_walk_speed_lower_bound():
    assert config.walk_speed_from_config(config.SPEED_CONFIG_MIN) == pytest.approx(
        config.WALK_SPEED_MIN_PXPS
    )


def test_walk_speed_upper_bound():
    assert config.walk_speed_from_config(config.SPEED_CONFIG_MAX) == pytest.approx(
        config.WALK_SPEED_MAX_PXPS
    )


def test_walk_speed_midpoint():
    mid = (config.SPEED_CONFIG_MIN + config.SPEED_CONFIG_MAX) / 2
    expected = (config.WALK_SPEED_MIN_PXPS + config.WALK_SPEED_MAX_PXPS) / 2
    assert config.walk_speed_from_config(mid) == pytest.approx(expected)


@pytest.mark.parametrize("value", [-5.0, 0.0, 10.0])
def test_walk_speed_clamps_out_of_range(value):
    result = config.walk_speed_from_config(value)
    assert config.WALK_SPEED_MIN_PXPS <= result <= config.WALK_SPEED_MAX_PXPS


# --- compute_target ---------------------------------------------------------

def test_compute_target_slow_cursor_uses_upward_default():
    target, new_dir = compute_target(
        last_mouse=(100.0, 100.0),
        vel_avg=(5.0, 0.0),
        speed_avg=5.0,                       # < 40 => sin dirección de arrastre
        offset_dir=(0.0, -1.0),
        offset=30.0,
    )
    assert new_dir == pytest.approx((0.0, -1.0))
    assert target == pytest.approx((100.0, 70.0))


def test_compute_target_fast_cursor_places_behind_motion():
    # cursor moviéndose a la derecha rápido => el sprite queda a la izquierda del cursor
    target, new_dir = compute_target(
        last_mouse=(100.0, 100.0),
        vel_avg=(100.0, 0.0),
        speed_avg=100.0,
        offset_dir=(0.0, -1.0),
        offset=30.0,
    )
    expected_dir = (
        0.0 + (-1.0 - 0.0) * OFFSET_DIR_LERP,
        -1.0 + (0.0 - (-1.0)) * OFFSET_DIR_LERP,
    )
    assert new_dir == pytest.approx(expected_dir)
    assert target[0] < 100.0                  # detrás (a la izquierda) del cursor


def test_compute_target_threshold_is_exclusive_lower():
    _, at = compute_target((0.0, 0.0), (0.0, 0.0), DRAG_SPEED_THRESHOLD_PXPS, (0.0, -1.0), 10.0)
    _, above = compute_target(
        (0.0, 0.0), (DRAG_SPEED_THRESHOLD_PXPS + 1.0, 0.0),
        DRAG_SPEED_THRESHOLD_PXPS + 1.0, (0.0, -1.0), 10.0,
    )
    # justo en el umbral => todavía usa el default (0,-1)
    assert at == pytest.approx((0.0, -1.0))
    # por encima => empieza a girar hacia -vel
    assert above != pytest.approx((0.0, -1.0))


def test_compute_target_offset_dir_not_renormalized():
    # Rareza D-001: tras el lerp la magnitud puede caer por debajo de 1.
    _, new_dir = compute_target(
        (0.0, 0.0), (0.0, 100.0), 100.0, (1.0, 0.0), 10.0
    )
    assert math.hypot(*new_dir) < 1.0


# --- step_position ---------------------------------------------------------

def test_step_position_within_arrive_radius_does_not_move():
    pos = (0.0, 0.0)
    new_pos, walking = step_position(pos, (3.0, 4.0), walk_speed_pxps=640.0, dt_ms=16.0)
    assert new_pos == pos
    assert walking is False
    assert math.hypot(3.0, 4.0) <= ARRIVE_RADIUS_PX


def test_step_position_moves_toward_target_when_far():
    new_pos, walking = step_position((0.0, 0.0), (1000.0, 0.0), walk_speed_pxps=640.0, dt_ms=16.0)
    assert walking is True
    assert new_pos[0] == pytest.approx(640.0 * 16.0 / 1000.0)
    assert new_pos[1] == pytest.approx(0.0)


def test_step_position_slows_down_inside_slow_radius():
    dist = SLOW_RADIUS_PX / 2                 # 30 px
    new_pos, _ = step_position((0.0, 0.0), (dist, 0.0), walk_speed_pxps=640.0, dt_ms=16.0)
    slowed_speed = 640.0 * (dist / SLOW_RADIUS_PX)
    assert new_pos[0] == pytest.approx(slowed_speed * 16.0 / 1000.0)


def test_step_position_clamps_large_dt():
    # dt de 5000 ms se acota a 50 ms para no teletransportar.
    far, _ = step_position((0.0, 0.0), (100000.0, 0.0), walk_speed_pxps=640.0, dt_ms=5000.0)
    assert far[0] == pytest.approx(640.0 * 50.0 / 1000.0)


def test_step_position_never_overshoots_target():
    new_pos, _ = step_position((0.0, 0.0), (7.0, 0.0), walk_speed_pxps=640.0, dt_ms=1000.0)
    assert new_pos[0] <= 7.0
