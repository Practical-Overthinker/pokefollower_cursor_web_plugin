# CLAUDE.md

## Resumen del proyecto

PokéFollower Desktop es un clon personal, sin fines comerciales, de la extensión de Chrome
[pokefollower_cursor_web_plugin](https://github.com/ThinkrDoer/pokefollower_cursor_web_plugin):
un Pokémon animado (sprites retro estilo PMD) que sigue el cursor con suavizado, 8 direcciones
y estados idle/walk/sleep.

La diferencia es de alcance: en vez de vivir dentro de una pestaña de Chrome, corre a nivel de
todo el escritorio de Windows, como proceso en background controlado desde el System Tray, sin
ventana principal. No modifica el cursor real de Windows — el Pokémon es una ventana propia,
transparente y click-through que se mueve encima del escritorio.

**Estado actual: v1 funcional.** El código de la extensión Chrome original vive intacto en
`reference/` (solo lectura, no se ejecuta). La app de escritorio en Python/PySide6 está
implementada y validada en Windows real: ventana transparente click-through, seguimiento de
cursor con suavizado, 8 direcciones, idle/walk/sleep, tray con selector de 493 Pokémon y
Settings con efecto en vivo. Historial completo del port (decisiones, validaciones,
divergencias) en `workbench/desktop-port/` (no versionado, local a cada sesión de trabajo).

## Stack tecnológico

- Python 3.11+ (probado también en 3.14.6 sin problemas)
- PySide6 (Qt 6) — ventanas transparentes, `QSystemTrayIcon`, `QTimer`, `QCursor`
- venv + pip para gestión de entorno/dependencias (`requirements.txt`, solo `PySide6`)
- Sin framework web, sin Electron, sin servidor, sin base de datos

**Legado (extensión Chrome, en `reference/` — solo lectura, código de consulta):**
- JavaScript vanilla (Manifest V3), sin build step de framework
- Node.js solo para scripts de authoring (`reference/scripts/*.cjs|.js`): parseo de
  spritesheets y generación del índice de packs. `add_pokemon.py` en la raíz los invoca.

No introducir TypeScript, frameworks de UI web, ni gestores de paquetes Python alternativos
(poetry, uv) sin discutirlo antes — la decisión de venv+pip es deliberada por simplicidad,
dado que es un proyecto personal sin distribución.

## Comandos esenciales

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Diagnóstico de assets (carga los 493 packs y reporta fallos):
```bash
python check_packs.py
```

Scripts de authoring de assets (Node, invocados por `add_pokemon.py`, no forman parte del
runtime de la app):
```bash
node reference/scripts/parse-anim.js       # parsea spritesheets crudos -> JSON de pack
node reference/scripts/build-pack-index.cjs  # regenera assets/packs/index.json
```

No hay lint/typecheck/test runner configurado. Si se añaden (ej. `ruff`, `mypy`, `pytest`),
esta sección debe actualizarse con los comandos exactos.

## Arquitectura y mapa del repositorio

```
main.py          # QApplication, lifecycle, wiring de componentes, shutdown
tray.py          # QSystemTrayIcon, QMenu (Enabled, Choose Pokémon..., Settings..., Exit)
follower.py      # ventana transparente click-through, cursor tracking, movement loop, tick()
animation.py     # estado de animación: frames, idle/walk/sleep, direcciones (sin Qt)
pokemon.py       # descubrimiento de packs (load_index), lectura de JSON, carga de sprites
selector.py      # diálogo de selección de Pokémon (búsqueda + rejilla de miniaturas)
settings.py      # diálogo de ajustes (scale/speed/distance/sleep) con efecto en vivo
config.py        # defaults, load/save/clamps de config.json
check_packs.py   # diagnóstico: carga los 493 packs y reporta fallos
config.json      # persistencia local del usuario (no versionar cambios personales)
assets/          # packs y sprites, fuente única para el runtime
reference/       # código legado de la extensión Chrome, solo lectura/consulta
workbench/       # historial de planificación/ejecución del port (no versionado)
```

**Flujo de datos del loop principal** (`FollowerWindow._tick()`, cada ~16ms):
`QCursor.pos()` → actualizar EMA de velocidad (solo si el cursor se movió) → `pick_state_by_speed()`
→ `AnimationState.advance()` (transición de estado + avance de frame) → `compute_target()` →
`step_position()` → `set_frame()` + `move_center_to()`.

## Convenciones de código

- Los nombres de las funciones core de movimiento/animación se conservan iguales a las del
  original (`reference/content.js`) para mapeo directo: `compute_target`, `step_position`
  (equivalente al bloque de movimiento de `tick()`), `pick_dir8_from_vector`,
  `pick_row_for_state`, `pick_state_by_speed`, `walk_speed_from_config`.
- `animation.py` es casi puro (sin Qt) — `pick_dir8_from_vector`, `pick_row_for_state`,
  `pick_state_by_speed` son funciones puras; `AnimationState.advance()` es el único estado
  mutable. `compute_target()` y `step_position()` en `follower.py` también son funciones puras
  a nivel de módulo, separadas de la clase `FollowerWindow` para poder testearlas sin Qt.
- Los archivos JSON de Pokémon (`assets/packs/**/*.json`) son datos, no código — no hardcodear
  lógica específica de un Pokémon en Python; toda diferencia entre Pokémon debe venir del JSON.
  En particular: leer siempre el campo `sheet` de cada estado, nunca derivarlo del nombre del
  estado (ver gotcha de `148-dragonair` abajo).
- `config.py` es la única fuente de verdad para leer/escribir `config.json`. Ningún otro módulo
  debe tocar el archivo directamente. `config.load()` sanea valores fuera de rango o corruptos
  cayendo a defaults — no asumir que los valores en memoria vienen ya validados desde el JSON.
- Un módulo, una responsabilidad: no mezclar lógica de tray (`tray.py`) con lógica de
  movimiento (`follower.py`) ni con carga de assets (`pokemon.py`).

## Reglas arquitectónicas

- No modificar el cursor real de Windows ni instalar drivers/hooks globales de mouse. El
  tracking es por polling con `QCursor.pos()` en un `QTimer`, no un hook del sistema.
- El follower nunca debe bloquear input hacia otras ventanas — la ventana debe ser siempre
  click-through (`WindowTransparentForInput`). Cualquier cambio a `follower.py` que toque flags
  de ventana debe verificar que esto se preserva (ver `WINDOW_FLAGS` en `follower.py`).
- No añadir servidor, cuenta, telemetría, ni sincronización en la nube. Toda persistencia es
  local vía `config.json`.
- No copiar infraestructura de Chrome (`chrome.storage`, `chrome.runtime`, DOM, popup HTML,
  `requestAnimationFrame`) al puerto Python — solo la semántica de movimiento/animación.
- Mantener el scope acotado a lo listado en el handoff original: sin ataques, emotes,
  multi-follower, packaging/instalador, ni catálogo online. Autostart de Windows sigue fuera
  de scope. No expandir scope sin confirmarlo con el usuario primero.
- El formato JSON por-Pokémon (`assets/packs/**/*.json`) no se reestructura salvo necesidad
  fuerte — el objetivo es "mismos assets + mismos JSON + runtime diferente".
- `reference/` es solo lectura/consulta. No se ejecuta ni se mantiene funcionalmente; solo se
  toca si hace falta releer la semántica original al portar un comportamiento nuevo.

## Workflow de desarrollo

1. Para cualquier cambio de comportamiento (movimiento, dirección, estados), primero revisar
   la función equivalente en `reference/content.js` para entender la semántica original antes
   de tocar el código Python.
2. Localizar el módulo responsable (`follower.py` para movimiento/ventana, `animation.py` para
   estados/frames, `pokemon.py` para carga de assets, `tray.py`/`selector.py`/`settings.py`
   para UI, `config.py` para persistencia) — evitar lógica cruzada entre módulos.
3. Implementar el cambio siguiendo el patrón existente en el módulo.
4. Si el cambio toca una función pura (`animation.py`, o `compute_target`/`step_position` en
   `follower.py`), verificarla con vectores de prueba antes de integrarla — idealmente
   cruzados contra `reference/content.js` ejecutado con Node (`node -e "..."`), no solo contra
   la propia lectura del código.
5. Ejecutar la app manualmente (`python main.py`) y verificar en el escritorio real: no hay
   test suite automatizado para el comportamiento visual/de integración con Windows
   (click-through, always-on-top, DPI, multi-monitor).
6. Si se tocaron packs o el índice, correr `python check_packs.py` para confirmar que los 493
   siguen cargando sin fallos.
7. Revisar el diff antes de dar por terminado el cambio.

## Testing

No hay framework de testing configurado. La mayor parte del comportamiento crítico (ventana
transparente, click-through, always-on-top, DPI scaling, multi-monitor) es difícil de cubrir
con unit tests y requiere verificación manual en Windows real:

- Verificar visualmente que el follower sigue el cursor con el suavizado esperado.
- Verificar que no bloquea clicks/drag/scroll sobre otras ventanas.
- Probar con escalado de Windows en 100/125/150/200% (100% validado; 125/150/200% pendiente,
  ver `workbench/desktop-port/decision.log` si existe en la sesión).
- Probar con al menos dos monitores, incluyendo coordenadas negativas (monitor a la izquierda).
- Verificar que el tray funciona y que `Exit` cierra realmente el proceso.

`python check_packs.py` sí es un check automatizable y barato — actúa como el equivalente más
cercano a un test de regresión de datos: carga los 493 packs y valida que cada sheet existe y
que ninguna fila/frame se sale de los límites del spritesheet.

Si se extraen más funciones puras en el futuro, son candidatas naturales a unit tests con
`pytest` — actualizar esta sección si se añade esa infraestructura.

## Gotchas y patrones no obvios

- **`sheet` se lee siempre del JSON, nunca se deriva del nombre del estado**: en
  `assets/packs/retro/gen-1/148-dragonair.json`, el estado `idle` usa `"sheet":
  "Walk-Anim.webp"` porque ese pack no tiene `Idle-Anim.webp`. `pokemon.py` funciona
  correctamente porque nunca asume `f"{state_name}-Anim.webp"` — si se toca esa lógica,
  preservar esta indirección.
- **`flipX: true` en los JSON de Pokémon está presente en los 493 packs pero no se usa en
  ningún lado** (ni en el original `reference/content.js` ni en este port) — es metadato
  muerto heredado del pipeline de authoring. Los spritesheets PMD ya traen 8 filas de
  dirección reales, así que no hace falta voltear nada en runtime. No "activarlo" sin motivo.
- **`sleep` con todas las filas en 0**: es habitual (ver Blastoise) que el estado `sleep`
  mapee las 8 direcciones a la fila `0` porque el sprite de dormir no tiene variantes
  direccionales. No es un bug del JSON, no "arreglar" añadiendo filas.
- **La dirección visual (`pick_row_for_state`) se deriva de la velocidad del CURSOR
  (`vel_avg`), no de la trayectoria del sprite** — decisión deliberada del original que
  produce una orientación más natural. Si el Pokémon parece "mirar mal", revisar primero si
  se está pasando el vector correcto antes de tocar los umbrales de `pick_dir8_from_vector`.
- **El EMA de velocidad del cursor se congela cuando el cursor deja de moverse** (no decae a
  cero) — fidelidad deliberada al original, que solo actualiza `velAvg` en eventos
  `mousemove`. Bajo polling (`follower.py`), esto se replica actualizando el EMA solo cuando
  `QCursor.pos()` cambió respecto al tick anterior. No "arreglarlo" haciendo que decaiga: eso
  cambiaría el comportamiento visible respecto al original sin necesidad demostrada.
- **`offset_dir` no se renormaliza tras el lerp en `compute_target()`** — su magnitud puede
  caer momentáneamente por debajo de 1 durante una transición de dirección. Es una rareza
  del original (probablemente no intencional) preservada por fidelidad literal (ver
  `workbench/desktop-port/decision.log`, D-001); no produjo ningún problema visible en las
  validaciones de fases 2-4, así que no se ha corregido.
- **El frame y el acumulador de animación no se resetean al cambiar de estado**
  (`AnimationState.advance()`): el índice de frame se arrastra del estado anterior y se acota
  con módulo contra el nuevo `frames` del estado entrante. Es fidelidad literal al original,
  no un olvido — no "arreglar" añadiendo un reset.
- **No usar mouse hook global ni fullscreen overlay** — fue evaluado y descartado
  deliberadamente a favor de polling con `QTimer` + ventana pequeña. Si surge la tentación de
  "arreglar" latencia con un hook global, es un cambio de arquitectura que debe discutirse.
- **Licencia de los sprites**: los assets de `assets/packs/` vienen de PMD Sprite Repository
  bajo CC-BY-NC-SA 4.0 (ver `CREDITS.txt`). Uso personal está bien; cualquier intención de
  distribuir públicamente el proyecto requiere revisar la licencia antes.

## Definition of Done

Antes de dar un cambio por terminado:

- La app arranca sin errores (`python main.py`) y el tray aparece correctamente.
- El comportamiento se verificó manualmente en el escritorio (no solo leyendo el código) —
  especialmente para cambios que tocan `follower.py` (ventana, click-through, always-on-top).
- No se rompió el click-through: se puede interactuar con ventanas debajo del Pokémon.
- Si se tocó `pokemon.py` o algún pack, `python check_packs.py` sigue reportando 0 fallos.
- El diff se revisó y no incluye scope fuera de lo pedido (ver Reglas arquitectónicas —
  no colar features fuera del scope acordado).
- Si se tocó un archivo JSON de pack, se verificó que sigue siendo JSON válido y que no se
  alteró la semántica de `rows`/`frame`/`fps`/`frames` sin motivo.
- `config.json` de ejemplo/plantilla no contiene datos personales o de sesión que no deban
  versionarse (de hecho, `config.json` está en `.gitignore` — no debería aparecer en `git status`).

No hay hooks/CI configurados que hagan cumplir esto automáticamente — por ahora es disciplina
manual. Si se añade lint/typecheck/test runner, considerar un hook de pre-commit y actualizar
esta sección para reflejar qué se ejecuta obligatoriamente.
