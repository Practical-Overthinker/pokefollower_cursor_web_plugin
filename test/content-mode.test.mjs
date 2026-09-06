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

test("wander speed is derived from popup speed", () => {
  assert.equal(mode.wanderSpeed(260), 130);
});

test("nearby targets stay safe and local", () => {
  const bounds = mode.getWanderBounds({
    viewportWidth: 800,
    viewportHeight: 600,
    spriteWidth: 40,
    spriteHeight: 40,
    scale: 1,
    edgeMargin: 12
  });
  const origin = { x: 400, y: 300 };
  const target = mode.pickNearbyWanderTarget(bounds, origin, null, 220, () => 0.5);
  assert.equal(mode.isWithinBounds(target, bounds), true);
  assert.ok(Math.hypot(target.x - origin.x, target.y - origin.y) <= 220);
});

test("sleep eligibility requires the sleep state, three stops, and the chance roll", () => {
  assert.equal(mode.shouldSleepAfterWander({ hasSleep: false, destinations: 8, randomValue: 0 }), false);
  assert.equal(mode.shouldSleepAfterWander({ hasSleep: true, destinations: 2, randomValue: 0 }), false);
  assert.equal(mode.shouldSleepAfterWander({ hasSleep: true, destinations: 3, randomValue: 0.34 }), true);
  assert.equal(mode.shouldSleepAfterWander({ hasSleep: true, destinations: 3, randomValue: 0.35 }), false);
});

test("random sleep duration stays between fifteen and sixty seconds", () => {
  assert.equal(mode.randomBetween(15000, 60000, () => 0), 15000);
  assert.equal(mode.randomBetween(15000, 60000, () => 1), 60000);
});

test("wander timing contract is present", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.match(source, /WANDER_IDLE_MIN_MS\s*=\s*1500/);
  assert.match(source, /WANDER_IDLE_MAX_MS\s*=\s*4500/);
  assert.match(source, /WANDER_SLEEP_MIN_MS\s*=\s*15000/);
  assert.match(source, /WANDER_SLEEP_MAX_MS\s*=\s*60000/);
});

test("popup places Wander Mode below Follow Mode", () => {
  const html = fs.readFileSync(new URL("../src/popup/index.html", import.meta.url), "utf8");
  assert.ok(html.indexOf("Follow Mode") < html.indexOf("Wander Mode"));
  assert.match(html, /\.mode-toggles\s*\{[^}]*flex-direction:\s*column/s);
});

test("wander facing is preserved when walking settles into idle", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.doesNotMatch(
    source,
    /RUNTIME\.isWalking = false;\s*if \(RUNTIME\.isWandering\) \{\s*RUNTIME\.moveVel\.x = 0;/s
  );
});
