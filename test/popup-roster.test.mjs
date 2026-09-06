import fs from "node:fs";
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

test("popup markup provides the slot strip and remove affordance contract", () => {
  const html = fs.readFileSync(new URL("../src/popup/index.html", import.meta.url), "utf8");
  assert.match(html, /class="brand-block"/);
  assert.match(html, /id="rosterSlots"/);
  assert.match(html, /<script type="module" src="popup\.js"><\/script>/);
  assert.match(html, /\.slot-remove\s*\{[^}]*position:\s*absolute/s);
  assert.match(html, /\.slot-remove\s*\{[^}]*background:\s*#ef4036/s);
  assert.match(html, /\.slot-remove\s*\{[^}]*border[^}]*#000/s);
});

test("popup controller is wired for roster storage and slot actions", () => {
  const popup = fs.readFileSync(new URL("../src/popup/popup.js", import.meta.url), "utf8");
  assert.match(popup, /from ["']\.\/roster\.js["']/);
  assert.match(popup, /vcp1_packs/);
  assert.match(popup, /vcp1_pack/);
  assert.match(popup, /rosterSlots/);
  assert.match(popup, /slot-remove/);
});
