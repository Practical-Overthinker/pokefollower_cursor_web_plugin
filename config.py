"""Persistencia local de configuración. Única puerta a config.json."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

import paths

CONFIG_PATH = paths.config_dir() / "config.json"

# Rango del slider de velocidad (llamado "lerp" en el original por legado, no es un lerp).
SPEED_CONFIG_MIN = 0.05
SPEED_CONFIG_MAX = 0.50
WALK_SPEED_MIN_PXPS = 80.0
WALK_SPEED_MAX_PXPS = 640.0

# Rangos válidos para los controles de Settings (settings.py) y para sanear config.json.
SCALE_MIN, SCALE_MAX = 0.5, 3.0
OFFSET_MIN, OFFSET_MAX = 0.0, 100.0
SLEEP_AFTER_MIN, SLEEP_AFTER_MAX = 5, 300


@dataclass
class Config:
    enabled: bool = True
    pokemon: str = "retro/gen-1/009-blastoise"
    scale: float = 1.25
    offset: float = 30.0
    lerp: float = 0.20
    sleep: bool = True
    sleep_after: int = 30


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _sanitize(cfg: Config) -> Config:
    """Corrige valores fuera de rango (p.ej. tras editar config.json a mano)."""
    cfg.scale = _clamp(float(cfg.scale), SCALE_MIN, SCALE_MAX)
    cfg.offset = _clamp(float(cfg.offset), OFFSET_MIN, OFFSET_MAX)
    cfg.lerp = _clamp(float(cfg.lerp), SPEED_CONFIG_MIN, SPEED_CONFIG_MAX)
    cfg.sleep_after = int(_clamp(int(cfg.sleep_after), SLEEP_AFTER_MIN, SLEEP_AFTER_MAX))
    return cfg


def load() -> Config:
    if not CONFIG_PATH.exists():
        return Config()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    defaults = asdict(Config())
    defaults.update({k: v for k, v in data.items() if k in defaults})
    try:
        cfg = Config(**defaults)
        return _sanitize(cfg)
    except (TypeError, ValueError):
        # Tipo incompatible en el JSON (p.ej. scale: "grande" tras editarlo a mano):
        # _sanitize hace float()/int() y puede reventar. Fallback completo a defaults.
        return Config()


def save(config: Config) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    except OSError:
        # No hay forma de mostrarle esto al usuario desde aquí (config.py no toca Qt).
        # Preferible perder la persistencia de este cambio a tumbar la app en cada slider.
        pass


def walk_speed_from_config(lerp: float) -> float:
    """Convierte el slider de velocidad (0.05..0.50) a px/s (80..640)."""
    t = (lerp - SPEED_CONFIG_MIN) / (SPEED_CONFIG_MAX - SPEED_CONFIG_MIN)
    t = max(0.0, min(1.0, t))
    return WALK_SPEED_MIN_PXPS + t * (WALK_SPEED_MAX_PXPS - WALK_SPEED_MIN_PXPS)
