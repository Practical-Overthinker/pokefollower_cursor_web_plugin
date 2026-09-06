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

test("only Multiple hybrid mode enters independent wander after pointer idle", () => {
  const active = {
    rosterMode: "multiple",
    followMode: true,
    wanderMode: true,
    lastMoveTs: 1000,
    now: 3999
  };
  assert.equal(mode.isIndependentWander(active), false);
  assert.equal(mode.isIndependentWander({ ...active, now: 4000 }), true);
  assert.equal(mode.isIndependentWander({ ...active, rosterMode: "individual", now: 4000 }), false);
  assert.equal(mode.isIndependentWander({ ...active, followMode: false, now: 4000 }), true);
});

test("trailing targets use movement direction and spacing", () => {
  const moving = mode.getTrailingTarget({
    previousPosition: { x: 100, y: 100 },
    previousTarget: { x: 200, y: 100 },
    spacing: 30,
    fallbackDirection: { x: 0, y: 1 }
  });
  assert.equal(moving.x, 70);
  assert.equal(moving.y, 100);

  const stationary = mode.getTrailingTarget({
    previousPosition: { x: 100, y: 100 },
    previousTarget: { x: 100, y: 100 },
    spacing: 30,
    fallbackDirection: { x: 0, y: 1 }
  });
  assert.equal(stationary.x, 100);
  assert.equal(stationary.y, 70);
});

test("chain follower facing points toward the previous pokemon", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.match(source, /function pickRowForState\(actor, stateName, index\)/);
  assert.match(source, /MODE\.getChainFacingVector/);
  assert.match(source, /pickRowForState\(actor, runtime\.anim\.name, index\)/);

  const direction = mode.getChainFacingVector({
    actorPosition: { x: 100, y: 100 },
    previousPosition: { x: 160, y: 70 }
  });
  assert.equal(direction.x, 60);
  assert.equal(direction.y, -30);
});

test("configured chain distance becomes a visible gap after sprite footprints", () => {
  assert.equal(
    mode.getFollowerSpacing({
      configuredDistance: 30,
      previousSize: { w: 32, h: 40 },
      currentSize: { w: 32, h: 40 },
      scale: 3
    }),
    150
  );
});

test("wandering positions keep the configured minimum center distance", () => {
  const separated = mode.separatePositions({
    first: { x: 100, y: 100 },
    second: { x: 110, y: 100 },
    minimumDistance: 30
  });

  assert.equal(
    Math.hypot(
      separated.second.x - separated.first.x,
      separated.second.y - separated.first.y
    ),
    30
  );
  assert.equal(separated.changed, true);
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

test("popup keeps stacked modes compact and readable", () => {
  const html = fs.readFileSync(new URL("../src/popup/index.html", import.meta.url), "utf8");
  assert.match(html, /\.header\s*\{[^}]*height:\s*58px/s);
  assert.match(html, /\.mode-toggles\s*\{[^}]*gap:\s*2px/s);
  assert.match(html, /\.mode-toggle\s*\{[^}]*font-size:\s*12px/s);
});

test("scale 1 keeps the previous 3x visual baseline", () => {
  const popup = fs.readFileSync(new URL("../src/popup/popup.js", import.meta.url), "utf8");
  const content = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.match(popup, /const SCALE_BASE = 3/);
  assert.match(popup, /vcp1_scale:\s*1(?:\.0+)?\s*,/);
  assert.match(popup, /vcp1_scale_version/);
  assert.match(content, /const SCALE_BASE = 3/);
  assert.match(content, /scale:\s*1(?:\.0+)?\s*,/);
  assert.match(content, /CONFIG\.scale\s*\*\s*SCALE_BASE/);
});

test("wander facing is preserved when walking settles into idle", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.doesNotMatch(
    source,
    /RUNTIME\.isWalking = false;\s*if \(RUNTIME\.isWandering\) \{\s*RUNTIME\.moveVel\.x = 0;/s
  );
});

test("content runtime reads the roster and keeps Individual mode single-actor", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.match(source, /vcp1_packs/);
  assert.match(source, /vcp1_roster_mode/);
  assert.match(source, /function createFollowerRuntime/);
  assert.match(source, /const ACTORS\s*=\s*\[\]/);
  assert.match(source, /function activePackKeys/);
  assert.match(source, /rosterMode === "individual"/);
});

test("Multiple Follow derives ordered trailing targets from prior actors", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.match(source, /STATE\.rosterMode === "multiple" && index > 0/);
  assert.match(source, /const previousActor = ACTORS\[index - 1\];\s*const previous = previousActor\.runtime/s);
  assert.match(source, /MODE\.getTrailingTarget/);
  assert.match(source, /MODE\.getFollowerSpacing/);
  assert.match(source, /configuredDistance:\s*CONFIG\.offset/);
  assert.match(source, /ACTORS\.length\s*=\s*0/);

  const first = mode.getTrailingTarget({
    previousPosition: { x: 100, y: 100 },
    previousTarget: { x: 200, y: 100 },
    spacing: 30
  });
  const second = mode.getTrailingTarget({
    previousPosition: first,
    previousTarget: { x: first.x + 100, y: first.y },
    spacing: 30
  });
  assert.equal(first.x, 70);
  assert.equal(second.x, 40);
});

test("Multiple Wander keeps per-actor phases and resets them for hybrid rejoin", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.match(source, /function computeWanderTarget\(actor, now\)/);
  assert.match(source, /runtime\.wanderTarget/);
  assert.match(source, /runtime\.wanderPhase/);
  assert.match(source, /runtime\.isWandering = STATE\.wander && !following/);
  assert.match(source, /if \(!following\) \{\s*computeWanderTarget\(actor, now\)/s);
  assert.match(source, /if \(separated\.changed\) \{[\s\S]*runtime\.wanderTarget = null/s);
  assert.match(source, /ACTORS\.forEach\(\(actor\) => \{\s*resetWanderState\(actor\)/s);
  assert.match(source, /function removeActorElements/);
  assert.match(source, /if \(MODE\.isActive\(STATE\.enabled, STATE\.wander\)\) start\(\);/);
  assert.match(source, /let rebuildToken = 0/);
});
