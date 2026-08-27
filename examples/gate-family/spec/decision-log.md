# Decision log — Gate Family

Append-only. Each entry records what was decided, on what basis, and what it constrains downstream. Superseded entries stay; they are not edited.

---

**D-001 — Camera projection: orthographic top-down** · `CONFIRMED` → `LOCKED`

Asked first because it is the least reversible decision in the project: it constrains every asset's geometry, the readability rules, and the entire art direction. Changing it later invalidates essentially all art.

Constrains: every AssetSpec's projection requirement, the geometry anchor, the readability evaluation size.

---

**D-002 — Tile size: 64 px** · `CONFIRMED` → `LOCKED`

Follows from the target display context and the desired number of visible tiles.

Constrains: `runtime.intended_display_size` on every gameplay asset. This is the size QC judges readability at — not the 256 px source canvas.

---

**D-003 — Gate states: closed / transition / open** · `CONFIRMED` → `LOCKED`

`transition` was not in the original concept. It was added because without it the player receives no feedback that powering the switch worked, which makes the puzzle feel broken rather than difficult.

Constrains: family membership (three assets, not two), and the `STATE_TO_TRANSITION` topology.

---

**D-004 — Gate orientation: NOT_APPLICABLE** · `NOT_APPLICABLE`

The level grammar places gates on one axis only.

Recorded explicitly rather than left `UNSEEN`. A future reader seeing an absent orientation field cannot tell whether it was considered and dismissed or simply forgotten — and would likely "fix" it by adding variants no level can reach.

Constrains: variant expansion stops at 3 assets rather than 6.

---

**D-005 — Accessibility baseline: 3.0:1, three CVD modes, non-colour channel required** · `CONFIRMED` → `LOCKED`

Gate state drives a movement decision, and a hue-only distinction fails for roughly one player in twelve.

Written into `project.yaml` rather than only stated here, so that `game-asset-qc` can actually verify it. A baseline no downstream stage can check is not a baseline.

Constrains: `state.encoding_channels` on every gate spec, `NEG-STATE-004`, and the QC accessibility block.

---

**D-006 — Palette raised to v2 after a QC contrast failure** · `CONFIRMED`

QC measured 2.41:1 against the chamber floor against a declared floor of 3.0.

Routed to `art-style-builder`, not to the generator. The candidates had implemented the v1 palette correctly; the palette itself could not meet the baseline, so regeneration could not have fixed it. See `.pipeline/handoffs/HND-0001.yaml`.

The handoff constrained the fix to `palette.value_structure` with `palette.hue_family` preserved, so v2 is brighter rather than different. Measured after: 4.28 / 3.86 / 3.32.

Invalidated: all FAM-GATE generation, normalization, QC, and runtime approvals (`INV-0001`). Preserved: anchors, constraint ledger, spec content.

---

**OQ-001 — "Permanently sealed" gate state?** · `UNRESOLVED`, non-blocking

Would add a fourth family member. Left open because it does not block the current milestone, and inventing it would produce an asset with no defined gameplay meaning — the most expensive kind of guess, since every downstream stage inherits it.
