# Multi-Pokémon Switcher Design

## Goal

Let users save up to six Pokémon in the popup and switch between them without making an occupied slot ambiguous or accidentally deleting it. This first slice is the roster and switcher only; runtime chaining is deliberately kept separate for a later decision.

## User-facing behavior

- The popup shows six circular slots in one row beneath the `PokeFollower v5.0` label.
- Slot 1 starts occupied by the current Pokémon. The remaining slots are black empty circles.
- An occupied Pokéball selects that slot and loads its Pokémon into the existing picker.
- An empty black circle creates the next slot, selects it, and opens it with Bulbasaur as the predictable starting Pokémon. The user can then cycle or search for another Pokémon.
- The selected slot has a visible highlight.
- Clicking an occupied Pokéball never removes it.
- Slots after the first can be removed only through a separate, very small control above the selected Pokéball:
  - red circular background;
  - black outline;
  - black `×` glyph;
  - shown only for selected slots 2–6;
  - distinct from the main Pokéball click target.
- Removing a slot shifts later Pokémon left so occupied slots stay contiguous and empty circles remain at the end. Slot 1 cannot be removed.

## State model

Keep the roster separate from the selected slot and from runtime display behavior:

```text
roster: [packId, ...]   // one to six entries
selectedSlot: number    // zero-based index
displayMode: "switch" | "chain"  // future runtime decision
```

Persist the roster in `chrome.storage.sync`. Preserve the existing single-Pokémon setting as the migration source: an existing `vcp1_pack` becomes the first roster entry, and new installations start with the existing Bulbasaur default.

The current picker remains the editor for whichever slot is selected. Changing the picker updates only that roster entry and keeps the selected slot active.

## Runtime scope

This slice implements switcher semantics: only the selected Pokémon is the active follower. The roster data and slot UI must not assume that only one follower can ever be rendered, so a later chain mode can render all entries without redesigning slot management.

Do not add a chain toggle or multi-follower movement behavior in this slice.

## Accessibility and interaction details

- Each slot is a real button with an accessible name such as `Pokémon slot 2, 005 Charmeleon` or `Empty Pokémon slot 3`.
- The selected slot exposes selected state to assistive technology.
- The remove control has an explicit label such as `Remove Pokémon from slot 2`.
- The remove control is positioned above its Pokéball and is small enough not to overlap neighboring slot icons.
- Removing a selected slot selects the previous remaining slot, or slot 1 when no previous slot exists.

## Scope limits

- No automatic chain rendering yet.
- No random assignment for new slots; predictable Bulbasaur initialization is enough for the first test.
- No drag-and-drop reordering.
- No per-slot settings; scale, distance, and speed remain global.

## Verification

Verify the popup manually and with focused tests for:

- Existing single-Pokémon installations migrating to a one-entry roster.
- Six slots rendering with one occupied slot and five empty slots.
- Selecting occupied slots without changing roster length.
- Opening an empty slot and adding a Pokémon.
- Removing slots 2–6 through the red `×` badge.
- Slot 1 having no remove control.
- Removing a middle slot compacting later entries.
- Roster persistence and reload.
- Only the selected slot remaining active in this first switcher slice.
