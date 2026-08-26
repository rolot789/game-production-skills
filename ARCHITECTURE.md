# Architecture

## 1. Two kinds of state

The toolkit separates **design state** from **production state**.

### Design state

```text
GameSpec
ArtStyle
Style Anchors
```

These describe what must exist and how it should look.

### Production state

```text
AssetSpec
GenerationRecord
NormalizationRecord
QCReport
RuntimeReport
```

These describe how a particular production asset was produced and validated.

## 2. Compiler-style pipeline

The toolkit is intentionally compiler-like:

```text
human intent
→ structured semantic spec
→ visual spec
→ asset IR
→ generation job
→ runtime artifact
→ verification
```

Each stage narrows ambiguity.

## 3. Failure routing

A downstream symptom is routed to its root owner:

```text
undefined behavior             → game-spec-builder
undefined/incompatible style   → art-style-builder
wrong asset decomposition      → game-asset-planner
wrong generated visual         → game-asset-generator
processing/canvas/pivot issue  → game-asset-normalizer
incorrect isolated QC          → game-asset-qc
runtime-only integration issue → runtime integration / validator
```

## 4. Dependency-aware invalidation

Upstream revisions invalidate only dependent descendants.

Example:

```text
Gate state model changes
→ Gate specs invalidated
→ Gate generations invalidated
→ Gate normalization invalidated
→ Gate QC invalidated
→ Gate runtime reports invalidated
```

Unrelated character assets stay valid.

## 5. Human checkpoints

Recommended human approval points:

- Game Spec lock
- Art Style lock
- Calibration style anchors
- First P0 gameplay asset family
- Major runtime visual regression
