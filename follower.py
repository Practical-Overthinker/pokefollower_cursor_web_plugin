"""Ventana transparente, click-through, always-on-top que sigue el cursor."""
from __future__ import annotations

import math
import time

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QCursor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget

import config
from animation import AnimationState, pick_state_by_speed
from pokemon import Pack

WINDOW_FLAGS = (
    Qt.FramelessWindowHint
    | Qt.WindowStaysOnTopHint
    | Qt.Tool
    | Qt.WindowTransparentForInput
    | Qt.WindowDoesNotAcceptFocus
    | Qt.NoDropShadowWindowHint
)

TICK_INTERVAL_MS = 16
ARRIVE_RADIUS_PX = 6.0
SLOW_RADIUS_PX = 60.0
OFFSET_DIR_LERP = 0.08
VEL_EMA_TAU_MS = 70.0  # tau equivalente al EMA por evento (alpha=0.2 @ ~60Hz) del original
DRAG_SPEED_THRESHOLD_PXPS = 40.0


def compute_target(
    last_mouse: tuple[float, float],
    vel_avg: tuple[float, float],
    speed_avg: float,
    offset_dir: tuple[float, float],
    offset: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Réplica de computeTarget(): target detrás/encima del cursor según su velocidad.

    offset_dir no se renormaliza tras el lerp (fidelidad literal, D-001).
    """
    has_dir = speed_avg > DRAG_SPEED_THRESHOLD_PXPS
    if has_dir:
        desired = (-vel_avg[0] / speed_avg, -vel_avg[1] / speed_avg)
    else:
        desired = (0.0, -1.0)

    new_offset_dir = (
        offset_dir[0] + (desired[0] - offset_dir[0]) * OFFSET_DIR_LERP,
        offset_dir[1] + (desired[1] - offset_dir[1]) * OFFSET_DIR_LERP,
    )
    target = (
        last_mouse[0] + new_offset_dir[0] * offset,
        last_mouse[1] + new_offset_dir[1] * offset,
    )
    return target, new_offset_dir


def step_position(
    pos: tuple[float, float],
    target: tuple[float, float],
    walk_speed_pxps: float,
    dt_ms: float,
) -> tuple[tuple[float, float], bool]:
    """Réplica del bloque de movimiento de tick(): radios de llegada/frenado."""
    dx = target[0] - pos[0]
    dy = target[1] - pos[1]
    dist = math.hypot(dx, dy)
    if dist <= ARRIVE_RADIUS_PX:
        return pos, False

    speed = walk_speed_pxps * (dist / SLOW_RADIUS_PX) if dist < SLOW_RADIUS_PX else walk_speed_pxps
    move_dt_ms = min(dt_ms, 50.0)
    move_dist = min(dist, speed * move_dt_ms / 1000.0)
    new_pos = (pos[0] + dx / dist * move_dist, pos[1] + dy / dist * move_dist)
    return new_pos, True


class FollowerWindow(QWidget):
    def __init__(
        self,
        pack: Pack,
        scale: float,
        offset: float,
        lerp: float,
        sleep_enabled: bool = True,
        sleep_after: int = 30,
    ):
        super().__init__()
        self._pack = pack
        self._scale = scale
        self._offset = offset
        self._lerp = lerp
        self._sleep_enabled = sleep_enabled
        self._sleep_after_ms = float(sleep_after) * 1000.0
        self._pixmap = QPixmap()

        self.setWindowFlags(WINDOW_FLAGS)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._anim = AnimationState()
        self._pos = (0.0, 0.0)
        self._offset_dir = (0.0, -1.0)
        self._vel_avg = (0.0, 0.0)
        self._speed_avg = 0.0
        self._is_walking = False
        self._last_cursor = QCursor.pos()
        self._last_move_ts = 0.0
        self._last_tick_ms = 0.0

        self._timer = QTimer(self)
        self._timer.setInterval(TICK_INTERVAL_MS)
        self._timer.timeout.connect(self._tick)

        self.set_frame("idle", 0, 0)

    # -- configuración en caliente ------------------------------------------

    def set_pack(self, pack: Pack) -> None:
        """Cambia de Pokémon en caliente. Reinicia la animación: los índices de
        fila/frame del pack anterior no son válidos para el nuevo (frame counts
        y filas difieren entre packs)."""
        self._pack = pack
        self._anim = AnimationState()
        self.set_frame("idle", 0, 0)

    def set_speed_config(self, lerp: float) -> None:
        self._lerp = lerp

    def set_offset(self, offset: float) -> None:
        self._offset = offset

    def set_scale(self, scale: float) -> None:
        self._scale = scale
        self.set_frame(self._anim.name, self._anim.row, self._anim.frame)

    def set_sleep_config(self, enabled: bool, sleep_after: int) -> None:
        self._sleep_enabled = enabled
        self._sleep_after_ms = float(sleep_after) * 1000.0

    # -- ciclo de vida --------------------------------------------------------

    def start(self) -> None:
        now = time.perf_counter() * 1000.0
        cursor = QCursor.pos()
        self._pos = (float(cursor.x()), float(cursor.y() - 30))
        self._last_cursor = cursor
        self._last_move_ts = now
        self._last_tick_ms = now
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    # -- render ---------------------------------------------------------------

    def set_frame(self, state_name: str, row: int, frame: int) -> None:
        state = self._pack.states[state_name]
        frame = frame % state.frames
        raw_pixmap = self._pack.frame_pixmap(state_name, row, frame)

        dpr = self.devicePixelRatioF() if self.windowHandle() else 1.0
        physical_w = max(1, round(state.frame_w * self._scale * dpr))
        physical_h = max(1, round(state.frame_h * self._scale * dpr))
        scaled = raw_pixmap.scaled(
            physical_w, physical_h, Qt.IgnoreAspectRatio, Qt.FastTransformation
        )
        scaled.setDevicePixelRatio(dpr)
        self._pixmap = scaled

        logical_w = math.ceil(state.frame_w * self._scale)
        logical_h = math.ceil(state.frame_h * self._scale)
        if self.width() != logical_w or self.height() != logical_h:
            self.resize(logical_w, logical_h)
        self.update()

    def move_center_to(self, center: QPoint) -> None:
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)

    def paintEvent(self, event) -> None:  # noqa: N802 (nombre impuesto por Qt)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, False)
        painter.drawPixmap(0, 0, self._pixmap)
        painter.end()

    def place_at_startup_position(self) -> None:
        cursor_pos = QCursor.pos()
        self.move_center_to(QPoint(cursor_pos.x(), cursor_pos.y() - 30))

    # -- loop principal ---------------------------------------------------------

    def _tick(self) -> None:
        now = time.perf_counter() * 1000.0
        dt_ms = max(1.0, now - self._last_tick_ms)
        self._last_tick_ms = now

        cursor = QCursor.pos()
        if cursor != self._last_cursor:
            dx = cursor.x() - self._last_cursor.x()
            dy = cursor.y() - self._last_cursor.y()
            vx = dx * 1000.0 / dt_ms
            vy = dy * 1000.0 / dt_ms
            # EMA dependiente de dt (equivalente al EMA por evento del original bajo polling).
            alpha = 1.0 - math.exp(-dt_ms / VEL_EMA_TAU_MS)
            self._vel_avg = (
                self._vel_avg[0] + (vx - self._vel_avg[0]) * alpha,
                self._vel_avg[1] + (vy - self._vel_avg[1]) * alpha,
            )
            self._speed_avg = math.hypot(*self._vel_avg)
            self._last_move_ts = now
            self._last_cursor = cursor
        # Si no se movió, vel_avg queda congelado en su último valor (fidelidad D-001).

        has_sleep = self._pack.has_state("sleep") and self._sleep_enabled
        desired_state = pick_state_by_speed(
            now, self._last_move_ts, self._is_walking, has_sleep, self._sleep_after_ms
        )
        self._anim.advance(dt_ms, self._pack.states, desired_state, now, self._vel_avg)

        walk_speed = config.walk_speed_from_config(self._lerp)
        last_mouse = (float(cursor.x()), float(cursor.y()))
        target, self._offset_dir = compute_target(
            last_mouse, self._vel_avg, self._speed_avg, self._offset_dir, self._offset
        )
        self._pos, self._is_walking = step_position(self._pos, target, walk_speed, dt_ms)

        state = self._pack.states[self._anim.name]
        self.set_frame(self._anim.name, self._anim.row, self._anim.frame % state.frames)
        self.move_center_to(QPoint(round(self._pos[0]), round(self._pos[1])))
