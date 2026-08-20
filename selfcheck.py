"""Verificación post-build: confirma que el bundle congelado tiene todo lo que necesita
para funcionar de verdad, no solo que "abre sin traceback". Diseñado contra los fallos
silenciosos concretos de esta app (icono vacío, miniaturas ausentes, sprite indecodificable).

Se invoca con `PokeFollower.exe --self-check` (ver main.py). Vive en su propio módulo para
poder correr igual desde fuente que congelado, sin crear ventanas.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

from PySide6.QtGui import QIcon, QImageReader
from PySide6.QtWidgets import QApplication

import config
import paths
from pokemon import PackLoadError, load_index, load_pack
from tray import ICON_PATH


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def run_checks() -> list[CheckResult]:
    results: list[CheckResult] = []

    # 1. Formatos de imagen — el fallo más probable: sin qwebp, todos los sprites quedan
    # invisibles sin ningún error (precedente: D-008 del port ya usó este mismo oráculo).
    formats = {f.data().decode() for f in QImageReader.supportedImageFormats()}
    ok = "webp" in formats and "png" in formats
    results.append(CheckResult("formatos webp+png soportados", ok, f"disponibles: {sorted(formats)}"))

    # 2. assets_dir + índice legibles.
    index_path = paths.assets_dir() / "packs" / "index.json"
    assets_ok = paths.assets_dir().exists() and index_path.exists()
    results.append(CheckResult("assets_dir + index.json", assets_ok, str(paths.assets_dir())))

    # 3. Exactamente 493 entradas — número duro, no ">0".
    entries: list = []
    try:
        entries = load_index()
        count_ok = len(entries) == 493
        results.append(CheckResult("493 entradas en el índice", count_ok, f"{len(entries)} encontradas"))
    except PackLoadError as exc:
        results.append(CheckResult("493 entradas en el índice", False, str(exc)))

    # 4. Las 493 miniaturas existen — lo que selector.py silenciaría sin este check.
    missing_thumbs = [e.id for e in entries if not e.thumbnail.exists()]
    results.append(CheckResult(
        "493 miniaturas presentes",
        not missing_thumbs,
        "todas presentes" if not missing_thumbs else f"{len(missing_thumbs)} faltantes, ej: {missing_thumbs[:3]}",
    ))

    # 5. Decodificación real de un frame por generación — un .webp presente pero
    # indecodificable (plugin faltante, archivo corrupto) falla aquí, no en producción.
    seen_gens: set[str] = set()
    decode_failures: list[str] = []
    for entry in entries:
        if entry.generation in seen_gens:
            continue
        seen_gens.add(entry.generation)
        try:
            pack = load_pack(entry.id)
            frame = pack.frame_pixmap("idle", 0, 0)
            if frame.isNull():
                decode_failures.append(f"{entry.id} (pixmap nulo)")
        except PackLoadError as exc:
            decode_failures.append(f"{entry.id} ({exc})")
    results.append(CheckResult(
        f"decodificación real ({len(seen_gens)} generaciones)",
        not decode_failures,
        "OK" if not decode_failures else f"fallos: {decode_failures}",
    ))

    # 6. Icono del tray no nulo — el fallo silencioso de tray.py (QIcon vacío sin error).
    icon = QIcon(str(ICON_PATH))
    results.append(CheckResult("icono del tray no nulo", not icon.isNull(), str(ICON_PATH)))

    # 7. Config escribible en la ruta esperada (APPDATA si frozen).
    try:
        cfg = config.load()
        config.save(cfg)
        write_ok = config.CONFIG_PATH.exists()
        results.append(CheckResult("config escribible", write_ok, str(config.CONFIG_PATH)))
    except OSError as exc:
        results.append(CheckResult("config escribible", False, str(exc)))

    return results


def main() -> int:
    app = QApplication(sys.argv)  # QImageReader/QPixmap necesitan una QGuiApplication activa
    del app  # no se usa más allá de inicializar Qt; no se crea ninguna ventana

    results = run_checks()
    lines = ["PokéFollower — self-check", ""]
    all_ok = True
    for r in results:
        status = "OK  " if r.passed else "FAIL"
        lines.append(f"[{status}] {r.name}: {r.detail}")
        all_ok = all_ok and r.passed
    lines.append("")
    lines.append("RESULTADO: " + ("TODO OK" if all_ok else "HAY FALLOS"))
    report = "\n".join(lines)

    log_path = paths.config_dir() / "selfcheck.log"
    try:
        log_path.write_text(report, encoding="utf-8")
    except OSError:
        pass

    print(report)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
