# PokéFollower Desktop

**A tiny retro Pokémon companion that follows your cursor across Windows.**

A pixel-art Pokémon walks around your desktop, chasing the mouse pointer with smooth
8-direction movement and idle / walk / sleep animations — not trapped inside a browser tab,
but on top of everything, system-wide. It lives in the System Tray, has no main window, and
never touches your real Windows cursor: the Pokémon is its own transparent, click-through
window, so it never blocks clicks, drags or scrolling on the apps underneath.

> [!NOTE]
> **Public beta (`v0.1.0-beta.1`).** It works and it's usable, but it's early — see
> [Beta status & known limitations](#beta-status--known-limitations).

<!-- VISUALS: see docs/README.md for the exact captures still needed. Drop them in docs/
     and uncomment:
![PokéFollower following the cursor](docs/demo.gif)
-->

## What it does

- Follows your cursor anywhere on the Windows desktop, above other windows.
- Idle, walk and sleep animations, with 8 directional facings.
- 493 Pokémon to choose from (Gen 1–5), with a searchable picker.
- Adjustable size, follow speed and follow distance — changes apply live.
- Configurable "sleep" after a period of no mouse movement.
- Lightweight, tray-first: no main window, no browser, no account, no telemetry.
- Optional "start with Windows" (offered by the installer).
- Your settings persist locally between runs.

## Installation

1. Go to [**Releases**](../../releases) and download
   `PokeFollower-Setup-0.1.0-beta.1.exe`.
2. Run it and follow the wizard. **No administrator rights required** — it installs just for
   your user.
3. The beta is **not code-signed**, so Windows SmartScreen may show a blue
   *"Windows protected your PC / Unknown publisher"* dialog. Click **More info → Run anyway**.
   This is expected for a personal project without a paid signing certificate; the installer
   is the same file listed on the Releases page, and its SHA-256 is published alongside it.
4. When setup finishes, PokéFollower starts straight into the System Tray (near the clock —
   it may be under the hidden-icons caret `^`). A tray notification confirms it's running.

### Verifying the download (optional)

Each release includes `SHA256SUMS.txt`. To check the installer matches:

```powershell
Get-FileHash .\PokeFollower-Setup-0.1.0-beta.1.exe -Algorithm SHA256
```

Compare the printed hash with the one in `SHA256SUMS.txt`.

## Usage

Right-click the tray icon for:

- **Enabled** — turn the follower on or off (it stays in the tray either way).
- **Choose Pokémon…** — pick from all 493, with name search and thumbnails.
- **Settings…** — adjust scale, follow speed, follow distance and sleep behaviour.
- **Exit** — quit the app completely.

If you ticked **"Start PokéFollower automatically with Windows"** during setup, it launches on
sign-in. Only one copy ever runs at a time — launching it again (Start Menu, shortcut, Startup)
detects the running instance and exits silently.

## Settings

| Setting | What it does |
| --- | --- |
| **Scale** | Sprite size (0.5×–3×). |
| **Follow Speed** | How quickly the Pokémon catches up to the cursor. |
| **Distance** | How far behind / above the cursor it trails (0–100 px). |
| **Sleep enabled** | Whether it lies down after the mouse is idle. |
| **Sleep after** | Idle time before sleeping (5–300 s). |

Changes take effect immediately and are saved to `%APPDATA%\PokeFollower\config.json`.

## System requirements

- **Windows 10 or 11, 64-bit.** (Built and tested on Windows 10 x64.)
- No Python or other runtime needed — the installer bundles everything.
- Tested at 100% display scaling; 125/150/200% is not yet verified.

## Beta status & known limitations

This is the first public beta. Expect rough edges, and please report anything odd via
[Issues](../../issues).

- **Unsigned installer** — SmartScreen "Unknown publisher" warning (see Installation).
- **Windows only**, 64-bit.
- **No automatic updater** — new versions are installed by downloading a newer installer.
- **Exclusive-fullscreen apps** (some games/video players) render above every normal window,
  so the Pokémon won't be visible over them.
- **Secure desktop** (UAC prompts, the lock screen, Ctrl+Alt+Del) never shows normal app
  overlays, so the Pokémon disappears there by design.
- **High-DPI**: validated at 100% scaling only.

## Development (run from source)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Requirements: Windows, Python 3.11+ (3.12 is the build target), PySide6 (Qt 6).

Run the regression tests:

```bash
pip install -r requirements-dev.txt
pytest
```

Diagnose the sprite catalogue (loads all 493 packs, reports any failure):

```bash
python check_packs.py
```

### Building the installer

Requires `requirements-dev.txt` (PyInstaller, Pillow) and
[Inno Setup](https://jrsoftware.org/isdl.php):

```bash
pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File tools\build.ps1
```

This regenerates the icon, builds the PyInstaller onedir bundle, runs the frozen
`PokeFollower.exe --self-check` gate, compiles the Inno Setup installer, and writes
`SHA256SUMS.txt`. Output: `installer/Output/PokeFollower-Setup-0.1.0-beta.1.exe`. See
[`CLAUDE.md`](CLAUDE.md) for what each step does and the project architecture.

## Credits & licensing

PokéFollower Desktop is an **unofficial, non-commercial fan project** — a system-wide
reimagining of the Chrome extension
[PokéFollower](https://github.com/ThinkrDoer/pokefollower_cursor_web_plugin) by **Ali Hamad**
(ThinkrDoer). It reuses that project's sprite assets, per-Pokémon data format and movement
logic; the original extension source is kept unmodified under [`reference/`](reference/).

- **Code & design** — MIT License, © 2025 Ali Hamad and contributors.
- **Pokémon sprites** — from the [PMD Sprite Repository](https://sprites.pmdcollab.org),
  © their individual contributors, used under
  [CC-BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) (NonCommercial +
  ShareAlike). Because the installer redistributes these sprites, the whole project is
  **non-commercial**.
- Reference/popup images from [Pokémon Database](https://pokemondb.net).
- Pokémon and character names are trademarks of Nintendo / Game Freak / Creatures Inc. This
  project is not affiliated with or endorsed by them.

See [`LICENSE.txt`](LICENSE.txt) and [`CREDITS.txt`](CREDITS.txt) for the full text.
