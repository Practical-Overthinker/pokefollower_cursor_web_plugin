# Multi-Pokémon Switcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a six-slot Pokémon roster to the popup, with unambiguous selection and a small red remove control above selected extra slots, while keeping the active runtime as a single switchable follower.

**Architecture:** Extract roster mutation and migration rules into a small pure ES module. The popup owns the DOM and persists the roster as `vcp1_packs`; it continues mirroring the selected pack to the existing `vcp1_pack` key so the current content script remains the single-follower runtime. The six-slot UI is independent of future chain rendering.

**Tech Stack:** Chrome Manifest V3 popup, vanilla HTML/CSS/JavaScript, `chrome.storage.sync`, Node's built-in `node:test` runner.

## Global Constraints

- Show six circular slots beneath the `PokeFollower v5.0` label.
- Occupied slots select Pokémon; clicking an occupied slot never removes it.
- Slots 2–6 remove only through a very small red circular control with black outline and black `×` above the selected Pokéball.
- Slot 1 cannot be removed.
- Keep occupied slots contiguous and shift later Pokémon left after removal.
- Use Bulbasaur as the predictable starting Pokémon for a newly opened slot.
- Persist the roster in `chrome.storage.sync` and migrate existing `vcp1_pack` installations.
- Keep this slice in switcher mode only; do not add chain rendering or a chain toggle.
- Keep scale, distance, and speed global.
- Do not add dependencies.

---

### Task 1: Add tested roster state primitives

**Files:**
- Create: `src/popup/roster.js`
- Create: `test/popup-roster.test.mjs`

**Interfaces:**
- `MAX_ROSTER_SIZE`: number `6`.
- `normalizeRoster(rawRoster, fallbackPack)`: returns a non-empty array of at most six non-empty string pack IDs.
- `addRosterSlot(roster, pack)`: returns a new array with `pack` appended, or the original roster when already full.
- `setRosterPack(roster, index, pack)`: returns a new array with one valid entry replaced, or the original roster for an invalid request.
- `removeRosterSlot(roster, index)`: returns a new compacted array for indexes 1–5, or the original roster for slot 0/invalid indexes.
- `selectedIndexAfterRemoval(index)`: returns `Math.max(0, index - 1)`.

- [ ] **Step 1: Write the failing tests**

```js
import test from "node:test";
import assert from "node:assert/strict";
import {
  MAX_ROSTER_SIZE,
  addRosterSlot,
  normalizeRoster,
  removeRosterSlot,
  selectedIndexAfterRemoval,
  setRosterPack
} from "../src/popup/roster.js";

const BULBASAUR = "retro/gen-1/001-bulbasaur";
const CHARMANDER = "retro/gen-1/004-charmander";
const SQUIRTLE = "retro/gen-1/007-squirtle";

test("legacy single-pack storage migrates to one roster entry", () => {
  assert.deepEqual(normalizeRoster(undefined, BULBASAUR), [BULBASAUR]);
  assert.deepEqual(normalizeRoster([CHARMANDER], BULBASAUR), [CHARMANDER]);
});

test("roster normalization removes invalid entries and caps six slots", () => {
  const raw = ["", CHARMANDER, null, SQUIRTLE, ...Array(8).fill(BULBASAUR)];
  const roster = normalizeRoster(raw, BULBASAUR);
  assert.equal(roster.length, MAX_ROSTER_SIZE);
  assert.deepEqual(roster, [CHARMANDER, SQUIRTLE, BULBASAUR, BULBASAUR, BULBASAUR, BULBASAUR]);
});

test("adding a slot is capped at six entries", () => {
  assert.deepEqual(addRosterSlot([BULBASAUR], CHARMANDER), [BULBASAUR, CHARMANDER]);
  const full = Array(MAX_ROSTER_SIZE).fill(BULBASAUR);
  assert.strictEqual(addRosterSlot(full, CHARMANDER), full);
});

test("updating a slot leaves the other entries unchanged", () => {
  assert.deepEqual(
    setRosterPack([BULBASAUR, CHARMANDER], 1, SQUIRTLE),
    [BULBASAUR, SQUIRTLE]
  );
});

test("removing an extra slot compacts the roster but slot one is protected", () => {
  const roster = [BULBASAUR, CHARMANDER, SQUIRTLE];
  assert.deepEqual(removeRosterSlot(roster, 1), [BULBASAUR, SQUIRTLE]);
  assert.strictEqual(removeRosterSlot(roster, 0), roster);
  assert.equal(selectedIndexAfterRemoval(2), 1);
  assert.equal(selectedIndexAfterRemoval(1), 0);
});
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `node --test test/popup-roster.test.mjs`

Expected: FAIL because `src/popup/roster.js` does not exist yet.

- [ ] **Step 3: Implement the minimal roster module**

Implement the five named exports using array copies for valid mutations. Treat only non-empty strings as pack IDs, return `[fallbackPack]` when no valid entries remain, and never allow `removeRosterSlot` to remove index `0`.

- [ ] **Step 4: Run the focused test to verify it passes**

Run: `node --test test/popup-roster.test.mjs`

Expected: PASS with all roster tests green.

- [ ] **Step 5: Commit**

```bash
git add src/popup/roster.js test/popup-roster.test.mjs
git commit -m "feat: add multi-pokemon roster primitives"
```

### Task 2: Add the six-slot popup markup and visual treatment

**Files:**
- Modify: `src/popup/index.html`
- Modify: `test/popup-roster.test.mjs`

**Interfaces:**
- Produces an empty `#rosterSlots` container inside the left-side brand block for the popup controller to render.
- Produces `.slot-item`, `.slot-select`, `.slot-remove`, and `.slot-select.empty` styles.

- [ ] **Step 1: Add failing popup contract assertions**

Append tests that read `src/popup/index.html` and assert:

```js
const html = fs.readFileSync(new URL("../src/popup/index.html", import.meta.url), "utf8");
assert.match(html, /class="brand-block"/);
assert.match(html, /id="rosterSlots"/);
assert.match(html, /<script type="module" src="popup\.js"><\/script>/);
assert.match(html, /\.slot-remove\s*\{[^}]*position:\s*absolute/s);
assert.match(html, /\.slot-remove\s*\{[^}]*background:\s*#ef4036/s);
assert.match(html, /\.slot-remove\s*\{[^}]*border[^}]*#000/s);
```

- [ ] **Step 2: Run the popup contract test to verify it fails**

Run: `node --test test/popup-roster.test.mjs`

Expected: FAIL because the brand block, slot styles, and module popup script are not present.

- [ ] **Step 3: Add the minimal markup and CSS**

Wrap the existing brand in `.brand-block`, add:

```html
<div id="rosterSlots" class="roster-slots" role="group" aria-label="Pokémon slots"></div>
```

below the brand, and change the popup controller script tag to `type="module"`. Keep the mode toggles in the existing right-side column.

Add compact CSS that:

- lays out six `.slot-item` elements in one row;
- positions `.slot-remove` absolutely above its slot;
- uses `#ef4036` for the remove circle, a black outline, and a black `×`;
- keeps the remove badge smaller than the Pokéball icon;
- renders empty slots as black circles;
- gives selected slots a clear focus/highlight treatment;
- preserves the popup's existing compact dimensions and keyboard focus outlines.

- [ ] **Step 4: Run the popup contract test to verify it passes**

Run: `node --test test/popup-roster.test.mjs`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/popup/index.html test/popup-roster.test.mjs
git commit -m "feat: add multi-pokemon slot controls"
```

### Task 3: Connect slot selection, editing, removal, and storage

**Files:**
- Modify: `src/popup/popup.js`
- Modify: `test/popup-roster.test.mjs`

**Interfaces:**
- Consumes the roster functions from `./roster.js`.
- Persists `vcp1_packs` as the roster and mirrors the selected entry to legacy-compatible `vcp1_pack`.
- Keeps the current picker, shuffle button, chevrons, and search flow as the editor for the selected slot.

- [ ] **Step 1: Add failing source-contract assertions for integration wiring**

Append assertions that `popup.js` imports the roster module, reads `vcp1_packs`, writes `vcp1_packs`, mirrors `vcp1_pack`, renders `rosterSlots`, and handles `slot-remove`.

```js
const popup = fs.readFileSync(new URL("../src/popup/popup.js", import.meta.url), "utf8");
assert.match(popup, /from ["']\.\/roster\.js["']/);
assert.match(popup, /vcp1_packs/);
assert.match(popup, /vcp1_pack/);
assert.match(popup, /rosterSlots/);
assert.match(popup, /slot-remove/);
```

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `node --test test/popup-roster.test.mjs`

Expected: FAIL because the existing popup controller has no roster integration.

- [ ] **Step 3: Implement the popup controller integration**

At the top of `popup.js`, import the roster helpers and add state:

```js
let roster = [DEFAULT_PACK];
let selectedSlot = 0;
```

Implement these controller behaviors:

1. On storage load, read `vcp1_packs` alongside the existing settings. Normalize it using `vcp1_pack` or `DEFAULT_PACK` as fallback. Initialize `selectedSlot` to `0`, render the six slots, and select the first roster entry. If the plural key is absent, write the migrated roster and the selected `vcp1_pack`.
2. Render exactly six slot items. Occupied items show `../assets/icons/pokeball-32.png`; empty items show black circles. Occupied slot buttons select their index. Only the first empty item is enabled to add the next slot, preventing gaps; later empty circles remain visibly black but disabled.
3. Clicking the first empty item appends `DEFAULT_PACK`, selects it, saves the roster, and loads it into the existing picker.
4. Clicking an occupied slot updates `selectedSlot`, updates the select and preview, closes an open search field, and does not change roster length.
5. Show the small remove button only for a selected occupied slot with index greater than `0`. Stop its click event from selecting the slot, remove the slot with `removeRosterSlot`, select the previous remaining slot, save, rerender, and load the new active pack.
6. Change the existing picker `change` handler so it calls `setRosterPack`, saves `{ vcp1_packs: roster, vcp1_pack: selectedPack }`, rerenders the slot strip, and retains the current preview behavior. Existing shuffle, search, and chevron handlers continue to dispatch this same change event.
7. Keep the content script contract unchanged: the selected pack is still sent through `vcp1_pack`, so only the selected Pokémon remains active in this first switcher slice.

- [ ] **Step 4: Run focused and full tests**

Run:

```bash
node --test test/popup-roster.test.mjs
node --test test/*.test.mjs
```

Expected: all tests pass with no warnings.

- [ ] **Step 5: Commit**

```bash
git add src/popup/popup.js test/popup-roster.test.mjs
git commit -m "feat: wire multi-pokemon popup switcher"
```

### Task 4: Verify the popup behavior in Chrome

**Files:**
- No additional files unless verification exposes a defect.

- [ ] **Step 1: Build the extension assets if needed**

Run: `npm run build:index`

Expected: the generated pack index completes without errors and the working tree remains unchanged unless the index was stale.

- [ ] **Step 2: Load the branch as an unpacked extension**

In `chrome://extensions`, reload the unpacked extension from this worktree and open the popup on a normal website.

- [ ] **Step 3: Verify the approved interactions**

Confirm:

- six circles appear beneath the version label;
- the first slot is occupied and the other five are black;
- clicking the first empty slot creates a Bulbasaur slot and keeps the popup open;
- clicking occupied slots switches the preview and active follower without removing anything;
- the selected extra slot shows a tiny red outlined `×` above it;
- clicking the Pokéball body selects it, while clicking only the `×` removes it;
- removing a middle slot shifts later Pokémon left;
- slot 1 has no remove badge;
- reopening the popup preserves the roster;
- the active page still shows only the selected Pokémon.

- [ ] **Step 4: Run final checks**

Run: `node --test test/*.test.mjs && git diff --check && git status --short --branch`

Expected: all tests pass, no whitespace errors, and only the intended branch commits are present.
