# PokeFollower Chrome Extension — AI Agent Context

## What This Project Is
A Chrome extension where an animated Pokemon follows the user's cursor.
New generations unlock at install milestones.
When asked to add Pokemon, always ask which generation if not specified.

## How To Add New Pokemon (Full Workflow)

When asked to add a batch of Pokemon, do the following IN ORDER:

### Step 1 — Download source files in a browser
For EACH Pokemon in the batch:

1. Go to: https://pokemondb.net/sprites/{name}
   - Find the "Generation V" section (always use Gen V sprites regardless of which generation you are adding)
   - Find the first sprite under "Normal" column (not Shiny)
   - Right-click and save as: {dex}-{name}.png
   - Save to: /Users/alihamad/Desktop/me/Digital Body/Projects/PokéFollower/Pokemon/incoming/

2. Go to: https://sprites.pmdcollab.org/#{dex4}
   (where {dex4} = dex number zero-padded to 4 digits, e.g. 0337)
   - Scroll past Portraits to the "Sprites" section
   - Click "Download all sprites" blue link
   - Rename downloaded file from sprites.zip to: {dex}-{name} sprite.zip
   - Move to: /Users/alihamad/Desktop/me/Digital Body/Projects/PokéFollower/Pokemon/incoming/

Confirm both files are in incoming/ before proceeding.

### Step 2 — Run the Python script
```bash
python3 add_pokemon.py --gen {X} --batch "{dex}-{name} {dex}-{name} ..."
```

Example:
```bash
python3 add_pokemon.py --gen 4 --batch "387-turtwig 388-grotle 389-torterra"
```

Dry run (no files moved, just shows what would happen):
```bash
python3 add_pokemon.py --gen 4 --batch "387-turtwig" --dry-run
```

---

## Key Paths

| What | Path |
|---|---|
| VS Code project root | /Users/alihamad/Desktop/me/Digital Body/Projects/PokéFollower/app/ |
| Raw sprites (VS Code) | src/assets/raw/gen-{X}/{dex}-{name}/ |
| Cover PNGs (VS Code) | src/assets/ui/gen-{X}/ |
| Pack JSONs (VS Code) | src/assets/packs/retro/gen-{X}/ |
| Incoming folder | /Users/alihamad/Desktop/me/Digital Body/Projects/PokéFollower/Pokemon/incoming/ |
| Processed archive | /Users/alihamad/Desktop/me/Digital Body/Projects/PokéFollower/Pokemon/processed/ |

---

## Naming Conventions
- VS Code gen folders: gen-3, gen-4 (lowercase, hyphen)
- PROJECTS gen folders: Gen 3, Gen 4 (capital G, space)
- Pokemon folder: {dex}-{name} e.g. 337-lunatone
- Sprite archive folder: {dex}-{name} sprite e.g. 337-lunatone sprite
- Cover PNG filename: {dex}-{name}.png e.g. 337-lunatone.png
- Sprite zip filename: {dex}-{name} sprite.zip e.g. 337-lunatone sprite.zip
- Zero-padded dex for PMD URL: 4 digits e.g. 0337

---

## What The Script Does
1. Finds cover PNG and sprite zip in incoming/
2. Extracts ALL zip contents to sprite archive folder
3. Applies fallbacks if Idle-Anim or Sleep-Anim missing (uses Walk-Anim)
4. Converts Idle-Anim, Sleep-Anim, Walk-Anim PNG -> WebP (lossless)
5. Archives everything to PROJECTS/processed/Gen X/{dex}-{name} sprite/
6. Creates in use/ subfolder with the 5 deployed files
7. Copies files to VS Code project
8. Runs parse-anim.js per Pokemon to generate JSON
9. Runs npm run build:index once at end
10. Cleans up incoming/

---

## Versioning
- Single source of truth: `package.json`'s `"version"`.
- Convention: major version = number of fully completed generations (1.0 → Gen 1 done, 2.0 → Gen 2 done, 3.0 → Gen 3 done, 4.0 → Gen 4 done). QoL/bugfix work done alongside a generation rides along in that same major bump unless it's significant enough to warrant its own minor bump.
- To bump: edit `package.json`'s `"version"`, then run:
```bash
npm run sync-version
```
This propagates the version into `src/manifest.json` (`"version"`, the actual extension version) and the popup brand label in `src/popup/index.html` (trims a trailing `.0` patch for display, e.g. "4.0.0" -> "v4.0").

---

## Adding A New Generation
Before running the script for a new gen for the first time, create these folders:
```bash
mkdir -p "src/assets/raw/gen-{X}"
mkdir -p "src/assets/ui/gen-{X}"
mkdir -p "src/assets/packs/retro/gen-{X}"
mkdir -p "/Users/alihamad/Desktop/me/Digital Body/Projects/PokéFollower/Pokemon/processed/Gen {X}"
```
Then use --gen {X} in the script command.

---

## Sprite Fallback Logic
- Idle-Anim.png missing -> use Walk-Anim.png as substitute
- Sleep-Anim.png missing -> use Idle-Anim.png as substitute
- Walk-Anim.png missing -> error, except #618 Stunfisk and #683 Aromatisse (reuse Idle-Anim.png)
- AnimData.xml missing -> error (always required)

---

## Source URLs
- Cover PNGs: https://pokemondb.net/sprites/{name} (always Gen V Normal)
- Sprite zips: https://spriteserver.pmdcollab.org/assets/{dex4}/sprites.zip

---

## Full Documentation
https://www.notion.so/34641183ac9c81db8547e332e0870799
