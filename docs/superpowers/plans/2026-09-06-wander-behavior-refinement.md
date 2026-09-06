# Wander Behavior Refinement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Wander Mode visually subordinate to Follow Mode and give it a slower roam/idle/sleep cycle controlled by the existing popup speed setting.

**Architecture:** Keep one follower element and one animation loop. Extend the tested classic-script movement helper with nearby-target, speed, duration, and sleep-decision primitives; keep phase deadlines in content.js. Adjust only the existing popup header layout.

**Tech Stack:** Chrome Manifest V3, vanilla JavaScript, HTML/CSS, Node node:test and vm.

## Global Constraints

- Follow Mode keeps its existing speed mapping and cursor behavior.
- Wander Mode uses 50% of the popup-controlled Follow speed.
- Wander destinations are at most 220 px from the current position when the viewport allows it.
- Idle pauses last 1.5–4.5 seconds.
- After at least three destinations, a pack with a sleep state has a 35% chance to sleep for 15–60 seconds, then resumes roaming.
- Packs without a sleep state skip sleeping.
- Wander Mode is directly beneath Follow Mode in the right-aligned popup control group.
- No new settings, assets, pack schema, collision detection, or multi-Pokémon behavior.

---

### Task 1: Test and extend movement primitives

**Files:**
- Modify: test/content-mode.test.mjs
- Modify: src/content-mode.js

**Interfaces:**
- wanderSpeed(baseSpeed) returns baseSpeed * 0.5.
- pickNearbyWanderTarget(bounds, origin, previousTarget, maxDistance, random) returns a safe nearby point.
- randomBetween(min, max, random) returns a bounded number.
- shouldSleepAfterWander({ hasSleep, destinations, randomValue }) returns true only when sleep is available, destinations is at least 3, and randomValue is below 0.35.

- [ ] Step 1: Write the failing tests.

Add tests for speed, nearby safe targets, sleep eligibility, and 15–60 second bounds:

~~~js
test("wander speed is derived from popup speed", () => {
  assert.equal(mode.wanderSpeed(260), 130);
});

test("nearby targets stay safe and local", () => {
  const bounds = mode.getWanderBounds({
    viewportWidth: 800, viewportHeight: 600,
    spriteWidth: 40, spriteHeight: 40, scale: 1, edgeMargin: 12
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
~~~

- [ ] Step 2: Run the tests and confirm the expected red failure.

Run:

~~~bash
node --test test/content-mode.test.mjs
~~~

Expected: the new tests fail because the four helper functions do not exist.

- [ ] Step 3: Implement the helper functions.

Add the four functions to src/content-mode.js and expose them on globalThis.__vcp1Mode. Generate nearby points with a random angle and distance, clamp them to bounds, and fall back to pickWanderTarget if the result equals the previous target.

- [ ] Step 4: Run the focused helper tests and existing page checks.

~~~bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
~~~

Expected: all eleven tests pass.

- [ ] Step 5: Commit the primitives.

~~~bash
git add src/content-mode.js test/content-mode.test.mjs
git commit -m "feat: add calm wander behavior primitives"
~~~

### Task 2: Add roam, idle, and sleep phases

**Files:**
- Modify: src/content.js
- Modify: test/content-mode.test.mjs

**Interfaces:**
- Consume the Task 1 helper API through globalThis.__vcp1Mode.
- Keep walkSpeedFromConfig as the Follow Mode source and use MODE.wanderSpeed(walkSpeedFromConfig()) only while wandering.

- [ ] Step 1: Write the failing timing-contract test.

~~~js
test("wander timing contract is present", () => {
  const source = fs.readFileSync(new URL("../src/content.js", import.meta.url), "utf8");
  assert.match(source, /WANDER_IDLE_MIN_MS\s*=\s*1500/);
  assert.match(source, /WANDER_IDLE_MAX_MS\s*=\s*4500/);
  assert.match(source, /WANDER_SLEEP_MIN_MS\s*=\s*15000/);
  assert.match(source, /WANDER_SLEEP_MAX_MS\s*=\s*60000/);
});
~~~

- [ ] Step 2: Run the test and confirm it fails.

~~~bash
node --test test/content-mode.test.mjs
~~~

Expected: only the timing-contract test fails because the constants are absent.

- [ ] Step 3: Add phase state and constants.

Add these constants to src/content.js:

~~~js
const WANDER_IDLE_MIN_MS = 1500;
const WANDER_IDLE_MAX_MS = 4500;
const WANDER_SLEEP_MIN_MS = 15000;
const WANDER_SLEEP_MAX_MS = 60000;
const WANDER_MAX_STEP_PX = 220;
const WANDER_SLEEP_MIN_DESTINATIONS = 3;
const WANDER_SLEEP_CHANCE = 0.35;
~~~

Add wanderPhase, wanderIdleUntil, wanderSleepUntil, and wanderDestinations to RUNTIME. Reset all four in resetWanderState.

- [ ] Step 4: Implement computeWanderTarget(now).

Keep viewport bounds. While phase is sleep, hold target at current position until wanderSleepUntil, then reset the phase and destination count. While phase is roam, walk toward a nearby target. Upon arrival, enter idle until a random 1.5–4.5 seconds deadline. When idle expires, increment destinations; if hasState("sleep"), the destination count is at least 3, and a 35% roll succeeds, enter sleep for a random 15–60 seconds. Otherwise return to roam with another nearby target.

- [ ] Step 5: Use popup speed and sleep animation.

In the shared movement block use:

~~~js
const baseSpeed = walkSpeedFromConfig();
const walkSpeed = RUNTIME.isWandering ? MODE.wanderSpeed(baseSpeed) : baseSpeed;
~~~

Make pickStateBySpeed return sleep during the Wander sleep phase and idle during the Wander idle phase. Preserve existing Follow Mode sleep behavior. When pointer movement interrupts hybrid wandering, reset the wander phase, deadlines, and target.

- [ ] Step 6: Run runtime checks.

~~~bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
node --check src/content-mode.js
node --check src/content.js
git diff --check
~~~

Expected: all twelve tests pass and syntax checks exit 0.

- [ ] Step 7: Commit the runtime behavior.

~~~bash
git add src/content.js test/content-mode.test.mjs
git commit -m "feat: add roam idle and sleep phases"
~~~

### Task 3: Stack the popup controls vertically

**Files:**
- Modify: src/popup/index.html
- Modify: test/content-mode.test.mjs

- [ ] Step 1: Write the failing markup test.

~~~js
test("popup places Wander Mode below Follow Mode", () => {
  const html = fs.readFileSync(new URL("../src/popup/index.html", import.meta.url), "utf8");
  assert.ok(html.indexOf("Follow Mode") < html.indexOf("Wander Mode"));
  assert.match(html, /\.mode-toggles\s*\{[^}]*flex-direction:\s*column/s);
});
~~~

- [ ] Step 2: Run it and confirm it fails.

~~~bash
node --test test/content-mode.test.mjs
~~~

Expected: the layout assertion fails because mode-toggles is horizontal.

- [ ] Step 3: Change the existing CSS.

Set the header tall enough for two rows and make the existing mode-toggles group vertical:

~~~css
.header {
  height: 50px;
  align-items: start;
}
.mode-toggles {
  display: inline-flex;
  flex-direction: column;
  align-items: end;
  gap: 4px;
}
~~~

Keep the existing IDs, labels, toggle styling, focus outline, and storage handlers.

- [ ] Step 4: Run popup and full checks.

~~~bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
node --check src/popup/popup.js
git diff --check
~~~

Expected: all thirteen tests pass.

- [ ] Step 5: Commit the layout refinement.

~~~bash
git add src/popup/index.html test/content-mode.test.mjs
git commit -m "fix: stack follower mode toggles"
~~~

### Task 4: Final verification and Chrome handoff

**Files:**
- Modify: none unless a verification failure identifies a concrete defect.

- [ ] Step 1: Run the complete automated suite.

~~~bash
node --test test/content-mode.test.mjs test/page-check.test.mjs
node --check src/content-mode.js
node --check src/content.js
node --check src/popup/popup.js
node --check src/popup/page-check.js
python3 -m json.tool src/manifest.json >/dev/null
npm run build:index
git diff --check
git status --short --branch
~~~

- [ ] Step 2: Manually verify in Chrome.

Verify the stacked controls; Follow Mode only with unchanged speed; Wander Mode at a calmer slider-controlled pace; nearby walking; idle pauses; eventual bounded sleep and resume; hybrid interruption of idle or sleep; resize; pack switching; and disabling both modes.

- [ ] Step 3: Push after verification.

~~~bash
git push
git ls-remote origin refs/heads/feature/wander-mode
~~~

Report the final branch commit and any manual behavior that still needs tuning before merging.
