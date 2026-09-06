// === VCP1 content script: load pack JSON + animate one or more followers ===
const DEFAULT_PACK = "retro/gen-1/001-bulbasaur";
const GENERATION_DIRS = ["gen-1", "gen-2", "gen-3", "gen-4", "gen-5", "gen-6", "gen-7", "gen-8", "gen-9"];
const MODE = globalThis.__vcp1Mode;
const SCALE_BASE = 3;
const SCALE_VERSION = 2;

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

const ACTORS = [];
let rafId = null;
let running = false;
let rebuildToken = 0;

function createFollowerRuntime() {
  return {
    anim: { name: "idle", frame: 0, row: 0, accMs: 0 },
    wanderTarget: null,
    isWandering: false,
    moveVel: { x: 0, y: 0 },
    wanderPhase: "roam",
    wanderIdleUntil: 0,
    wanderSleepUntil: 0,
    wanderDestinations: 0,
    pos: { x: 0, y: 0 },
    target: { x: 0, y: 0 },
    offsetDir: { x: 0, y: -1 },
    isWalking: false,
    pendingState: null
  };
}

// --- behavior thresholds ---
const SLEEP_TIMEOUT_MS = 30000;
const ARRIVE_RADIUS_PX = 6;
const SLOW_RADIUS_PX = 60;
const WANDER_IDLE_MIN_MS = 1500;
const WANDER_IDLE_MAX_MS = 4500;
const WANDER_SLEEP_MIN_MS = 15000;
const WANDER_SLEEP_MAX_MS = 60000;
const WANDER_MAX_STEP_PX = 220;
const WANDER_SLEEP_MIN_DESTINATIONS = 3;
const WANDER_SLEEP_CHANCE = 0.35;
const WANDER_EDGE_MARGIN_PX = 12;

function hasState(actor, name) {
  return !!(actor?.meta?.states && actor.meta.states[name]);
}

// --- UI-configurable tuning (persisted in chrome.storage.sync) ---
const CONFIG = {
  scale: 1,
  offset: 30,
  lerp: 0.20
};

function normalizeStoredScale(value, version) {
  if (typeof value !== "number" || !Number.isFinite(value)) return CONFIG.scale;
  if (version === SCALE_VERSION) return value;
  return Number((value / SCALE_BASE).toFixed(2));
}

function visualScale() {
  return CONFIG.scale * SCALE_BASE;
}

function applyConfigPatch(obj = {}) {
  if (typeof obj.vcp1_scale === "number" && !Number.isNaN(obj.vcp1_scale)) CONFIG.scale = obj.vcp1_scale;
  if (typeof obj.vcp1_offset === "number" && !Number.isNaN(obj.vcp1_offset)) CONFIG.offset = obj.vcp1_offset;
  if (typeof obj.vcp1_lerp === "number" && !Number.isNaN(obj.vcp1_lerp)) CONFIG.lerp = obj.vcp1_lerp;
}

// Map the popup's SPEED value onto a steady walking speed in px/s.
const WALK_SPEED_MIN_PXPS = 80;
const WALK_SPEED_MAX_PXPS = 640;
const SPEED_CONFIG_MIN = 0.05;
const SPEED_CONFIG_MAX = 0.50;

function walkSpeedFromConfig() {
  const t = (CONFIG.lerp - SPEED_CONFIG_MIN) / (SPEED_CONFIG_MAX - SPEED_CONFIG_MIN);
  const clamped = Math.min(1, Math.max(0, t));
  return WALK_SPEED_MIN_PXPS + clamped * (WALK_SPEED_MAX_PXPS - WALK_SPEED_MIN_PXPS);
}

// --- Live poller for smooth slider updates during popup drag ---
let LIVE = { dragging: false, pollId: null };

function applyFrames() {
  ACTORS.forEach(applyFrame);
}

function startLocalPoll() {
  if (LIVE.pollId) return;
  LIVE.pollId = setInterval(() => {
    chrome.storage.local.get(["vcp1_scale", "vcp1_offset", "vcp1_lerp"], (res) => {
      const patch = {};
      if (typeof res.vcp1_scale === "number") patch.vcp1_scale = res.vcp1_scale;
      if (typeof res.vcp1_offset === "number") patch.vcp1_offset = res.vcp1_offset;
      if (typeof res.vcp1_lerp === "number") patch.vcp1_lerp = res.vcp1_lerp;
      if (Object.keys(patch).length) {
        applyConfigPatch(patch);
        applyFrames();
      }
    });
  }, 33);
}

function stopLocalPoll() {
  if (LIVE.pollId) {
    clearInterval(LIVE.pollId);
    LIVE.pollId = null;
  }
}

// --- follow targeting: trail the cursor when moving; perch above when idle ---
function computeFollowTarget(actor) {
  const runtime = actor.runtime;
  const speed = POINTER.speedAvg || 0;
  const hasDir = speed > 40;
  const offset = CONFIG.offset;
  let desiredX;
  let desiredY;

  if (hasDir) {
    desiredX = -(POINTER.velAvg.x / (speed || 1));
    desiredY = -(POINTER.velAvg.y / (speed || 1));
  } else {
    desiredX = 0;
    desiredY = -1;
  }

  const directionLerp = 0.08;
  runtime.offsetDir.x += (desiredX - runtime.offsetDir.x) * directionLerp;
  runtime.offsetDir.y += (desiredY - runtime.offsetDir.y) * directionLerp;
  runtime.target.x = (POINTER.lastMouse.x || 0) + runtime.offsetDir.x * offset;
  runtime.target.y = (POINTER.lastMouse.y || 0) + runtime.offsetDir.y * offset;
}

function resetWanderState(actor) {
  const runtime = actor.runtime;
  runtime.wanderTarget = null;
  runtime.wanderPhase = "roam";
  runtime.wanderIdleUntil = 0;
  runtime.wanderSleepUntil = 0;
  runtime.wanderDestinations = 0;
  runtime.moveVel.x = 0;
  runtime.moveVel.y = 0;
}

function spriteSizeFor(actor) {
  return actor.meta?.states?.walk?.frame || actor.meta?.states?.idle?.frame || { w: 40, h: 40 };
}

function currentWanderBounds(actor) {
  const frame = spriteSizeFor(actor);
  return MODE.getWanderBounds({
    viewportWidth: window.innerWidth,
    viewportHeight: window.innerHeight,
    spriteWidth: frame.w,
    spriteHeight: frame.h,
    scale: visualScale(),
    edgeMargin: WANDER_EDGE_MARGIN_PX
  });
}

function chooseWanderTarget(actor, bounds = currentWanderBounds(actor)) {
  const runtime = actor.runtime;
  runtime.wanderTarget = MODE.pickNearbyWanderTarget(
    bounds,
    runtime.pos,
    runtime.wanderTarget,
    WANDER_MAX_STEP_PX
  );
  return runtime.wanderTarget;
}

function reachedWanderTarget(actor) {
  const runtime = actor.runtime;
  return Math.hypot(
    runtime.wanderTarget.x - runtime.pos.x,
    runtime.wanderTarget.y - runtime.pos.y
  ) <= ARRIVE_RADIUS_PX;
}

function computeWanderTarget(actor, now) {
  const runtime = actor.runtime;
  const bounds = currentWanderBounds(actor);
  if (runtime.wanderTarget && !MODE.isWithinBounds(runtime.wanderTarget, bounds)) {
    runtime.wanderTarget = null;
    runtime.wanderPhase = "roam";
    runtime.wanderIdleUntil = 0;
  }

  if (runtime.wanderPhase === "sleep") {
    runtime.target.x = runtime.pos.x;
    runtime.target.y = runtime.pos.y;
    if (now < runtime.wanderSleepUntil) return;
    runtime.wanderPhase = "roam";
    runtime.wanderSleepUntil = 0;
    runtime.wanderDestinations = 0;
    runtime.wanderTarget = null;
  }

  if (!runtime.wanderTarget) chooseWanderTarget(actor, bounds);

  if (runtime.wanderPhase === "roam" && reachedWanderTarget(actor)) {
    runtime.wanderPhase = "idle";
    runtime.wanderIdleUntil = now + MODE.randomBetween(WANDER_IDLE_MIN_MS, WANDER_IDLE_MAX_MS);
  }

  if (runtime.wanderPhase === "idle") {
    runtime.target.x = runtime.pos.x;
    runtime.target.y = runtime.pos.y;
    if (now < runtime.wanderIdleUntil) return;

    runtime.wanderIdleUntil = 0;
    runtime.wanderDestinations += 1;
    if (MODE.shouldSleepAfterWander({
      hasSleep: hasState(actor, "sleep"),
      destinations: runtime.wanderDestinations,
      randomValue: Math.random(),
      minDestinations: WANDER_SLEEP_MIN_DESTINATIONS,
      chance: WANDER_SLEEP_CHANCE
    })) {
      runtime.wanderPhase = "sleep";
      runtime.wanderSleepUntil = now + MODE.randomBetween(WANDER_SLEEP_MIN_MS, WANDER_SLEEP_MAX_MS);
      runtime.target.x = runtime.pos.x;
      runtime.target.y = runtime.pos.y;
      return;
    }

    runtime.wanderPhase = "roam";
    chooseWanderTarget(actor, bounds);
  }

  runtime.target.x = runtime.wanderTarget.x;
  runtime.target.y = runtime.wanderTarget.y;
}

function computeTarget(actor, index, now) {
  const runtime = actor.runtime;
  const following = MODE.shouldFollow({
    followMode: STATE.enabled,
    wanderMode: STATE.wander,
    lastMoveTs: POINTER.lastMoveTs,
    now
  });
  runtime.isWandering = STATE.wander && !following;

  if (!following) {
    computeWanderTarget(actor, now);
    return;
  }

  resetWanderState(actor);
  if (STATE.rosterMode === "multiple" && index > 0 && ACTORS[index - 1]) {
    const previousActor = ACTORS[index - 1];
    const previous = previousActor.runtime;
    const spacing = MODE.getFollowerSpacing({
      configuredDistance: CONFIG.offset,
      previousSize: spriteSizeFor(previousActor),
      currentSize: spriteSizeFor(actor),
      scale: visualScale()
    });
    const target = MODE.getTrailingTarget({
      previousPosition: previous.pos,
      previousTarget: previous.target,
      spacing,
      fallbackDirection: POINTER.velAvg
    });
    runtime.target.x = target.x;
    runtime.target.y = target.y;
  } else {
    computeFollowTarget(actor);
  }
}

function enforceWanderSeparation() {
  if (STATE.rosterMode !== "multiple" || ACTORS.length < 2) return;

  for (let pass = 0; pass < ACTORS.length; pass += 1) {
    for (let firstIndex = 0; firstIndex < ACTORS.length; firstIndex += 1) {
      const firstActor = ACTORS[firstIndex];
      if (!firstActor.runtime.isWandering) continue;

      for (let secondIndex = firstIndex + 1; secondIndex < ACTORS.length; secondIndex += 1) {
        const secondActor = ACTORS[secondIndex];
        if (!secondActor.runtime.isWandering) continue;

        const minimumDistance = MODE.getFollowerSpacing({
          configuredDistance: CONFIG.offset,
          previousSize: spriteSizeFor(firstActor),
          currentSize: spriteSizeFor(secondActor),
          scale: visualScale()
        });
        const separated = MODE.separatePositions({
          first: firstActor.runtime.pos,
          second: secondActor.runtime.pos,
          minimumDistance
        });
        firstActor.runtime.pos = separated.first;
        secondActor.runtime.pos = separated.second;
        if (separated.changed) {
          [firstActor, secondActor].forEach((blockedActor) => {
            if (!blockedActor.runtime.isWalking) return;
            blockedActor.runtime.wanderTarget = null;
            blockedActor.runtime.wanderPhase = "roam";
            blockedActor.runtime.wanderIdleUntil = 0;
          });
        }
      }
    }
  }
}

// --- 8-way facing from a direction vector (octants) ---
function pickDir8FromVector(vx, vy) {
  const dead = 0.3;
  if (Math.abs(vx) <= dead && Math.abs(vy) <= dead) return "front";
  const angle = Math.atan2(vy, vx);
  const norm = (angle + 2 * Math.PI) % (2 * Math.PI);
  const idx = Math.floor((norm + Math.PI / 8) / (Math.PI / 4)) % 8;
  return ["right", "frontRight", "front", "frontLeft", "left", "backLeft", "back", "backRight"][idx];
}

function pickRowForState(actor, stateName, index) {
  const st = actor.meta?.states?.[stateName];
  if (!st) return 0;
  const rows = st.rows || { front: 0 };
  let direction;
  if (actor.runtime.isWandering) {
    direction = actor.runtime.moveVel;
  } else if (STATE.rosterMode === "multiple" && index > 0 && ACTORS[index - 1]) {
    const previous = ACTORS[index - 1].runtime;
    direction = MODE.getChainFacingVector({
      actorPosition: actor.runtime.pos,
      previousPosition: previous.pos,
      fallbackDirection: {
        x: previous.target.x - actor.runtime.target.x,
        y: previous.target.y - actor.runtime.target.y
      }
    });
  } else {
    direction = POINTER.velAvg;
  }
  const dir8 = pickDir8FromVector(direction.x, direction.y);
  if (dir8 in rows) return rows[dir8];
  const fallbackMap = {
    frontRight: "front",
    frontLeft: "front",
    backRight: "back",
    backLeft: "back"
  };
  const fallback = fallbackMap[dir8] || dir8;
  return fallback in rows ? rows[fallback] : (rows.front ?? 0);
}

// Once the extension is reloaded/updated, tabs that already had this content
// script injected lose their connection to it. Shut down quietly in that case.
function isExtensionContextValid() {
  try {
    return !!(chrome.runtime && chrome.runtime.id);
  } catch (_) {
    return false;
  }
}

function extUrl(rel) {
  return chrome.runtime.getURL(rel);
}

function createFollower(actor, index) {
  if (actor.element) return;
  const element = document.createElement("div");
  element.id = `__vcp1_follower_${index}`;
  Object.assign(element.style, {
    position: "fixed",
    left: "0px",
    top: "0px",
    width: "40px",
    height: "40px",
    pointerEvents: "none",
    zIndex: "2147483647",
    willChange: "transform, background-position, background-image",
    backgroundRepeat: "no-repeat",
    imageRendering: "pixelated",
    transition: "transform 120ms linear, width 120ms linear, height 120ms linear"
  });
  document.documentElement.appendChild(element);
  actor.element = element;
}

function removeActorElements() {
  ACTORS.forEach((actor) => {
    if (actor.element?.parentNode) actor.element.parentNode.removeChild(actor.element);
    actor.element = null;
  });
}

function packSlug(packKey = STATE.pack) {
  const parts = String(packKey || DEFAULT_PACK).split("/");
  return parts[parts.length - 1];
}

function dexFromSlug(slug) {
  const dex = parseInt((slug || "").split("-")[0], 10);
  return Number.isFinite(dex) ? dex : null;
}

function generationForDex(dex) {
  if (!Number.isFinite(dex)) return null;
  if (dex <= 151) return "gen-1";
  if (dex <= 251) return "gen-2";
  if (dex <= 386) return "gen-3";
  if (dex <= 493) return "gen-4";
  if (dex <= 649) return "gen-5";
  if (dex <= 721) return "gen-6";
  if (dex <= 809) return "gen-7";
  if (dex <= 905) return "gen-8";
  return "gen-9";
}

function buildPackCandidates(packKey) {
  const clean = typeof packKey === "string" ? packKey.trim().replace(/^\/+|\/+$/g, "") : "";
  if (!clean) return [DEFAULT_PACK];
  const candidates = [clean];
  if (!clean.includes("/gen-")) {
    const parts = clean.split("/");
    const slug = parts.pop();
    const prefix = parts.join("/");
    const inferred = generationForDex(dexFromSlug(slug));
    const pushCandidate = (gen) => {
      const candidate = `${prefix}/${gen}/${slug}`;
      if (!candidates.includes(candidate)) candidates.push(candidate);
    };
    if (inferred) pushCandidate(inferred);
    GENERATION_DIRS.forEach(pushCandidate);
  }
  return candidates;
}

async function fetchPackMeta(packKey) {
  const jsonPath = `assets/packs/${packKey}.json`;
  const res = await fetch(extUrl(jsonPath));
  if (!res.ok) {
    const error = new Error(`HTTP ${res.status} for ${jsonPath}`);
    error.status = res.status;
    throw error;
  }
  const meta = await res.json();
  if (!meta || !meta.states || !meta.states.idle || !meta.states.walk) {
    throw new Error("Pack schema invalid: missing states.idle or states.walk");
  }
  return meta;
}

function sheetUrlFor(actor, stateName) {
  const state = actor.meta?.states?.[stateName];
  const sheetFilename = state?.sheet || "";
  const metaPath = typeof actor.meta?.rawPath === "string" ? actor.meta.rawPath.trim() : "";
  const slug = metaPath ? metaPath.replace(/^\/+|\/+$/g, "") : packSlug(actor.packKey);
  return extUrl(`assets/raw/${slug}/${sheetFilename}`);
}

function ensureImagesLoaded(actor) {
  const tasks = [];
  Object.keys(actor.meta.states).forEach((stateName) => {
    const img = new Image();
    img.src = sheetUrlFor(actor, stateName);
    actor.images[stateName] = img;
    tasks.push(new Promise((resolve) => {
      img.onload = resolve;
      img.onerror = resolve;
    }));
  });
  return Promise.all(tasks);
}

function resetAnimationForNewPack(actor) {
  actor.runtime.anim = { name: "idle", frame: 0, row: 0, accMs: 0 };
}

function applyFrame(actor) {
  const element = actor.element;
  const runtime = actor.runtime;
  const state = actor.meta?.states?.[runtime.anim.name];
  if (!element || !state || !state.frame || typeof state.frames !== "number" || !Number.isFinite(state.frames)) return;

  const { w, h } = state.frame;
  const frame = runtime.anim.frame % state.frames;
  const rowIndex = runtime.anim.row || 0;
  element.style.width = `${w}px`;
  element.style.height = `${h}px`;
  element.style.backgroundImage = `url("${sheetUrlFor(actor, runtime.anim.name)}")`;
  const img = actor.images[runtime.anim.name];
  if (img?.naturalWidth && img?.naturalHeight) {
    element.style.backgroundSize = `${img.naturalWidth}px ${img.naturalHeight}px`;
  }
  element.style.backgroundRepeat = "no-repeat";
  element.style.imageRendering = "pixelated";
  element.style.backgroundPosition = `${-(frame * w)}px ${-(rowIndex * h)}px`;
  element.style.transform =
    `translate(${Math.round(runtime.pos.x)}px, ${Math.round(runtime.pos.y)}px) ` +
    "translate(-50%, -50%) " +
    `scale(${visualScale()})`;
  element.style.transformOrigin = "center center";
}

function pickStateBySpeed(actor, now) {
  const runtime = actor.runtime;
  if (runtime.isWandering && runtime.wanderPhase === "sleep") return "sleep";
  if (runtime.isWandering && runtime.wanderPhase === "idle") return "idle";
  if (hasState(actor, "sleep") && !runtime.isWandering && now - POINTER.lastMoveTs > SLEEP_TIMEOUT_MS) return "sleep";
  return runtime.isWalking ? "walk" : "idle";
}

function tickActor(actor, index, dtMs, now) {
  const runtime = actor.runtime;
  computeTarget(actor, index, now);
  const desired = pickStateBySpeed(actor, now);
  if (desired !== runtime.anim.name) {
    if (!runtime.pendingState || runtime.pendingState.name !== desired) {
      runtime.pendingState = { name: desired, queuedAt: now };
    }
    const currentState = actor.meta.states[runtime.anim.name] || actor.meta.states.idle;
    const frames = Number(currentState.frames) || 1;
    const atCycleEnd = runtime.anim.frame >= frames - 1;
    const timedOut = now - runtime.pendingState.queuedAt > 300;
    if (atCycleEnd || timedOut) {
      runtime.anim.name = runtime.pendingState.name;
      runtime.anim.row = pickRowForState(actor, runtime.anim.name, index);
      runtime.pendingState = null;
    }
  } else {
    runtime.pendingState = null;
  }

  const dx = runtime.target.x - runtime.pos.x;
  const dy = runtime.target.y - runtime.pos.y;
  const dist = Math.hypot(dx, dy);
  if (dist > ARRIVE_RADIUS_PX) {
    const baseSpeed = walkSpeedFromConfig();
    const walkSpeed = runtime.isWandering ? MODE.wanderSpeed(baseSpeed) : baseSpeed;
    const speed = dist < SLOW_RADIUS_PX ? walkSpeed * (dist / SLOW_RADIUS_PX) : walkSpeed;
    const moveDtMs = Math.min(dtMs, 50);
    const moveDist = Math.min(dist, speed * (moveDtMs / 1000));
    if (runtime.isWandering) {
      runtime.moveVel.x = dx / dist;
      runtime.moveVel.y = dy / dist;
    }
    runtime.pos.x += (dx / dist) * moveDist;
    runtime.pos.y += (dy / dist) * moveDist;
    runtime.isWalking = true;
  } else {
    runtime.isWalking = false;
  }

  const state = actor.meta.states[runtime.anim.name] || actor.meta.states.idle;
  const fps = Number(state.fps) || 8;
  const frames = Number(state.frames) || 1;
  const msPerFrame = 1000 / fps;
  runtime.anim.accMs += dtMs;
  while (runtime.anim.accMs >= msPerFrame) {
    runtime.anim.accMs -= msPerFrame;
    runtime.anim.frame = (runtime.anim.frame + 1) % frames;
  }
  runtime.anim.row = pickRowForState(actor, runtime.anim.name, index);
}

function teardownInvalidatedContext() {
  window.removeEventListener("mousemove", onMouseMove);
  stopLocalPoll();
  removeActorElements();
  running = false;
}

function loop() {
  let last = performance.now();
  const step = () => {
    if (!isExtensionContextValid()) {
      teardownInvalidatedContext();
      return;
    }
    const now = performance.now();
    const dt = now - last;
    last = now;
    if (ACTORS.length) {
      ACTORS.forEach((actor, index) => tickActor(actor, index, dt, now));
      enforceWanderSeparation();
      applyFrames();
    }
    rafId = requestAnimationFrame(step);
  };
  rafId = requestAnimationFrame(step);
}

function onMouseMove(e) {
  const now = performance.now();
  const dt = Math.max(1, now - (POINTER.lastMouse.t || now));
  const vx = (e.clientX - POINTER.lastMouse.x) * (1000 / dt);
  const vy = (e.clientY - POINTER.lastMouse.y) * (1000 / dt);
  const smooth = 0.2;
  POINTER.velAvg.x = POINTER.velAvg.x * (1 - smooth) + vx * smooth;
  POINTER.velAvg.y = POINTER.velAvg.y * (1 - smooth) + vy * smooth;
  POINTER.speedAvg = Math.hypot(POINTER.velAvg.x, POINTER.velAvg.y);
  POINTER.lastMouse.x = e.clientX;
  POINTER.lastMouse.y = e.clientY;
  POINTER.lastMouse.t = now;
  POINTER.lastMoveTs = now;

  if (STATE.enabled && STATE.wander) {
    ACTORS.forEach((actor) => {
      resetWanderState(actor);
      actor.runtime.isWandering = false;
    });
  }
}

function initializeActor(actor, index, previousActor) {
  const runtime = actor.runtime;
  if (previousActor?.runtime) {
    runtime.pos.x = previousActor.runtime.pos.x;
    runtime.pos.y = previousActor.runtime.pos.y;
    runtime.target.x = previousActor.runtime.target.x;
    runtime.target.y = previousActor.runtime.target.y;
    runtime.offsetDir.x = previousActor.runtime.offsetDir.x;
    runtime.offsetDir.y = previousActor.runtime.offsetDir.y;
  } else {
    const initialX = STATE.enabled ? POINTER.lastMouse.x : window.innerWidth / 2;
    const initialY = STATE.enabled ? POINTER.lastMouse.y : window.innerHeight / 2;
    runtime.pos.x = initialX - index * CONFIG.offset;
    runtime.pos.y = initialY;
    runtime.target.x = runtime.pos.x;
    runtime.target.y = runtime.pos.y;
  }
  resetWanderState(actor);
}

function replaceActors(nextActors) {
  const previousActors = ACTORS.slice();
  removeActorElements();
  ACTORS.length = 0;
  nextActors.forEach((actor, index) => {
    initializeActor(actor, index, previousActors[index]);
    ACTORS.push(actor);
    if (running) createFollower(actor, index);
  });
}

function normalizeStoredRoster(rawRoster, fallbackPack) {
  const fallback = typeof fallbackPack === "string" && fallbackPack.trim() ? fallbackPack : DEFAULT_PACK;
  const entries = Array.isArray(rawRoster)
    ? rawRoster.filter((value) => typeof value === "string" && value.trim()).slice(0, 6)
    : [];
  return entries.length ? entries : [fallback];
}

function activePackKeys() {
  if (STATE.rosterMode === "individual") return [STATE.pack || STATE.packs[0] || DEFAULT_PACK];
  return STATE.packs.length ? STATE.packs : [STATE.pack || DEFAULT_PACK];
}

async function loadActor(packKey) {
  const actor = {
    packKey,
    meta: null,
    images: {},
    element: null,
    runtime: createFollowerRuntime()
  };
  let chosen = null;
  let meta = null;
  let lastError = null;

  for (const candidate of buildPackCandidates(packKey)) {
    try {
      meta = await fetchPackMeta(candidate);
      chosen = candidate;
      break;
    } catch (error) {
      lastError = error;
    }
  }
  if (!chosen || !meta) throw lastError || new Error(`Unable to load pack for key "${packKey}"`);

  actor.packKey = chosen;
  actor.meta = meta;
  resetAnimationForNewPack(actor);
  await ensureImagesLoaded(actor);
  if (chosen !== packKey && packKey === STATE.pack) {
    STATE.pack = chosen;
    try { chrome.storage.sync.set({ vcp1_pack: chosen }); } catch (_) {}
  }
  return actor;
}

async function rebuildActors() {
  const token = ++rebuildToken;
  const keys = activePackKeys();
  const loaded = (await Promise.all(keys.map(async (key) => {
    try {
      return await loadActor(key);
    } catch (error) {
      console.warn(`pack load failed for ${key}`, error);
      return null;
    }
  }))).filter(Boolean);

  if (token !== rebuildToken) return;
  if (!loaded.length && !ACTORS.length) {
    try {
      loaded.push(await loadActor(DEFAULT_PACK));
    } catch (error) {
      console.warn("default pack also failed", error);
    }
  }
  if (!loaded.length) return;
  replaceActors(loaded);
}

function start() {
  if (running || !ACTORS.length) return;
  running = true;
  ACTORS.forEach((actor, index) => {
    initializeActor(actor, index);
    createFollower(actor, index);
  });
  POINTER.lastMoveTs = performance.now();
  window.addEventListener("mousemove", onMouseMove, { passive: true });
  loop();
}

function stop() {
  if (!running) return;
  running = false;
  window.removeEventListener("mousemove", onMouseMove);
  removeActorElements();
  if (rafId) cancelAnimationFrame(rafId);
  rafId = null;
}

function applyState() {
  if (MODE.isActive(STATE.enabled, STATE.wander)) start();
  else stop();
}

// boot
chrome.storage.sync.get(
  ["vcp1_enabled", "vcp1_wander", "vcp1_pack", "vcp1_packs", "vcp1_roster_mode", "vcp1_scale", "vcp1_scale_version", "vcp1_offset", "vcp1_lerp"],
  async (res) => {
    STATE.enabled = !!res.vcp1_enabled;
    STATE.wander = !!res.vcp1_wander;
    STATE.pack = res.vcp1_pack || DEFAULT_PACK;
    STATE.packs = normalizeStoredRoster(res.vcp1_packs, STATE.pack);
    STATE.rosterMode = res.vcp1_roster_mode === "multiple" ? "multiple" : "individual";
    const scale = normalizeStoredScale(res.vcp1_scale, res.vcp1_scale_version);
    applyConfigPatch({ ...res, vcp1_scale: scale });
    if (res.vcp1_scale_version !== SCALE_VERSION) {
      try { chrome.storage.sync.set({ vcp1_scale: scale, vcp1_scale_version: SCALE_VERSION }); } catch (_) {}
    }
    await rebuildActors();
    applyState();
  }
);

// react to popup changes
chrome.storage.onChanged.addListener(async (changes, area) => {
  if (area !== "sync") return;

  if (changes.vcp1_enabled) {
    STATE.enabled = !!changes.vcp1_enabled.newValue;
    if (STATE.enabled && STATE.wander) POINTER.lastMoveTs = performance.now();
    applyState();
  }
  if (changes.vcp1_wander) {
    STATE.wander = !!changes.vcp1_wander.newValue;
    if (STATE.enabled && STATE.wander) POINTER.lastMoveTs = performance.now();
    applyState();
  }

  if (changes.vcp1_packs || changes.vcp1_pack || changes.vcp1_roster_mode) {
    if (changes.vcp1_pack) STATE.pack = changes.vcp1_pack.newValue || DEFAULT_PACK;
    if (changes.vcp1_packs) STATE.packs = normalizeStoredRoster(changes.vcp1_packs.newValue, STATE.pack);
    if (changes.vcp1_roster_mode) {
      STATE.rosterMode = changes.vcp1_roster_mode.newValue === "multiple" ? "multiple" : "individual";
    }
    await rebuildActors();
    applyState();
  }

  if (changes.vcp1_scale || changes.vcp1_offset || changes.vcp1_lerp) {
    applyConfigPatch({
      vcp1_scale: changes.vcp1_scale ? Number(changes.vcp1_scale.newValue) : undefined,
      vcp1_offset: changes.vcp1_offset ? Number(changes.vcp1_offset.newValue) : undefined,
      vcp1_lerp: changes.vcp1_lerp ? Number(changes.vcp1_lerp.newValue) : undefined
    });
  }
});

// listen for live slider updates and drag state from popup.js
chrome.runtime.onMessage.addListener((msg) => {
  if (!msg) return;
  if (msg.type === "vcp1_config" && msg.patch) {
    applyConfigPatch(msg.patch);
    applyFrames();
    return;
  }
  if (msg.type === "vcp1_drag") {
    const on = !!msg.dragging;
    if (on && !LIVE.dragging) {
      LIVE.dragging = true;
      startLocalPoll();
    } else if (!on && LIVE.dragging) {
      LIVE.dragging = false;
      stopLocalPoll();
    }
  }
});

window.addEventListener("beforeunload", () => {
  stopLocalPoll();
  stop();
});
