# Runtime Evidence Policy

## Purpose

Runtime visual validation must be reproducible. A claim such as `the current state is hard to distinguish` is not sufficient by itself; another agent should be able to identify the build, context, and rendered evidence that produced the finding.

This policy defines the minimum evidence needed for runtime approval and rework findings.

## Evidence hierarchy

Use the strongest evidence available for the claim.

### E1 — Rendered capture

A screenshot or rendered frame from the executable target context.

Use for:

- actual-scale readability,
- hierarchy,
- placement,
- overlap,
- clipping,
- compositing,
- contextual style,
- static state differentiation.

For Canvas/WebGL or comparable visual surfaces, E1 is mandatory for visual BLOCKER/MAJOR findings.

### E2 — Frame sequence / transition evidence

Multiple deterministic captures, a frame sequence, or video-equivalent evidence.

Use for:

- animation continuity,
- transition timing,
- anchor jitter,
- state-change clarity,
- camera-dependent visual problems.

Do not infer animation quality from one isolated frame when the failure is temporal.

### E3 — Runtime metadata

Supporting data such as:

- viewport size,
- device class,
- camera state,
- route/scene/level,
- runtime transforms,
- z-order,
- asset/version identifiers,
- build or commit ID.

Metadata supports visual evidence but normally does not replace it.

### E4 — Baseline evidence

Prior approved captures or runtime reports tied to a known build/context.

Use for regression checks.

Baseline evidence must be versioned. Do not compare a current capture against an undocumented screenshot and call the difference a regression.

### E5 — Supplied external capture

A screenshot or recording supplied by the user or another system when the validator cannot execute the runtime itself.

This can support diagnosis, but if the required executable contexts were not directly validated, the final status must remain `partial_validation_only` or `runtime_blocked` as appropriate.

## Evidence manifest

Maintain `evidence-manifest.yaml` with stable capture IDs.

Example:

```yaml
build:
  id: 7f31c2a

captures:
  CAP-001:
    type: screenshot
    context_id: CTX-001
    scene: stage-select
    viewport:
      width: 1920
      height: 1080
    camera: ui-fixed
    game_state: taurus_stage_3_current
    asset_versions:
      stage-star-current: normalized-v5
    path: captures/CAP-001.png
    baseline_id: BASE-013
    notes:
      - captured after scene settled for one frame
```

Do not invent build IDs, paths, timestamps, model data, or capture metadata that were not observed.

## Reproduction record

A MAJOR/BLOCKER runtime finding should identify:

1. build/commit or comparable build identity,
2. context ID,
3. viewport/device class,
4. scene/route/level,
5. camera and relevant game state,
6. deterministic entry steps where possible,
7. capture IDs,
8. expected player-visible outcome,
9. observed outcome.

If a reproduction step is nondeterministic, state that explicitly.

## Capture timing

Do not capture arbitrary frames if timing changes the result.

For dynamic scenes:

- define a stable capture point,
- identify transition start/end when relevant,
- wait for intended layout/render settling where appropriate,
- preserve a frame sequence when the problem is temporal.

Avoid masking a problem by choosing only a favorable frame.

## Actual-scale rule

Runtime-scale evidence is authoritative for readability.

You may also inspect crops or zoomed views for diagnosis, but a zoomed crop cannot prove that an asset is readable at the player's actual scale.

Recommended pairing:

```text
CAP-021-runtime.png   # authoritative context
CAP-021-detail.png    # optional diagnostic crop
```

## Canvas / WebGL rule

For Canvas, WebGL, game-engine render targets, or rasterized scene surfaces:

- do not treat DOM presence as visual correctness,
- do not treat source asset dimensions as rendered-size correctness,
- capture the rendered surface,
- use runtime/layout metadata only as supplemental evidence.

## Baseline policy

A baseline is approved evidence, not merely an older screenshot.

A valid baseline should identify:

```yaml
baseline:
  id: BASE-013
  approved_status: runtime_approved
  build: 12ab39f
  context_id: CTX-001
  capture_id: CAP-108
```

When the design intentionally changes, either:

- update the baseline after approval, or
- record the difference as intentional.

Do not continuously compare against obsolete design truth.

## Semantic regression evidence

Raw image difference may be used as a signal, not as final evidence of failure.

A regression finding should explain the player-relevant semantic change, such as:

- active state is no longer visually dominant,
- player silhouette is partially hidden,
- lock state reads as available,
- UI label collides with the gameplay area,
- camera shift causes a target to leave the readable region.

A harmless texture/noise change is not automatically a regression.

## Evidence sufficiency

### Sufficient for `runtime_approved`

- required executable contexts were exercised,
- visual claims have rendered evidence,
- required state/scene coverage is complete,
- unresolved context risk is below project threshold.

### Sufficient only for `partial_validation_only`

Examples:

- screenshots were supplied but runtime could not be launched,
- desktop was validated but a required mobile viewport was unavailable,
- only one state of a required family was observable,
- animation was judged from static captures only.

### Insufficient / `runtime_blocked`

Examples:

- no rendered output is available,
- the build cannot reach the required state,
- the expected behavior is contradictory or undefined,
- target asset version cannot be confirmed.

## Evidence minimization

Capture enough evidence to prove or disprove the requirement, not an unbounded archive.

Prefer:

- representative high-risk contexts,
- stable capture IDs,
- targeted evidence for each finding,
- baseline reuse.

Avoid taking dozens of near-identical screenshots without a decision purpose.

## Privacy / external references

Do not silently upload runtime captures to unrelated external services. Follow the execution environment's file and privacy rules. Record external evidence URLs only when they are legitimately available and needed for the validation record.
