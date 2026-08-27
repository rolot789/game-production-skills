# Contract Verification Policy

## Goal

Evaluate a normalized asset against explicit production truth without collapsing all visual judgment into subjective taste.

## Source precedence

When sources overlap, use this order unless a project-specific override is explicit:

1. AssetSpec semantic/runtime requirements
2. locked ArtStyle global rules
3. locked category/family overrides
4. approved scoped anchors
5. active style constraints
6. generation contract and selected-candidate record
7. normalization record

A lower source cannot silently override a higher locked source.

## Applicability resolution

Before visual comparison, determine which rules apply to the current asset.

For every candidate rule/anchor/constraint record:

- source ID/version,
- scope,
- governed dimension,
- current asset category/family/state,
- applicability result.

Never fail an asset against an anchor that does not govern the failed dimension.

## Verification result vocabulary

Use:

- `PASS`
- `FAIL`
- `NOT_APPLICABLE`
- `INSUFFICIENT_EVIDENCE`
- `CONTRACT_CONFLICT`

`INSUFFICIENT_EVIDENCE` is not a pass. If the unresolved evidence is production-critical, status becomes blocked.

## Positive-rule verification

Translate prose style rules into observable properties before judging. Examples:

- `hand-drawn contour` → controlled contour irregularity, non-mechanical curvature, readable silhouette,
- `restrained texture` → texture remains subordinate to shape/state information,
- `limited palette` → no unauthorized hue/value expansion that changes family identity,
- `simple readable forms` → no semantically useless micro-detail at intended display size.

Do not create new style requirements during verification.

## Negative-rule verification

For every active constraint:

1. identify its type,
2. resolve scope,
3. identify observable violation criteria,
4. compare at intended scale,
5. record evidence,
6. map to severity using production impact.

`HARD_FORBIDDEN` does not automatically mean BLOCKER if the ledger explicitly assigns another severity, but locked hard prohibitions should never be silently ignored.

## Anchor verification

An approved anchor is dimension-scoped evidence, not a full-image target unless explicitly declared as a full style/identity anchor.

Examples:

- `line_anchor` checks contour/line behavior only,
- `palette_anchor` checks palette/value family only,
- `geometry_anchor` checks shape/proportion/structural relationships,
- `identity_anchor` checks stable identity-bearing features,
- `ui_anchor` may govern UI-specific shape/texture/hierarchy fields defined in the manifest.

Record `governed_dimensions` in every anchor comparison.

## Runtime-size verification

Perform a visual check at the intended runtime footprint whenever known. Zoom inspection is useful for artifacts but cannot substitute for runtime-size readability.

A detail may be technically clean at 512 px but fail at 32 px because it collapses state distinction or creates noise.

## Version binding

QC reports must record upstream artifact versions/IDs used for evaluation. If a locked rule, anchor, AssetSpec, or normalization policy later changes, approval should be invalidated only when dependency mapping shows the changed field affects this asset.
