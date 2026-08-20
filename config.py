"""Persistencia local de configuración. Única puerta a config.json."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"

# Rango del slider de velocidad (llamado "lerp" en el original por legado, no es un lerp).
SPEED_CONFIG_MIN = 0.05
SPEED_CONFIG_MAX = 0.50
WALK_SPEED_MIN_PXPS = 80.0
WALK_SPEED_MAX_PXPS = 640.0


@dataclass
class Config:
    enabled: bool = True
    pokemon: str = "retro/gen-1/009-blastoise"
    scale: float = 1.25
    offset: float = 30.0
    lerp: float = 0.20
    sleep: bool = True
    sleep_after: int = 30
    start_with_windows: bool = False


def load() -> Config:
    if not CONFIG_PATH.exists():
        return Config()
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    defaults = asdict(Config())
    defaults.update({k: v for k, v in data.items() if k in defaults})
    return Config(**defaults)


def save(config: Config) -> None:
    CONFIG_PATH.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")


def walk_speed_from_config(lerp: float) -> float:
    """Convierte el slider de velocidad (0.05..0.50) a px/s (80..640)."""
    t = (lerp - SPEED_CONFIG_MIN) / (SPEED_CONFIG_MAX - SPEED_CONFIG_MIN)
    t = max(0.0, min(1.0, t))
    return WALK_SPEED_MIN_PXPS + t * (WALK_SPEED_MAX_PXPS - WALK_SPEED_MIN_PXPS)
