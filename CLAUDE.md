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

**Estado actual: en transición.** Este repo contenía originalmente el código fuente de la
extensión Chrome (JS/Manifest V3). Se está migrando a una app de escritorio Python + PySide6
que reutiliza los assets y el formato de datos de Pokémon tal cual, pero reemplaza toda la
infraestructura específica de navegador. Ver `docs/handoff.md` (o el handoff más reciente en
memoria/histórico de sesión) para el razonamiento arquitectónico completo.

## Stack tecnológico

**Destino (app de escritorio — lo que se está construyendo):**
- Python 3.11+
- PySide6 (Qt 6) — ventanas transparentes, `QSystemTrayIcon`, `QTimer`, `QCursor`
- venv + pip para gestión de entorno/dependencias (`requirements.txt`)
- Sin framework web, sin Electron, sin servidor, sin base de datos

**Legado (extensión Chrome — código de referencia, no se toca salvo migración puntual):**
- JavaScript vanilla (Manifest V3), sin build step de framework
- Node.js solo para scripts de authoring (`src/scripts/*.cjs`): parseo de spritesheets y
  generación del índice de packs

No introducir TypeScript, frameworks de UI web, ni gestores de paquetes Python alternativos
(poetry, uv) sin discutirlo antes — la decisión de venv+pip es deliberada por simplicidad,
dado que es un proyecto personal sin distribución.

## Comandos esenciales

**Python (desktop app):**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
(Aún no existen `requirements.txt` ni `main.py` — se crean en el vertical slice inicial.)

**Node (solo scripts de authoring de assets, heredados de la extensión):**
```bash
npm run parse        # src/scripts/parse-anim.js — parsea spritesheets crudos
npm run build:index  # src/scripts/build-pack-index.cjs — regenera assets/packs/index.json
npm run sync-version # src/scripts/sync-version.cjs — sincroniza versión entre manifest y package.json
```

No hay lint/typecheck/test runner configurado todavía en ninguno de los dos lados. Si se
añaden (ej. `ruff`, `mypy`, `pytest`), esta sección debe actualizarse con los comandos exactos.

## Arquitectura y mapa del repositorio

**Estructura destino** (según handoff; se construye incrementalmente):
```
main.py          # QApplication, lifecycle, wiring de componentes, shutdown
tray.py          # QSystemTrayIcon, QMenu, acciones del tray, lanzador de Settings
follower.py      # ventana transparente click-through, cursor tracking, movement loop
animation.py      # estado de animación: frames, idle/walk/sleep, direcciones
pokemon.py       # descubrimiento de packs, lectura de JSON, carga de sprites
config.py        # defaults, load/save de config.json, validación básica
config.json      # persistencia local del usuario (no versionar cambios personales)
assets/          # packs y sprites (compartidos entre legado y desktop)
reference/        # código legado de la extensión Chrome (tras la migración; ver más abajo)
```

**Estado actual del repo** (antes de completar la migración):
- `src/content.js` — TODO el runtime de la extensión: cursor tracking, cálculo de target,
  selección de dirección/estado/frame, loop de animación. Es la referencia semántica a portar,
  no código a ejecutar en el desktop.
- `src/manifest.json`, `src/scripts/*` — infraestructura específica de Chrome, no se porta.
- `src/assets/packs/<theme>/<gen>/<NNN-nombre>.json` — un archivo por Pokémon con las hojas de
  sprite, tamaño de frame, fps, frame count y mapeo de fila→dirección por estado
  (`idle`/`walk`/`sleep`). Este formato se conserva sin cambios en el desktop.
- `src/assets/packs/index.json` — índice generado de todos los packs disponibles.
- Cuando se mueva el código JS a `reference/` (pendiente, ver decisión de sesión), los assets
  (`packs/`, `raw/`) deben quedar accesibles desde una ruta común que ambos lados puedan usar
  o compartir hasta que el legado se retire del todo.

**Flujo de datos en el desktop (destino):** `QTimer` (~16ms) → `QCursor.pos()` → actualizar
velocidad/posición → `computeTarget()` → mover follower → `pickDir8FromVector()` +
`pickStateBySpeed()` → `pickRowForState()` → seleccionar frame del spritesheet → redraw de la
ventana transparente.

## Convenciones de código

- Los nombres de las funciones core de movimiento/animación deben conservarse iguales a las del
  original al portarlas, para que el mapeo con `src/content.js` sea directo durante la
  migración: `computeTarget`, `pickDir8FromVector`, `pickRowForState`, `pickStateBySpeed`,
  `walkSpeedFromConfig`, `tick`.
- Los archivos JSON de Pokémon (`assets/packs/**/*.json`) son datos, no código — no hardcodear
  lógica específica de un Pokémon en Python; toda diferencia entre Pokémon debe venir del JSON.
- `config.py` es la única fuente de verdad para leer/escribir `config.json`. Ningún otro módulo
  debe tocar el archivo directamente.
- Un módulo, una responsabilidad: no mezclar lógica de tray (`tray.py`) con lógica de
  movimiento (`follower.py`) ni con carga de assets (`pokemon.py`).

## Reglas arquitectónicas

- No modificar el cursor real de Windows ni instalar drivers/hooks globales de mouse. El
  tracking es por polling con `QCursor.pos()` en un `QTimer`, no un hook del sistema.
- El follower nunca debe bloquear input hacia otras ventanas — la ventana debe ser siempre
  click-through (`WindowTransparentForInput`). Cualquier cambio a `follower.py` que toque flags
  de ventana debe verificar que esto se preserva.
- No añadir servidor, cuenta, telemetría, ni sincronización en la nube. Toda persistencia es
  local vía `config.json`.
- No copiar infraestructura de Chrome (`chrome.storage`, `chrome.runtime`, DOM, popup HTML,
  `requestAnimationFrame`) al puerto Python — solo la semántica de movimiento/animación.
- Mantener el scope de v1 acotado a lo listado en el handoff (§23): sin ataques, emotes,
  multi-follower, packaging/instalador, ni catálogo online. No expandir scope sin confirmarlo
  con el usuario primero.
- El formato JSON por-Pokémon (`assets/packs/**/*.json`) no se reestructura salvo necesidad
  fuerte — el objetivo es "mismos assets + mismos JSON + runtime diferente".

## Workflow de desarrollo

1. Para cualquier cambio de comportamiento (movimiento, dirección, estados), primero revisar
   la función equivalente en `src/content.js` para entender la semántica original antes de
   tocar el código Python.
2. Localizar el módulo responsable (`follower.py` para movimiento/ventana, `animation.py` para
   estados/frames, `pokemon.py` para carga de assets, `tray.py` para UI del tray, `config.py`
   para persistencia) — evitar lógica cruzada entre módulos.
3. Implementar el cambio siguiendo el patrón existente en el módulo.
4. Ejecutar la app manualmente (`python main.py`) y verificar en el escritorio real: no hay
   test suite automatizado por ahora dado que gran parte del comportamiento es visual/de
   integración con Windows (click-through, always-on-top, DPI).
5. Revisar el diff antes de dar por terminado el cambio.

Durante la fase de migración inicial, seguir el orden del vertical slice (handoff §30): un solo
Pokémon, follower click-through, tracking global, idle/walk, 8 direcciones, botón Enabled y
Exit en el tray — antes de expandir a selector de Pokémon, sleep, escala, velocidad, distancia
y persistencia completa.

## Testing

No hay framework de testing configurado todavía. La mayor parte del comportamiento crítico
(ventana transparente, click-through, always-on-top, DPI scaling, multi-monitor) es difícil de
cubrir con unit tests y requiere verificación manual en Windows real:

- Verificar visualmente que el follower sigue el cursor con el suavizado esperado.
- Verificar que no bloquea clicks/drag/scroll sobre otras ventanas.
- Probar con escalado de Windows en 100/125/150/200%.
- Probar con al menos dos monitores, incluyendo coordenadas negativas (monitor a la izquierda).
- Verificar que el tray funciona y que `Exit` cierra realmente el proceso.

Si en el futuro se extraen funciones puras (ej. `computeTarget`, `pickDir8FromVector`), esas sí
son candidatas naturales a unit tests con `pytest` — actualizar esta sección si se añade esa
infraestructura.

## Gotchas y patrones no obvios

- **`flipX: true` en los JSON de Pokémon** (ver `009-blastoise.json`): algunos packs no tienen
  sprites completos para las 8 direcciones y se espera que el renderer voltee horizontalmente
  ciertas filas. Si el spritesheet no cubre `left`/`frontLeft`/`backLeft` explícitamente, no
  asumir que faltan — puede ser intencional y resolverse con flip en runtime.
- **`sleep` con todas las filas en 0**: en el ejemplo de Blastoise, el estado `sleep` mapea
  todas las direcciones a la fila `0` — no es un bug del JSON, es que el sprite de dormir no
  tiene variantes direccionales. No "arreglar" esto añadiendo filas.
- **La dirección visual se deriva de la velocidad del cursor, no de la trayectoria del
  follower** (handoff §12) — es una decisión deliberada del original porque produce una
  orientación más natural. Si el Pokémon parece "mirar mal" al portar el algoritmo, revisar
  primero si se está usando el vector correcto (cursor vs. follower) antes de tocar los
  umbrales de `pickDir8FromVector`.
- **No usar mouse hook global ni fullscreen overlay** — fue evaluado y descartado
  deliberadamente (handoff §2, §14) a favor de polling con `QTimer` + ventana pequeña. Si surge
  la tentación de "arreglar" latencia con un hook global, es un cambio de arquitectura que debe
  discutirse, no una optimización local.
- **Licencia de los sprites**: los assets de `assets/packs/` vienen de PMD Sprite Repository
  bajo CC-BY-NC-SA 4.0 (ver `CREDITS.txt`). Uso personal está bien; cualquier intención de
  distribuir públicamente el proyecto requiere revisar la licencia antes.

## Definition of Done

Antes de dar un cambio por terminado:

- La app arranca sin errores (`python main.py`) y el tray aparece correctamente.
- El comportamiento se verificó manualmente en el escritorio (no solo leyendo el código) —
  especialmente para cambios que tocan `follower.py` (ventana, click-through, always-on-top).
- No se rompió el click-through: se puede interactuar con ventanas debajo del Pokémon.
- El diff se revisó y no incluye scope fuera de lo pedido (ver Reglas arquitectónicas —
  no colar features de la lista de "NO v1" del handoff).
- Si se tocó un archivo JSON de pack, se verificó que sigue siendo JSON válido y que no se
  alteró la semántica de `rows`/`frame`/`fps`/`frames` sin motivo.
- `config.json` de ejemplo/plantilla no contiene datos personales o de sesión que no deban
  versionarse.

No hay hooks/CI configurados que hagan cumplir esto automáticamente — por ahora es disciplina
manual. Si se añade lint/typecheck/test runner, considerar un hook de pre-commit y actualizar
esta sección para reflejar qué se ejecuta obligatoriamente.
