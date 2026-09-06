# Wander Mode Design

## Goal

Add an optional autonomous movement mode without changing the existing cursor-following behavior for current users.

## User-facing behavior

The popup will expose two independent toggles:

| Follow Mode | Wander Mode | Behavior |
| --- | --- | --- |
| Off | Off | Pokémon is hidden. |
| On | Off | Pokémon follows the cursor using the existing movement behavior. |
| Off | On | Pokémon appears and wanders around the visible page. |
| On | On | Pokémon follows the cursor while it moves, then wanders after the cursor has been still briefly. |

The existing `vcp1_enabled` setting remains the stored value for Follow Mode so existing installations keep their current state. Wander Mode adds `vcp1_wander` and defaults to `false`.

## Hybrid mode

When both toggles are on, cursor movement has priority:

1. Cursor movement immediately returns the Pokémon to Follow Mode.
2. After approximately three seconds without cursor movement, the Pokémon enters Wander Mode.
3. It selects a random destination inside a viewport-safe rectangle, walks there using the existing speed setting, pauses briefly, and selects another destination.
4. Moving the cursor again cancels the current wander target and returns the Pokémon to the cursor target.

This keeps the product's core identity intact while making the second toggle useful rather than silently overriding Follow Mode.

## Runtime design

- Keep one follower element and one animation loop.
- Change the spawn condition to `followMode || wanderMode`.
- Split target selection into follow and wander paths; the existing movement, animation, scale, and offset logic remains shared.
- Store wander state only in runtime memory: current wander target, next allowed wander time, and whether the pointer is currently considered active.
- Keep wander destinations inside the viewport with a conservative edge margin based on the follower's scaled dimensions.
- Recalculate bounds on resize and avoid choosing the same destination repeatedly.
- Use the existing walk speed setting for travel; use a short randomized pause at destinations instead of adding another popup control in the first version.

## Popup changes

- Rename the current visible label from `Enable Follower` to `Follow Mode`.
- Add a matching `Wander Mode` toggle.
- Persist each toggle independently through `chrome.storage.sync`.
- Keep both toggles off/on states clear to keyboard and screen-reader users.

## Scope limits

- No multi-Pokémon chaining.
- No new animation assets or pack schema changes.
- No wandering timer controls in the first version.
- No page-content collision or obstacle detection; the first version uses viewport bounds only.

## Verification

Add focused tests for:

- The four toggle combinations and spawn decision.
- Wander destinations staying within safe viewport bounds.
- Hybrid mode returning to Follow Mode when pointer movement resumes.
- Existing Follow Mode behavior remaining unchanged when Wander Mode is off.

Manually verify the feature in Chrome on a normal webpage, including toggling each mode independently, enabling both, resizing the viewport, switching Pokémon, and disabling both modes.
