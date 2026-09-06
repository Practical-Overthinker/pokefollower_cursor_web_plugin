# Plan: Multiple Pokémon behavior

> **Execution note:** Implement this plan on `feature/multi-pokemon-chain` in the current worktree. Keep the branch unmerged so the user can load the unpacked `src` folder and test it.

## Goal

Add the approved `Individual` / `Multiple` population mode without changing the existing Follow/Wander controls:

- `Individual + Follow`: the selected Pokémon follows the cursor.
- `Individual + Wander`: the selected Pokémon wanders using the existing behavior.
- `Multiple + Follow`: every occupied slot is active in roster order, forming a spaced line behind the cursor.
- `Multiple + Wander`: every occupied slot wanders independently, with its own roam, idle, and sleep state.
- `Multiple + Follow + Wander`: the roster follows as a line while the cursor is active, then independently wanders after the existing idle threshold and rejoins the line when the cursor moves.

The maximum remains six Pokémon. Empty slots remain inactive. Existing `vcp1_pack` behavior remains available for migration and Individual mode.

## Existing code to reuse

- `src/popup/roster.js` already owns the six-slot roster normalization, selection, addition, replacement, and removal rules.
- `src/popup/popup.js` already persists `vcp1_packs` plus the selected legacy-compatible `vcp1_pack` and renders the slot controls.
- `src/content-mode.js` already owns the pure Follow/Wander decision, safe viewport bounds, random wander targets, wander speed, and sleep eligibility.
- `src/content.js` already owns pack loading, sprite-sheet animation, cursor tracking, speed mapping, and the single-follower wander state machine.
- Do not add a dependency, a new state-management layer, collision detection, drag ordering, per-Pokémon settings, or a new asset schema.

## Data and runtime design

### Popup storage

Add one key:

```text
vcp1_roster_mode: "individual" | "multiple"
```

Default invalid or missing values to `"individual"`. Keep these existing keys unchanged:

```text
vcp1_packs
vcp1_pack
vcp1_enabled
vcp1_wander
vcp1_scale
vcp1_offset
vcp1_lerp
```

The popup mode button is a real accessible button below the Pokéball strip. Its visible label is always `Individual` or `Multiple`, and its accessible name states the current value. Clicking it toggles and persists the new value without closing the popup.

### Content runtime

Replace the single DOM/runtime pair with a small actor collection while preserving the current movement and animation equations:

```js
const STATE = {
  enabled: false,
  wander: false,
  pack: DEFAULT_PACK,
  packs: [DEFAULT_PACK],
  rosterMode: "individual"
};

const POINTER = {
  lastMoveTs: 0,
  lastMouse: { x: 0, y: 0, t: 0 },
  velAvg: { x: 0, y: 0 },
  speedAvg: 0
};

const actors = [
  { packKey, meta, images, element, runtime }
];
```

Each actor runtime keeps its own animation, position, target, facing direction, movement velocity, wander target, phase, idle deadline, sleep deadline, and destination count. Pointer position/velocity remains shared because Follow Mode is a population-level cursor behavior.

`activePackKeys()` returns `[STATE.pack]` in Individual mode and the normalized occupied roster in Multiple mode. Rebuilding the actor collection loads those packs in parallel, creates one fixed follower element per pack, and removes stale elements before the next frame. If a Multiple pack fails to load, skip only that actor; if no pack loads, fall back to the current legacy pack so the extension does not fail silently.

The content script reads `vcp1_packs`, `vcp1_roster_mode`, and `vcp1_pack` on startup and rebuilds the active collection when any of those values changes. Follow/Wander and scale/offset/speed changes keep their existing live behavior.

## Implementation tasks

### 1. Add the popup population-mode control

**Tests first**

Extend `test/popup-roster.test.mjs` with tests that fail before implementation:

- `normalizeRosterMode()` returns `individual` for missing, invalid, and non-string values and preserves `multiple`.
- `toggleRosterMode()` switches both valid values.
- `src/popup/index.html` contains the mode button below `rosterSlots` and styles it as a compact focusable control.
- `src/popup/popup.js` reads/writes `vcp1_roster_mode`, renders the current label, and toggles without touching the selected-slot rules.

**Implementation**

- Add `normalizeRosterMode` and `toggleRosterMode` to `src/popup/roster.js`.
- Add a compact button such as `#rosterModeButton` immediately after `#rosterSlots` inside `.brand-block`, with visible text `Individual` by default.
- Add only the CSS needed for the compact button, visible focus state, and left alignment under the strip. Keep the existing header dimensions and toggle typography intact.
- Import the helpers in `src/popup/popup.js`.
- Track `rosterMode`, render its text/`aria-label`/`aria-pressed` state, read it during startup, and persist it as `vcp1_roster_mode` on click.
- Leave slot selection, editing, removal, and `vcp1_pack` persistence unchanged.

**Verification**

Run:

```bash
node --test test/popup-roster.test.mjs
```

Commit:

```text
feat: add individual multiple roster mode
```

### 2. Add pure behavior helpers for the population matrix

**Tests first**

Extend `test/content-mode.test.mjs` with focused assertions for:

- Multiple + Follow + Wander is following before the existing idle threshold and independent-wander eligible after it.
- Individual mode never enters the Multiple independent-wander branch.
- A trailing target uses the previous actor's movement direction and configured spacing, including a stationary fallback direction.

**Implementation**

Add the smallest testable helpers to `src/content-mode.js`:

- `isIndependentWander({ rosterMode, followMode, wanderMode, lastMoveTs, now, idleDelayMs })` delegates to the existing `shouldFollow` rule and is true only for Multiple + Wander after the cursor-idle threshold.
- `getTrailingTarget({ previousPosition, previousTarget, spacing, fallbackDirection })` returns a point behind the previous actor by `spacing` pixels, normalizing the direction and using the fallback when the previous actor is stationary.

Expose both through `globalThis.__vcp1Mode` and keep the existing helper behavior unchanged.

**Verification**

Run:

```bash
node --test test/content-mode.test.mjs
```

Commit:

```text
test: specify multiple follower movement rules
```

### 3. Refactor `content.js` to an actor collection without changing Individual mode

**Tests first**

Add source-contract tests before the refactor that require:

- `vcp1_packs` and `vcp1_roster_mode` to be read by the content script.
- The runtime to contain an actor collection rather than only `followerEl`/`RUNTIME` as the active rendering boundary.
- Individual mode to resolve to one actor using the selected `vcp1_pack`.

Run the focused tests and confirm they fail for the current single-follower implementation.

**Implementation**

- Move the current per-follower fields from `RUNTIME` into `createFollowerRuntime()`.
- Move cursor-only fields to `POINTER` and update `onMouseMove`, Follow targeting, and hybrid timing to use it.
- Parameterize the existing wander, animation, row selection, frame application, and target functions with an actor/runtime argument; do not change their thresholds or speed mapping.
- Replace `createFollower`/`removeFollower` with actor-aware DOM creation/removal. Use stable IDs such as `__vcp1_follower_0`, `__vcp1_follower_1`, and so on.
- Keep the current follower position initialization and legacy animation behavior for the one-actor path.
- Add a small `normalizeStoredRoster` local helper in `content.js` rather than importing popup modules into the classic content script. Filter invalid entries and cap at six; fall back to `STATE.pack`.
- Make `start`, `stop`, the local slider poller, `applyFrame`, and the message handler operate over every actor.

**Verification**

Run the full existing suite:

```bash
node --test test/*.test.mjs
```

Then inspect the diff for accidental changes to scale migration, facing preservation, blocked-page logic, and existing pack loading.

Commit:

```text
refactor: support multiple follower runtimes
```

### 4. Implement Multiple + Follow as an ordered line

**Tests first**

Add tests for the pure trailing-target helper and content source contract that require:

- the first actor to remain the cursor-follow leader;
- later actors to derive targets from the prior actor and `CONFIG.offset`/Distance;
- roster order to be the actor order;
- removing a roster entry to reduce the active actor collection on the next rebuild.

**Implementation**

- In the per-frame target calculation, use the existing Follow target for actor 0.
- For actor `i > 0` when the population is following, call `MODE.getTrailingTarget` with actor `i - 1`'s current position and target, the existing `CONFIG.offset` spacing, and the shared pointer velocity as fallback.
- Reset each actor's wander state while the population is in the Follow line so stale wander targets do not pull an actor away from the line.
- Advance actors in roster order and use each prior actor's current target for the next trailing target. This is the intentionally simple O(n) line model; it avoids adding a path buffer while still producing natural ordered following.
- Rebuild actors from the normalized roster whenever `vcp1_packs`, `vcp1_pack`, or `vcp1_roster_mode` changes. Empty slots never become actors.

**Verification**

Run focused and full tests. Add a small deterministic unit check for positions `[100, 70, 40]` when the prior movement direction is right and spacing is 30, proving the line math without requiring a browser.

Commit:

```text
feat: make multiple followers form a follow line
```

### 5. Implement independent Multiple + Wander and the hybrid transition

**Tests first**

Add source/behavior tests that require:

- each actor to call/use its own wander target and phase fields;
- Multiple + Wander to avoid the trailing-target path;
- Multiple + Follow + Wander to switch from line to independent wander after the existing idle threshold;
- a pointer movement to reset all actor wander states so they can rejoin the line;
- Follow/Wander Off to remove all actor elements.

**Implementation**

- For Multiple + Wander, run the existing wander state machine separately for each actor runtime. Keep `WANDER_IDLE_*`, `WANDER_SLEEP_*`, safe bounds, sleep chance, nearby target distance, and popup speed mapping unchanged.
- Use the shared population-level `MODE.shouldFollow` decision. If it returns false while Wander is enabled, every actor computes its own wander target and animation state; do not reuse actor 0's target or timing.
- In `onMouseMove`, reset wander state for every actor when Wander is enabled. The next frame therefore rebuilds the ordered line for hybrid mode.
- When the pointer becomes active again, clear each actor's wander state and set its target through the line calculation. Preserve each actor's current position so rejoining is smooth rather than teleporting.
- Keep Individual + Follow/Wander behavior routed through the same existing branches with only one actor, so the old mode matrix remains unchanged.
- Handle async pack rebuilds with a simple generation/token guard so a slower old roster load cannot replace a newer one. Do not add a general task queue.

**Verification**

Run:

```bash
node --test test/*.test.mjs
npm run build:index
git status --short
```

Confirm `build:index` does not modify source assets or generated files unexpectedly.

Commit:

```text
feat: add independent multiple wander behavior
```

### 6. Final review and user handoff

- Run the full test suite again.
- Inspect `git diff main...HEAD --stat` and the focused runtime diff for unnecessary files or behavior changes.
- Keep the worktree on `feature/multi-pokemon-chain`; do not merge or push.
- Tell the user to reload the unpacked extension from:

  ```text
  /Users/alihamad/Desktop/me/Digital Body/Projects/PokéFollower/app/.worktrees/multi-pokemon-chain/src
  ```

- Explain that manual Chrome behavior is the remaining user-side verification: test Individual/Multiple, both Follow/Wander combinations, slot removal, refresh persistence, and a six-Pokémon roster.

## Verification matrix

| Case | Expected result |
| --- | --- |
| Individual, both toggles off | No actor element |
| Individual + Follow | One selected Pokémon follows as before |
| Individual + Wander | One selected Pokémon roams, idles, and sleeps as before |
| Multiple + Follow | One actor per occupied slot, ordered line, Distance spacing |
| Multiple + Wander | One actor per occupied slot, independent targets/phases |
| Multiple + Follow + Wander | Line while cursor active, independent wander while idle, line rejoin on movement |
| Empty slots | Never rendered or animated |
| Remove selected extra slot | Roster compacts and active actor order compacts |
| Switch an occupied slot | Edits that slot without hiding other Multiple actors |
| Browser refresh | Content actor 0 matches the persisted active configuration |

