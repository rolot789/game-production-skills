# Changelog

Versions follow Semantic Versioning. Before 1.0, a minor bump may carry breaking changes.

## 0.2.0

Contract **v2 → v3**. Breaking. Existing projects need the migration below.

An audit of all 8 skills (31 documents, 6,716 lines) found 19 defects, 5 of which broke real installs. All 19 are fixed, each with a check that prevents recurrence.

### Fixed — these broke installed projects

- **Installed skills referenced contract files that were never shipped.** Four `SKILL.md` files pointed at `contracts/rework-handoff-contract.yaml` eight times; the installer only copied `skills/`, so every one of those references was dangling in a real install. Contracts and schemas are now mirrored into each skill's `references/` directory.
- **`npx` users could not create `project.yaml`,** which six skills resolve artifact paths through. `bootstrap_project.py` was never in `package.json` `files`. Adds the `init` command.
- **`game-spec-builder` and `art-style-builder` did not know about `project.yaml`** while every downstream stage resolved through it. The pipeline split silently between stages 2 and 3 — the first two stages wrote to repository-root filenames and everything after looked in `spec/` and `art/`.
- **All five `G0`–`G4` escalation levels existed under two incompatible names** — one set in the contract and skill documents, another in the policy file those documents point at.
- **Two policy documents specified non-canonical rework field names** against the contract they were meant to implement.

### Added

- **`contracts/schemas/`** — 11 JSON Schemas, plus `scripts/validate_project.py`, which verifies recorded `content_hash` values against the bytes on disk, binds QC verdicts to the outputs they claim to have evaluated, and rejects specialist-local aliases and unknown reason codes. Uses a dependency-free subset validator, so the npm package keeps zero runtime dependencies.
- **Deterministic scripts** for the three stages whose work is arithmetic: `normalize.py` (geometry, hashing), `technical_check.py` (conformance, contrast, colour-vision separation), `budget_check.py` (texture memory, atlas dimensions, file size).
- **`contracts/routing.yaml`** — single source of truth for failure routing: 20 symptom classes mapped to a root owner, an invalidation scope, and a revalidation scope.
- **`game-engine-integrator`** — an eighth stage between QC and runtime validation, covering atlas packing, import settings derived from recorded pivots, and measured performance budgets.
- **`examples/gate-family`** — a complete run from GameSpec to runtime report. Every hash and measurement is real, and `tools/build_example.py` rebuilds the derived layer byte-deterministically.
- **Lifecycle transitions** — 14 states with a declared, enforceable transition graph; every transition names the evidence that authorizes it.
- **`lite` / `full` profiles.** `lite` runs six stages with three artifacts and a `QC_APPROVED` ceiling; it relaxes file count, never lineage discipline.
- **Generation budget** — candidate, retry, and same-level repeat caps, symmetric with the existing reference-search budget.
- **Accessibility verification** — the baseline GameSpec declares is now checked downstream (contrast, colour-vision separability, non-colour channel) instead of merely stated.
- **`evals/`** — 24 executable cases (routing, handoff, lineage) and 21 specified for a model harness.
- **Reference policies** for the four skills that had none, including MRAU decomposition and geometry semantics.
- **Living-artist boundary policy** for reference anchoring.
- **`scripts/test_install.py`** — installs into a temporary project and resolves every path the installed documents point at. This is the check that would have caught the shipped install defect.

### Changed

- `validate_contracts.py` rewritten. It previously asserted that specific English sentences appeared in specific files — coupling prose to CI while proving nothing, and excluding the exact two skills that had the path-registry defect. It now compares sets and resolves references across 15 check groups.
- Skill descriptions rewritten as trigger conditions (`Use when …`) with explicit boundaries naming the sibling skill that owns the adjacent case.
- `version` and `content_hash` are required rather than "when available"; sha256 and the equivalence rule are defined.
- README, ARCHITECTURE, QUICKSTART, and CONTRIBUTING rewritten.
- `examples/minimal-project` removed, replaced by `examples/gate-family`.

### Migration from 0.1.x

No asset regeneration is required. The changes are to record shape, not to asset content.

**1. Reinstall the skills.** Installed skills now carry their contracts and schemas inside `references/`, so a stale install still has the dangling paths.

```bash
npx game-production-skills install --force
```

**2. Update `project.yaml`.**

```yaml
version: 3                        # was 2

profile: full                     # new, optional; full is the default

paths:
  engine_integration: engine-integration/   # new, required
```

Optionally add the `engine`, `budgets`, and `accessibility` blocks — see `templates/project/project.yaml`. `budgets` is required only if you run the engine integration stage, where an undeclared budget produces `integration_blocked` rather than a silent pass.

**3. Update `.pipeline/game-art-production-state.yaml`.**

```yaml
version: 3                        # was 2

stages:
  # ... after asset_qc, before runtime_validation:
  engine_integration:
    skill: game-engine-integrator
    status: NOT_STARTED
    readiness: null
    artifacts: []
```

**4. Convert lineage fields.** Records that carried `hash:` or the value `unknown` need real digests:

```yaml
# before
asset_spec:
  path: assets/specs/AST-001.yaml
  version: v3
  hash: unknown

# after
asset_spec:
  path: assets/specs/AST-001.yaml
  version: v3
  content_hash: <sha256sum of that exact file>
```

**5. Find everything that still needs attention.**

```bash
npx game-production-skills validate
```

It reports every schema violation, every hash mismatch, and every QC verdict bound to an output that has since changed. Work the list until it passes.

**Two behaviour changes worth knowing about**

- A QC report whose `evaluated.normalized_output.content_hash` does not match the current normalized output no longer counts as an approval for that asset. If a project has been regenerating assets without re-running QC, the validator will now say so.
- A runtime report claiming approval while `build.executable` is `false`, or while a `risk: high` context is untested, is rejected. Both were previously possible to record.

## 0.1.0

Initial release: eight skills, contract v2, prose contracts.
