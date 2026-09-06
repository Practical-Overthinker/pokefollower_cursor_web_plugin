export const MAX_ROSTER_SIZE = 6;

function isPackId(value) {
  return typeof value === "string" && value.trim().length > 0;
}

export function normalizeRoster(rawRoster, fallbackPack) {
  const entries = Array.isArray(rawRoster)
    ? rawRoster.filter(isPackId).slice(0, MAX_ROSTER_SIZE)
    : [];
  return entries.length ? entries : [fallbackPack];
}

export function addRosterSlot(roster, pack) {
  if (!Array.isArray(roster) || roster.length >= MAX_ROSTER_SIZE) return roster;
  if (!isPackId(pack)) return roster;
  return [...roster, pack];
}

export function setRosterPack(roster, index, pack) {
  if (!Array.isArray(roster) || !Number.isInteger(index) || index < 0 || index >= roster.length) {
    return roster;
  }
  if (!isPackId(pack)) return roster;
  const next = roster.slice();
  next[index] = pack;
  return next;
}

export function removeRosterSlot(roster, index) {
  if (!Array.isArray(roster) || !Number.isInteger(index) || index <= 0 || index >= roster.length) {
    return roster;
  }
  return roster.filter((_, entryIndex) => entryIndex !== index);
}

export function selectedIndexAfterRemoval(index) {
  return Math.max(0, index - 1);
}
