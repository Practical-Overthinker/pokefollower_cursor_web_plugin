"""Ventana de ajustes: escala, velocidad, distancia, sleep. Efecto en vivo."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QWidget,
)

import config

OFFSET_DECIMALS = 0
SCALE_DECIMALS = 2
SPEED_DECIMALS = 2
SLIDER_STEPS = 1000


class SettingsDialog(QDialog):
    """Emite un cambio por parámetro apenas el usuario mueve el control (sin botón Apply)."""

    scale_changed = Signal(float)
    speed_changed = Signal(float)
    offset_changed = Signal(float)
    sleep_config_changed = Signal(bool, int)

    def __init__(self, cfg: config.Config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PokéFollower — Settings")
        self.resize(360, 220)

        layout = QFormLayout(self)

        layout.addRow(
            "Scale",
            self._make_float_row(
                config.SCALE_MIN, config.SCALE_MAX, cfg.scale, self._on_scale_changed, SCALE_DECIMALS
            ),
        )
        layout.addRow(
            "Follow Speed",
            self._make_float_row(
                config.SPEED_CONFIG_MIN,
                config.SPEED_CONFIG_MAX,
                cfg.lerp,
                self._on_speed_changed,
                SPEED_DECIMALS,
            ),
        )
        layout.addRow(
            "Distance",
            self._make_float_row(
                config.OFFSET_MIN, config.OFFSET_MAX, cfg.offset, self._on_offset_changed,
                OFFSET_DECIMALS, suffix=" px",
            ),
        )

        self._sleep_checkbox = QCheckBox("Sleep enabled")
        self._sleep_checkbox.setChecked(cfg.sleep)
        self._sleep_checkbox.toggled.connect(self._emit_sleep_config)
        layout.addRow(self._sleep_checkbox)

        self._sleep_after_spin = QSpinBox()
        self._sleep_after_spin.setRange(config.SLEEP_AFTER_MIN, config.SLEEP_AFTER_MAX)
        self._sleep_after_spin.setSuffix(" s")
        self._sleep_after_spin.setValue(cfg.sleep_after)
        self._sleep_after_spin.valueChanged.connect(self._emit_sleep_config)
        layout.addRow("Sleep after", self._sleep_after_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addRow(buttons)

    def _make_float_row(
        self,
        minv: float,
        maxv: float,
        value: float,
        on_change,
        decimals: int,
        suffix: str = "",
    ) -> QWidget:
        container = QWidget()
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, SLIDER_STEPS)
        slider.setValue(round((value - minv) / (maxv - minv) * SLIDER_STEPS))

        label = QLabel(f"{value:.{decimals}f}{suffix}")
        label.setMinimumWidth(56)

        def _on_slider_value_changed(raw: int) -> None:
            v = minv + (raw / SLIDER_STEPS) * (maxv - minv)
            label.setText(f"{v:.{decimals}f}{suffix}")
            on_change(v)

        slider.valueChanged.connect(_on_slider_value_changed)

        hbox.addWidget(slider, 1)
        hbox.addWidget(label)
        return container

    def _on_scale_changed(self, value: float) -> None:
        self.scale_changed.emit(value)

    def _on_speed_changed(self, value: float) -> None:
        self.speed_changed.emit(value)

    def _on_offset_changed(self, value: float) -> None:
        self.offset_changed.emit(value)

    def _emit_sleep_config(self, *_args) -> None:
        self.sleep_config_changed.emit(
            self._sleep_checkbox.isChecked(), self._sleep_after_spin.value()
        )
