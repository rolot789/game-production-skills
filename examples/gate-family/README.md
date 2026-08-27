# Gate Family — worked example

A complete pipeline run, from GameSpec through runtime approval, for one three-state asset family. Every hash in here is real, every measurement was produced by the actual tools, and the whole thing is regenerable.

This exists because the toolkit used to ship an `examples/` directory containing an empty state file and a directory listing. That taught nothing. A single worked example is worth more than another thousand lines of policy prose, because it shows what the fields actually look like when they are filled in correctly.

## Verify it

```bash
python3 scripts/validate_project.py examples/gate-family
```

That checks schemas, verifies every recorded `content_hash` against the bytes on disk, confirms QC verdicts are bound to the outputs they claim to have evaluated, and rejects any handoff carrying a specialist-local alias.

## Rebuild it

```bash
python3 examples/gate-family/tools/build_example.py
```

Hand-authored artifacts — `project.yaml`, the GameSpec slice, the ArtStyle slice, the anchor manifest, the constraint ledger — are edited directly. Everything downstream is derived by running the real tools, because derived artifacts carry hashes and a hand-written hash is a lie waiting to be discovered.

## What is here

```text
spec/game-spec.yaml               gameplay meaning: three gate states, all decision-critical
art/art-style.yaml                locked visual rules (at v2 — see below)
art/style-anchor-manifest.yaml    anchors scoped by dimension, with explicit exclusions
art/style-constraint-ledger.yaml  four negative constraints, each with a positive counterpart

assets/asset-manifest.yaml        family index with topology
assets/specs/AST-GATE-*.yaml      three AssetSpecs with real upstream hashes

generation/AST-GATE-*/            candidates, records, candidate index
normalized/AST-GATE-*/            runtime PNGs, normalization records, geometry reports
qc/AST-GATE-*/                    QC reports with measured technical and accessibility blocks
qc/FAM-GATE/                      family summary with verified invariants
engine-integration/web-main/      budget report, import settings, atlas plan
runtime-validation/AST-GATE-*/    runtime reports

.pipeline/game-art-production-state.yaml   orchestration state with active lineage
.pipeline/handoffs/HND-0001.yaml           the rework handoff described below
.pipeline/invalidation-ledger.yaml         what that rework invalidated, and what it did not
```

## The three things worth reading

### 1. State encoded by shape, not hue

All three gate states share an identical frame and differ only in panel height. That is deliberate: `NEG-STATE-004` forbids hue-only encoding for this family, because the GameSpec marks every gate state decision-critical and the project declares a colour-vision baseline.

The QC reports show what that buys — around 43–56 RMS luminance separation between siblings under protanopia simulation, against a floor of 8. A recolour-only family would score near zero on the same measure and no unaided review would notice.

### 2. A finding routed past its symptom

`HND-0001` is the interesting artifact. QC measured a contrast failure on generated assets: 2.41:1 against the chamber floor, below the declared 3.0 floor.

The reflex is to route that to the generator. It would have been wrong, and expensively so — the candidates implemented the locked palette faithfully, so no regeneration obeying that palette could have fixed it. The root owner was `art-style-builder`, because the *palette* could not meet the baseline.

The handoff shows the separation the toolkit is built around:

```text
symptom location:   asset_qc
root owner:         art-style-builder
invalidation scope: FAMILY_SYSTEMIC
change scope:       palette.value_structure only
preserve scope:     hue family, shape language, geometry, texture, lighting, state encoding
```

`preserve_scope` is doing real work there. Without it, "fix the contrast" is an invitation to redesign the palette, and the project loses the warm hue family it had already approved. With it, only value moved — measured 4.28, 3.86, and 3.32 at v2, hue family intact.

### 3. Lineage that can actually be checked

Every record names its inputs by `content_hash`, not just by path. Tamper with any normalized PNG and the validator says so:

```text
normalized/AST-GATE-OPEN/normalization-record.yaml: content_hash mismatch
    recorded f99f385bb857…
    on disk  2a74926e1c61…
```

That is what makes dependency-aware invalidation executable rather than aspirational. A QC approval bound to a hash that no longer exists is detected instead of quietly trusted.

## Honest limitations

- **No image model ran.** `tools/make_candidates.py` draws the gates deterministically. Each generation record says so — `capability: deterministic-script` — because provenance describes what happened, not what would sound better.
- **No game ran.** The runtime reports describe contexts that were not executed against a real build. Their `capture_ids` are placeholders. In a real project, a runtime report without rendered evidence for a BLOCKER or MAJOR finding is rejected by the validator; here there are no such findings.
- **The GameSpec and ArtStyle are slices,** covering only what the gate family depends on. A real spec is much larger.

The parts that are real — schemas, hashes, geometry, contrast, colour-vision separation, budgets — are real because a tool measured them.
