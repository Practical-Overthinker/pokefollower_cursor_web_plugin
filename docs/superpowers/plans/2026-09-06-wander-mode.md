# Wander Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add independent Follow Mode and Wander Mode toggles while preserving the existing cursor-following behavior.

**Architecture:** Keep one follower element and one animation loop. Add a small classic-script movement helper, loaded before `content.js`, for mode decisions and viewport-safe random targets; keep runtime state and movement integration in the existing content script. Persist the two mode settings independently through the existing popup and `chrome.storage.sync` flow.

**Tech Stack:** Chrome Manifest V3 content script, vanilla JavaScript, HTML/CSS popup, Node's built-in `node:test` and `vm` modules.

## Global Constraints

- Existing `vcp1_enabled` remains the stored value for Follow Mode and existing installations retain its state.
- New `vcp1_wander` defaults to `false`.
- A follower is active when `followMode || wanderMode`.
- Follow Mode has priority while the pointer moves; with both modes enabled, Wander Mode begins after `3000` ms of pointer inactivity.
- Wander targets stay inside a conservative viewport-safe rectangle based on the scaled sprite dimensions.
- Use the existing walk speed setting; add no timer controls, collision detection, new assets, or pack schema changes.
- Keep both toggles accessible and use the exact labels `Follow Mode` and `Wander Mode`.

---

### Task 1: Add tested mode and wander-target primitives

**Files:**
- Create: `test/content-mode.test.mjs`
- Create: `src/content-mode.js`
- Modify: `src/manifest.json` (`content_scripts[0].js` order)

**Interfaces:**
- Produces `globalThis.__vcp1Mode` with `IDLE_DELAY_MS`, `isActive(followMode, wanderMode)`, `shouldFollow({ followMode, wanderMode, lastMoveTs, now, idleDelayMs })`, `getWanderBounds({ viewportWidth, viewportHeight, spriteWidth, spriteHeight, scale, edgeMargin })`, `isWithinBounds(point, bounds)`, and `pickWanderTarget(bounds, currentTarget, random)`.
- `content.js` consumes these functions through the global object; the helper remains a classic script because Manifest V3 content scripts are not loaded as ES modules.

- [ ] **Step 1: Write the failing helper tests**

Create `test/content-mode.test.mjs` with a small `vm` loader for the classic content helper and these focused cases:

```js
import fs from "node:fs";
import vm from "node:vm";
import test from "node:test";
import assert from "node:assert/strict";

function loadMode() {
  const source = fs.readFileSync(
    new URL("../src/content-mode.js", import.meta.url),
    "utf8"
  );
  const context = {};
  vm.runInNewContext(source, context);
  return context.__vcp1Mode;
}

const mode = loadMode();

test("spawns when either mode is enabled", () => {
  assert.equal(mode.isActive(false, false), false);
  assert.equal(mode.isActive(true, false), true);
  assert.equal(mode.isActive(false, true), true);
  assert.equal(mode.isActive(true, true), true);
});

test("hybrid mode follows briefly, then wanders after pointer idle", () => {
  assert.equal(mode.shouldFollow({ followMode: true, wanderMode: false, lastMoveTs: 0, now: 999999 }), true);
  assert.equal(mode.shouldFollow({ followMode: false, wanderMode: true, lastMoveTs: 0, now: 999999 }), false);
  assert.equal(mode.shouldFollow({ followMode: true, wanderMode: true, lastMoveTs: 1000, now: 3999 }), true);
  assert.equal(mode.shouldFollow({ followMode: true, wanderMode: true, lastMoveTs: 1000, now: 4000 }), false);
});

test("wander targets stay inside the scaled viewport-safe bounds", () => {
  const bounds = mode.getWanderBounds({
    viewportWidth: 800,
    viewportHeight: 600,
    spriteWidth: 100,
    spriteHeight: 80,
    scale: 1.25,
    edgeMargin: 12
  });
  const target = mode.pickWanderTarget(bounds, null, () => 0.5);
  assert.equal(mode.isWithinBounds(target, bounds), true);
  assert.ok(target.x >= 74.5 && target.x <= 725.5);
  assert.ok(target.y >= 62 && target.y <= 538);
});

test("a new wander target is not the previous target when alternatives exist", () => {
  const bounds = mode.getWanderBounds({
    viewportWidth: 400,
    viewportHeight: 300,
    spriteWidth: 40,
    spriteHeight: 40,
    scale: 1,
    edgeMargin: 8
  });
  const first = mode.pickWanderTarget(bounds, null, () => 0);
  const next = mode.pickWanderTarget(bounds, first, () => 0);
  assert.notDeepEqual(next, first);
  assert.equal(mode.isWithinBounds(next, bounds), true);
});
```

- [ ] **Step 2: Run the helper tests and confirm the expected red failure**

Run:

```bash
node --test test/content-mode.test.mjs
```

Expected: the test file fails because `src/content-mode.js` does not yet define `__vcp1Mode`.

- [ ] **Step 3: Implement the minimal classic helper and load it before the content script**

Create `src/content-mode.js` with the five functions above. Clamp invalid viewport or sprite dimensions to non-negative values, compute insets as `min(viewport / 2, scaledSprite / 2 + edgeMargin)`, and generate random coordinates within the returned bounds. If a generated point exactly equals `currentTarget`, move it to the opposite edge on the first axis with room, then the second axis.

Change the manifest content script list to:

```json
"js": ["content-mode.js", "content.js"]
```

- [ ] **Step 4: Run the focused tests and the existing page-check tests**

Run:

```bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
```

Expected: all seven tests pass.

- [ ] **Step 5: Commit the tested primitives**

```bash
git add src/content-mode.js src/manifest.json test/content-mode.test.mjs
git commit -m "feat: add wander mode movement primitives"
```

### Task 2: Integrate autonomous movement into the content script

**Files:**
- Modify: `src/content.js` (mode state, target selection, movement loop, storage listeners)

**Interfaces:**
- Consumes `globalThis.__vcp1Mode` from Task 1.
- Keeps the existing `computeFollowTarget`, animation, pack loading, speed, scale, offset, and follower element paths intact.

- [ ] **Step 1: Add runtime state and the failing integration assertions**

Extend the helper test with the already-covered `isActive` and `shouldFollow` cases as the integration contract, then run the focused tests before changing `content.js`:

```bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
```

The helper tests must remain green before touching the runtime integration.

- [ ] **Step 2: Add the smallest runtime state needed for wander mode**

In `src/content.js`:

```js
const MODE = globalThis.__vcp1Mode;

const STATE = {
  enabled: false,
  wander: false,
  pack: DEFAULT_PACK,
  facingLeft: false
};
```

Add `wanderTarget`, `wanderPauseUntil`, `isWandering`, and `moveVel` to `RUNTIME`. Add constants for the three-second hybrid delay, a short pause range, and a 12 px edge margin.

- [ ] **Step 3: Split follow and wander target selection**

Rename the existing `computeTarget()` to `computeFollowTarget()` without changing its body. Add `currentWanderBounds()`, `resetWanderState()`, `chooseWanderTarget()`, and `computeWanderTarget(now)`:

```js
function computeTarget(now) {
  const following = MODE.shouldFollow({
    followMode: STATE.enabled,
    wanderMode: STATE.wander,
    lastMoveTs: RUNTIME.lastMoveTs,
    now
  });
  RUNTIME.isWandering = STATE.wander && !following;
  if (following) {
    resetWanderState();
    computeFollowTarget();
  } else {
    computeWanderTarget(now);
  }
}
```

`computeWanderTarget` must recalculate bounds from `innerWidth`, `innerHeight`, the current idle frame dimensions, `CONFIG.scale`, and the edge margin on every target decision. If a resize puts the current target outside those bounds, discard it and choose a new target. On arrival, hold the target for a random 500–1000 ms pause before choosing another.

- [ ] **Step 4: Reuse the existing movement and animation path**

In `tick(dtMs)`, call `computeTarget(performance.now())` before the existing distance calculation. Keep the existing `walkSpeedFromConfig()` and frame-time clamp. Set `RUNTIME.moveVel` from the actual wander travel direction while `RUNTIME.isWandering`; keep the existing `RUNTIME.velAvg` direction for Follow Mode. Reset `moveVel` when a wander target is reached so the idle frame does not imply continued travel.

Use `RUNTIME.isWandering ? RUNTIME.moveVel : RUNTIME.velAvg` in `pickRowForState()` so autonomous movement faces the direction it is actually walking.

- [ ] **Step 5: Change the spawn and storage conditions**

Update `applyState()` to use `MODE.isActive(STATE.enabled, STATE.wander)`. Read and react to `vcp1_wander` alongside `vcp1_enabled` in `chrome.storage.sync`. Keep `vcp1_enabled` as the Follow Mode value and default missing `vcp1_wander` to `false`. When the pointer moves in hybrid mode, clear the current wander target and pause so the next frame immediately uses the cursor target.

- [ ] **Step 6: Run syntax, focused tests, and index/build checks**

Run:

```bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
node --check src/content-mode.js
node --check src/content.js
python3 -m json.tool src/manifest.json >/dev/null
npm run build:index
git diff --check
```

Expected: all tests pass, both JavaScript checks exit 0, the manifest parses, the index still reports 711 entries, and `git diff --check` is clean.

- [ ] **Step 7: Commit the runtime integration**

```bash
git add src/content.js
git commit -m "feat: integrate follower wander behavior"
```

### Task 3: Add the two popup controls

**Files:**
- Modify: `src/popup/index.html` (mode toggle markup and shared toggle styles)
- Modify: `src/popup/popup.js` (storage load and independent saves)

**Interfaces:**
- Uses `vcp1_enabled` for Follow Mode and `vcp1_wander` for Wander Mode.
- Keeps the existing Follow Mode save-and-close behavior and gives the new toggle the same immediate save behavior.

- [ ] **Step 1: Add accessible toggle markup**

Replace the single header label with a grouped pair:

```html
<div class="mode-toggles" role="group" aria-label="Follower modes">
  <label class="mode-toggle" for="enabled">
    <span>Follow Mode</span>
    <input id="enabled" type="checkbox" />
  </label>
  <label class="mode-toggle" for="wander">
    <span>Wander Mode</span>
    <input id="wander" type="checkbox" />
  </label>
</div>
```

Reuse the existing Pokéball switch styling through a shared `.mode-toggle input` selector; preserve visible focus outlines and keep both labels readable in the existing popup width.

- [ ] **Step 2: Load and persist both settings**

Add `const wanderEl = document.getElementById("wander")`, include `vcp1_wander` in the sync read, set `wanderEl.checked`, and add:

```js
wanderEl.addEventListener("change", () => {
  save({ vcp1_wander: wanderEl.checked });
  window.close();
});
```

Leave the existing `vcp1_enabled` key and handler intact apart from the label rename.

- [ ] **Step 3: Run static verification**

Run:

```bash
node --check src/popup/popup.js
node --check src/popup/page-check.js
git diff --check
```

- [ ] **Step 4: Commit the popup controls**

```bash
git add src/popup/index.html src/popup/popup.js
git commit -m "feat: add follow and wander mode toggles"
```

### Task 4: Verify the branch and manually test Chrome behavior

**Files:**
- Modify: none unless verification exposes a defect.

- [ ] **Step 1: Run the complete automated check set**

```bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
node --check src/content-mode.js
node --check src/content.js
node --check src/popup/popup.js
node --check src/popup/page-check.js
python3 -m json.tool src/manifest.json >/dev/null
npm run build:index
git diff --check
git status --short --branch
```

- [ ] **Step 2: Manually verify the four toggle states in Chrome**

Reload the unpacked extension on a normal webpage and verify:

1. Both off hides the Pokémon.
2. Follow Mode only preserves cursor following.
3. Wander Mode only spawns the Pokémon and walks it around the visible viewport.
4. Both on follows the cursor while it moves, switches to wandering after roughly three seconds of inactivity, and immediately returns to the cursor when the pointer moves.

Also resize the viewport, switch Pokémon, disable both modes, and reopen the popup to confirm each setting persists independently.

- [ ] **Step 3: Commit any only-if-needed verification fix and report the branch state**

```bash
git status --short --branch
git log --oneline -4
```

Report the feature branch and the manual verification result before opening or merging a pull request.
