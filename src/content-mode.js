(() => {
  const IDLE_DELAY_MS = 3000;

  const finite = (value, fallback = 0) =>
    Number.isFinite(Number(value)) ? Number(value) : fallback;

  function isActive(followMode, wanderMode) {
    return !!followMode || !!wanderMode;
  }

  function shouldFollow({
    followMode,
    wanderMode,
    lastMoveTs,
    now,
    idleDelayMs = IDLE_DELAY_MS
  }) {
    if (!followMode) return false;
    if (!wanderMode) return true;
    return now - lastMoveTs < finite(idleDelayMs, IDLE_DELAY_MS);
  }

  function getWanderBounds({
    viewportWidth,
    viewportHeight,
    spriteWidth,
    spriteHeight,
    scale = 1,
    edgeMargin = 12
  }) {
    const width = Math.max(0, finite(viewportWidth));
    const height = Math.max(0, finite(viewportHeight));
    const safeScale = Math.max(0, finite(scale, 1));
    const margin = Math.max(0, finite(edgeMargin));
    const xInset = Math.min(width / 2, (Math.max(0, finite(spriteWidth)) * safeScale) / 2 + margin);
    const yInset = Math.min(height / 2, (Math.max(0, finite(spriteHeight)) * safeScale) / 2 + margin);

    return {
      minX: xInset,
      maxX: width - xInset,
      minY: yInset,
      maxY: height - yInset
    };
  }

  function isWithinBounds(point, bounds) {
    return !!point &&
      point.x >= bounds.minX && point.x <= bounds.maxX &&
      point.y >= bounds.minY && point.y <= bounds.maxY;
  }

  function randomBetween(min, max, random = Math.random) {
    const low = finite(min);
    const high = Math.max(low, finite(max, low));
    const roll = Math.min(1, Math.max(0, finite(random())));
    return low + (high - low) * roll;
  }

  function wanderSpeed(baseSpeed) {
    return Math.max(0, finite(baseSpeed)) * 0.5;
  }

  function shouldSleepAfterWander({
    hasSleep,
    destinations,
    randomValue,
    minDestinations = 3,
    chance = 0.35
  }) {
    return !!hasSleep && destinations >= minDestinations && finite(randomValue) < chance;
  }

  function pickWanderTarget(bounds, currentTarget, random = Math.random) {
    const nextRandom = typeof random === "function" ? random : Math.random;
    const xSpan = Math.max(0, bounds.maxX - bounds.minX);
    const ySpan = Math.max(0, bounds.maxY - bounds.minY);
    const normalize = (value) => Math.min(1, Math.max(0, finite(value)));
    const target = {
      x: bounds.minX + xSpan * normalize(nextRandom()),
      y: bounds.minY + ySpan * normalize(nextRandom())
    };

    if (currentTarget && target.x === currentTarget.x && target.y === currentTarget.y) {
      if (xSpan > 0) target.x = target.x === bounds.minX ? bounds.maxX : bounds.minX;
      else if (ySpan > 0) target.y = target.y === bounds.minY ? bounds.maxY : bounds.minY;
    }

    return target;
  }

  function pickNearbyWanderTarget(bounds, origin, previousTarget, maxDistance = 220, random = Math.random) {
    const nextRandom = typeof random === "function" ? random : Math.random;
    const originX = Math.min(bounds.maxX, Math.max(bounds.minX, finite(origin?.x, (bounds.minX + bounds.maxX) / 2)));
    const originY = Math.min(bounds.maxY, Math.max(bounds.minY, finite(origin?.y, (bounds.minY + bounds.maxY) / 2)));
    const angle = randomBetween(0, Math.PI * 2, nextRandom);
    const distance = randomBetween(0, maxDistance, nextRandom);
    const candidate = {
      x: originX + Math.cos(angle) * distance,
      y: originY + Math.sin(angle) * distance
    };
    const target = {
      x: Math.min(bounds.maxX, Math.max(bounds.minX, candidate.x)),
      y: Math.min(bounds.maxY, Math.max(bounds.minY, candidate.y))
    };

    if (target.x === previousTarget?.x && target.y === previousTarget?.y) {
      return pickWanderTarget(bounds, previousTarget, nextRandom);
    }
    return target;
  }

  globalThis.__vcp1Mode = {
    IDLE_DELAY_MS,
    isActive,
    shouldFollow,
    getWanderBounds,
    isWithinBounds,
    pickWanderTarget,
    randomBetween,
    wanderSpeed,
    shouldSleepAfterWander,
    pickNearbyWanderTarget
  };
})();
