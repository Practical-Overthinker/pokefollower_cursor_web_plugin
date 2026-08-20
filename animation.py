"""Selección de estado/dirección/frame. Sin Qt, funciones puras o casi.

Nombres conservados iguales a reference/content.js para mapeo directo durante el port.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from pokemon import StateDef

# Orden exacto de reference/content.js pickDir8FromVector: idx 0 = ángulo 0° (derecha),
# +y es ABAJO (coordenadas de pantalla), cada sector cubre 45° centrados en su eje.
DIRECTIONS_BY_INDEX = (
    "right", "frontRight", "front", "frontLeft",
    "left", "backLeft", "back", "backRight",
)

# Fallback diagonal->cardinal de pickRowForState cuando el pack no tiene esa fila.
DIAGONAL_FALLBACK = {
    "frontRight": "front",
    "frontLeft": "front",
    "backRight": "back",
    "backLeft": "back",
}

SLEEP_TIMEOUT_MS = 30_000.0
STATE_TRANSITION_TIMEOUT_MS = 300.0
DEAD_ZONE_PXPS = 0.3


def pick_dir8_from_vector(vx: float, vy: float) -> str:
    """Réplica de pickDir8FromVector(): ángulo del vector -> una de 8 direcciones."""
    if abs(vx) <= DEAD_ZONE_PXPS and abs(vy) <= DEAD_ZONE_PXPS:
        return "front"
    angle = math.atan2(vy, vx)
    norm = angle % (2 * math.pi)
    idx = int((norm + math.pi / 8) / (math.pi / 4)) % 8
    return DIRECTIONS_BY_INDEX[idx]


def pick_row_for_state(rows: dict[str, int], vx: float, vy: float) -> int:
    """Réplica de pickRowForState(): usa la velocidad del CURSOR, no del sprite."""
    dir8 = pick_dir8_from_vector(vx, vy)
    if dir8 in rows:
        return rows[dir8]
    fallback = DIAGONAL_FALLBACK.get(dir8, dir8)
    if fallback in rows:
        return rows[fallback]
    return rows.get("front", 0)


def pick_state_by_speed(now_ms: float, last_move_ts: float, is_walking: bool, has_sleep: bool) -> str:
    """Réplica de pickStateBySpeed(): el nombre miente, no usa velocidad del cursor."""
    if has_sleep and (now_ms - last_move_ts) > SLEEP_TIMEOUT_MS:
        return "sleep"
    return "walk" if is_walking else "idle"


@dataclass
class PendingState:
    name: str
    queued_at: float


@dataclass
class AnimationState:
    name: str = "idle"
    frame: int = 0
    acc_ms: float = 0.0
    row: int = 0
    pending: Optional[PendingState] = None

    def advance(
        self,
        dt_ms: float,
        states: dict[str, StateDef],
        desired_state: str,
        now_ms: float,
        vel_avg: tuple[float, float],
    ) -> None:
        """Réplica de los pasos (1)-(3) y (7)-(8) de tick() en reference/content.js."""
        if desired_state != self.name:
            if self.pending is None or self.pending.name != desired_state:
                self.pending = PendingState(name=desired_state, queued_at=now_ms)
            current_state = states[self.name]
            at_cycle_end = self.frame >= current_state.frames - 1
            timed_out = (now_ms - self.pending.queued_at) > STATE_TRANSITION_TIMEOUT_MS
            if at_cycle_end or timed_out:
                # Frame y acc_ms NO se resetean al conmutar (fidelidad literal, D-001).
                self.name = self.pending.name
                self.pending = None
        else:
            self.pending = None

        state = states[self.name]
        ms_per_frame = 1000.0 / state.fps
        self.acc_ms += dt_ms  # sin clampear, igual que el original
        while self.acc_ms >= ms_per_frame:
            self.acc_ms -= ms_per_frame
            self.frame = (self.frame + 1) % state.frames

        # La fila se recalcula cada tick: el sprite gira instantáneamente.
        self.row = pick_row_for_state(state.rows, vel_avg[0], vel_avg[1])
