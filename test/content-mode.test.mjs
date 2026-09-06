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
