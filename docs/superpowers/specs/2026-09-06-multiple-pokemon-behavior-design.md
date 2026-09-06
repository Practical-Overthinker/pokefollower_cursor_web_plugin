# Multiple Pokémon Behavior Design

## Goal

Extend the existing six-slot roster so users can choose between one active Pokémon and all assigned Pokémon, while keeping Follow Mode and Wander Mode as the movement choices.

The popup's new control chooses population size. Follow/Wander determines how that population moves.

## User-facing control

Place a compact two-state button under the Pokéball slots, aligned with the left side of the popup and approximately the width of the first three slots. The button cycles between:

- `Individual`
- `Multiple`

Use `Individual` and `Multiple` rather than `Chain`: a chain describes Multiple + Follow, but Multiple + Wander intentionally does not keep the Pokémon in a line.

The button must expose its current value to assistive technology and persist it in `chrome.storage.sync` as `vcp1_roster_mode`. Existing installations default to `individual`.

Clicking an occupied Pokéball still selects that slot for editing. In Multiple mode, selecting a slot does not hide the other active Pokémon. The red `×` still removes the selected extra slot, and empty slots are ignored by the runtime.

## Behavior matrix

| Roster mode | Follow Mode | Wander Mode | Runtime behavior |
| --- | --- | --- | --- |
| Individual | Off | Off | No Pokémon is shown. |
| Individual | On | Off | The selected Pokémon follows the cursor using existing behavior. |
| Individual | Off | On | The selected Pokémon wanders using existing behavior. |
| Individual | On | On | The selected Pokémon follows while the cursor moves, then wanders after the existing idle threshold. |
| Multiple | Off | Off | No Pokémon is shown. |
| Multiple | On | Off | All occupied slots are active in slot order, forming a line behind the cursor. |
| Multiple | Off | On | All occupied slots are active and wander independently in their own directions. |
| Multiple | On | On | The Pokémon form a line while the cursor is active, then break into independent wandering after the cursor becomes idle. |

## Multiple + Follow

- Slot 1 is the leader and follows the cursor.
- Slots 2–6 follow behind in roster order.
- The existing Distance setting controls the spacing between consecutive Pokémon.
- Scale and speed remain global settings.
- Removing a slot immediately compacts the line; later slots take the removed slot's place.
- Switching or editing a slot changes its roster entry but does not change the line order.

The line should be driven by the leader's recent movement path or equivalent trailing targets so each Pokémon follows the one before it naturally rather than independently snapping to the cursor.

## Multiple + Wander

- Every occupied slot gets its own movement state and destination.
- Each Pokémon chooses destinations independently and can enter its own roam, idle, and sleep phases.
- Wander speed remains tied to the existing popup speed setting.
- Independent targets must not all be derived from the same target or timing, so Pokémon are free to move in different directions and pause independently.
- Existing viewport-safe bounds apply to every Pokémon.
- No collision avoidance or obstacle detection is added in this version.

## Multiple + Follow + Wander

Preserve the existing hybrid rule at the population level:

1. While the cursor is moving, the active Pokémon form the ordered Follow line.
2. After the existing cursor-idle threshold, each Pokémon leaves the line and runs its own Wander state.
3. When the cursor moves again, all Pokémon return to the ordered Follow line and smoothly rejoin it.

## Storage and runtime boundaries

- `vcp1_packs` remains the ordered roster.
- `vcp1_pack` remains the selected/legacy-compatible pack value for Individual mode and popup migration.
- `vcp1_roster_mode` stores `individual` or `multiple` and defaults to `individual`.
- `vcp1_enabled` and `vcp1_wander` retain their existing meanings and keys.
- The popup remains responsible for roster editing and mode persistence.
- The content script becomes responsible for rendering one or several followers based on the same stored configuration.

## Accessibility

- The mode control is a real button with an accessible name such as `Roster mode: Individual`.
- Its visible text always states the current mode.
- Its focus state remains visible and it must not rely on color alone to communicate the current value.

## Scope limits

- Maximum six Pokémon.
- No drag-and-drop ordering.
- No per-Pokémon scale, distance, or speed controls.
- No collision or obstacle avoidance.
- No new animation asset or pack schema changes.
- No random roster assignment when opening an empty slot.

## Verification

Verify with focused tests and manual Chrome testing:

- Mode storage defaults to `individual` and persists `multiple`.
- Individual mode preserves the current single-follower behavior.
- Multiple + Follow renders assigned Pokémon in slot order with spacing derived from Distance.
- Multiple + Wander gives each Pokémon independent targets and phases.
- Multiple + Follow + Wander transitions from line to independent wandering and back.
- Empty slots do not spawn followers.
- Removing a slot compacts both the roster and active runtime.
- Switching a slot in Multiple mode edits that entry without hiding the other followers.
- Existing Follow/Wander toggle behavior remains unchanged in Individual mode.
