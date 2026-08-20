"""Genera assets/icons/pokeball.ico multi-resolución (16/32/48/128/256) a partir de
los PNG existentes en assets/icons/. Script de authoring, no forma parte del runtime.

Requiere Pillow (requirements-dev.txt) — el plugin ICO de Qt (QImageWriter) NO soporta
escribir múltiples resoluciones en un solo archivo: solo conserva la última imagen escrita
(verificado empíricamente: un .ico generado con QImageWriter reporta count=1 en su
ICONDIR header pese a llamar a write() cuatro veces). Ver decision.log D-0xx.

Uso: python tools/make_icon.py
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Falta Pillow. Instalar con: pip install -r requirements-dev.txt", file=sys.stderr)
    sys.exit(1)

ICONS_DIR = Path(__file__).parent.parent / "assets" / "icons"
SOURCE_SIZES = (16, 32, 48, 128)  # PNG ya existentes, dibujados a mano en cada tamaño
UPSCALED_SIZE = 256  # no hay fuente nativa; se deriva del más grande con nearest-neighbor
OUTPUT_PATH = ICONS_DIR / "pokeball.ico"


def main() -> int:
    missing = [s for s in SOURCE_SIZES if not (ICONS_DIR / f"pokeball-{s}.png").exists()]
    if missing:
        print(f"Faltan PNG fuente para tamaños: {missing}", file=sys.stderr)
        return 1

    images = {s: Image.open(ICONS_DIR / f"pokeball-{s}.png").convert("RGBA") for s in SOURCE_SIZES}
    largest = max(SOURCE_SIZES)
    # nearest, no bicubic: es pixel art (coherente con FastTransformation en follower.py)
    upscaled = images[largest].resize((UPSCALED_SIZE, UPSCALED_SIZE), Image.NEAREST)

    # El plugin ICO de Pillow solo REDUCE desde la imagen base — nunca amplía. Por eso el
    # base debe ser la imagen más grande (el upscale a 256), y el resto se pasan ya en su
    # tamaño exacto vía append_images para que se embeban tal cual, sin remuestreo.
    ordered_sizes = sorted({UPSCALED_SIZE, *SOURCE_SIZES}, reverse=True)
    base = upscaled
    append_images = [images[s] for s in ordered_sizes if s != UPSCALED_SIZE]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    base.save(
        OUTPUT_PATH,
        format="ICO",
        sizes=[(s, s) for s in ordered_sizes],
        append_images=append_images,
    )

    with open(OUTPUT_PATH, "rb") as f:
        _, _, count = struct.unpack("<HHH", f.read(6))

    if count != len(ordered_sizes):
        print(
            f"AVISO: el .ico resultante tiene {count} imágenes, se esperaban {len(ordered_sizes)}.",
            file=sys.stderr,
        )
        return 1

    print(f"OK: {OUTPUT_PATH} generado con {count} resoluciones: {ordered_sizes}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
