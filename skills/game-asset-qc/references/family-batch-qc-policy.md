# Family / Batch QC Policy

## Goal

Evaluate related assets as a coherent production family while preserving local approvals whenever only one derivative fails.

## Canonical-first order

For families with a canonical parent:

1. validate canonical identity/style/geometry first,
2. validate representative derivatives,
3. validate remaining states/directions comparatively.

If the canonical parent fails a family-wide invariant, block approval of descendants that depend on that invariant.

## Family invariants

Common invariants include:

- identity-bearing features,
- base proportions/silhouette,
- camera/projection,
- scale convention,
- palette/material family,
- contour/texture behavior,
- shared geometry,
- pivot/anchor convention when visible/verifiable.

A derivative may intentionally change only declared variant dimensions.

## Variant-delta verification

For every derivative, resolve:

```text
Must Preserve
Must Change
May Vary
Must Not Introduce
```

Example:

```yaml
must_preserve:
  - character_identity
  - body_proportion
  - suit_palette
  - camera
must_change:
  - facing_direction
may_vary:
  - secondary_fold_shape
must_not_introduce:
  - new_accessories
```

QC should fail changes outside the allowed delta when they materially break the family contract.

## Local vs systemic invalidation

- one direction has wrong paw placement but identity/style pass → local derivative rework only,
- all directions have different helmet proportions → canonical/family contract failure,
- all assets gain excess gloss → likely systemic generator/style constraint issue,
- one normalized frame is clipped → local normalizer rework.

Do not invalidate an entire family when evidence supports only a local defect.

## Batch summary

For production batches, optionally emit `family-qc-summary.yaml` with:

```yaml
family_id:
canonical_asset:
family_contract_version:
status:
approved_members: []
rework_members: []
blocked_members: []
systemic_findings: []
local_findings: []
```

## State readability

Where states encode gameplay information, compare them side-by-side at intended display size. State differences should be strong enough to decode while preserving family identity.

An asset can be individually attractive and still fail if two gameplay states cannot be reliably distinguished.
