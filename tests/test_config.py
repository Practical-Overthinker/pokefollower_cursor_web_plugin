"""Persistencia y saneo de configuración (config.py).

Todos los tests que escriben usan la fixture `isolated_config` para no tocar el
`config.json` real del desarrollador.
"""
from __future__ import annotations

import json

import pytest

import config


def test_defaults_are_within_declared_ranges():
    cfg = config.Config()
    assert config.SCALE_MIN <= cfg.scale <= config.SCALE_MAX
    assert config.OFFSET_MIN <= cfg.offset <= config.OFFSET_MAX
    assert config.SPEED_CONFIG_MIN <= cfg.lerp <= config.SPEED_CONFIG_MAX
    assert config.SLEEP_AFTER_MIN <= cfg.sleep_after <= config.SLEEP_AFTER_MAX


def test_load_missing_file_returns_defaults(isolated_config):
    assert not isolated_config.exists()
    assert config.load() == config.Config()


def test_load_valid_file_round_trips(isolated_config):
    original = config.Config(pokemon="retro/gen-1/025-pikachu", scale=1.5, sleep_after=42)
    config.save(original)
    assert isolated_config.exists()
    assert config.load() == original


def test_load_malformed_json_falls_back_to_defaults(isolated_config):
    isolated_config.write_text("{ this is not json ", encoding="utf-8")
    assert config.load() == config.Config()


def test_load_missing_keys_are_filled_from_defaults(isolated_config):
    isolated_config.write_text(json.dumps({"pokemon": "retro/gen-1/001-bulbasaur"}), encoding="utf-8")
    cfg = config.load()
    assert cfg.pokemon == "retro/gen-1/001-bulbasaur"
    assert cfg.scale == config.Config().scale
    assert cfg.enabled == config.Config().enabled


def test_load_unknown_keys_are_ignored(isolated_config):
    isolated_config.write_text(
        json.dumps({"scale": 1.1, "totally_unknown": 999, "start_with_windows": True}),
        encoding="utf-8",
    )
    cfg = config.load()
    assert cfg.scale == pytest.approx(1.1)
    assert not hasattr(cfg, "totally_unknown")


@pytest.mark.parametrize(
    "field, raw, expected",
    [
        ("scale", 999.0, config.SCALE_MAX),
        ("scale", -5.0, config.SCALE_MIN),
        ("offset", -50.0, config.OFFSET_MIN),
        ("offset", 10_000.0, config.OFFSET_MAX),
        ("lerp", 5.0, config.SPEED_CONFIG_MAX),
        ("lerp", 0.0, config.SPEED_CONFIG_MIN),
        ("sleep_after", 99_999, config.SLEEP_AFTER_MAX),
        ("sleep_after", 1, config.SLEEP_AFTER_MIN),
    ],
)
def test_load_clamps_out_of_range_values(isolated_config, field, raw, expected):
    isolated_config.write_text(json.dumps({field: raw}), encoding="utf-8")
    cfg = config.load()
    assert getattr(cfg, field) == pytest.approx(expected)


def test_load_wrong_type_falls_back_to_defaults(isolated_config):
    isolated_config.write_text(json.dumps({"scale": "not-a-number"}), encoding="utf-8")
    assert config.load() == config.Config()


def test_save_is_pretty_printed_json(isolated_config):
    config.save(config.Config())
    text = isolated_config.read_text(encoding="utf-8")
    assert json.loads(text)["pokemon"] == config.Config().pokemon
    assert "\n" in text          # indent=2


def test_save_swallows_os_error(isolated_config, monkeypatch):
    # config.save() se llama en cada movimiento de slider; un fallo de disco no debe
    # tumbar la app (CLAUDE.md).
    def boom(*_a, **_kw):
        raise OSError("disk full")

    monkeypatch.setattr(type(isolated_config), "write_text", boom)
    config.save(config.Config())   # no debe propagar
