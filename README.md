# PokéFollower Desktop

Una app personal para Windows que trae un poco de alegría nostálgica al escritorio: un sprite
retro 2D de Pokémon que sigue tu cursor por toda la pantalla, no solo dentro del navegador.

---

## Qué es

PokéFollower Desktop es un fork conceptual, para uso personal y sin fines comerciales, de la
extensión de Chrome [PokéFollower](https://github.com/ThinkrDoer/pokefollower_cursor_web_plugin)
creada originalmente por **Ali Hamad**. En vez de vivir dentro de una pestaña del navegador,
corre a nivel de todo el sistema: un Pokémon animado sigue el cursor globalmente, en una
ventana transparente y click-through que no bloquea ni interfiere con ninguna otra aplicación.

No modifica el cursor real de Windows — el Pokémon es un objeto visual independiente.

## Instalación (usuario final, sin Python)

1. Descarga `PokeFollower-Setup-0.1.0-beta.1.exe` (ver [Releases](../../releases) o pídele el
   archivo a quien te lo compartió).
2. Ejecútalo y sigue el asistente. No requiere permisos de administrador.
3. Windows puede mostrar una advertencia de "Editor desconocido" (SmartScreen) — es normal en
   apps personales sin firma de código pagada. Clic en "Más información" → "Ejecutar de
   todas formas".
4. Al terminar, PokéFollower arranca directo al System Tray (junto al reloj, puede estar en
   los íconos ocultos ^). Verás un aviso confirmando que está corriendo.

Clic derecho en el ícono del tray para:

- **Enabled** — activar/desactivar el follower.
- **Choose Pokémon...** — elegir entre los 493 Pokémon disponibles (búsqueda + miniaturas).
- **Settings...** — ajustar escala, velocidad de seguimiento, distancia y comportamiento de
  `sleep`, todo con efecto en vivo.
- **Exit** — cerrar la app.

Para desinstalar: Configuración de Windows → Aplicaciones → PokéFollower → Desinstalar (tus
preferencias en `%APPDATA%\PokeFollower` se conservan por si reinstalas).

## Desarrollo (correr desde el código fuente)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Requisitos: Windows, Python 3.11+, PySide6 (Qt 6).

## Reconstruir el instalador

Requiere además `requirements-dev.txt` (PyInstaller, Pillow) e
[Inno Setup](https://jrsoftware.org/isdl.php) instalado:

```bash
pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

Genera `installer/Output/PokeFollower-Setup-0.1.0-beta.1.exe`. Ver [`CLAUDE.md`](CLAUDE.md) para el
detalle de qué hace cada paso del pipeline.

## Créditos

Este proyecto reutiliza los assets, el formato de datos por Pokémon y la lógica de movimiento
diseñados originalmente para
[pokefollower_cursor_web_plugin](https://github.com/ThinkrDoer/pokefollower_cursor_web_plugin)
por **Ali Hamad** (ThinkrDoer). El código fuente original de la extensión Chrome se conserva
intacto en [`reference/`](reference/) como referencia.

Ver [`CREDITS.txt`](CREDITS.txt) para la atribución completa de los sprites (PMD Sprite
Repository, CC-BY-NC-SA 4.0) y de Pokémon Database.

## Documentación técnica

Ver [`CLAUDE.md`](CLAUDE.md) para arquitectura, convenciones y guía de desarrollo.
