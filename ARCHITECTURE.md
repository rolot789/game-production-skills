# Architecture

## 1. Two kinds of state

The toolkit separates **design state** from **production state**.

```text
Design state                Production state
────────────                ────────────────
GameSpec                    AssetSpec
ArtStyle                    GenerationRecord
Style Anchors               NormalizationRecord
Constraint Ledger           QCReport
                            BudgetReport
                            RuntimeReport
```

Design state describes what must exist and how it should look. Production state describes how one particular asset was made and verified. Confusing them is how a rendering bug turns into an art-direction meeting.

## 2. Compiler-style pipeline

```text
human intent
→ structured semantic spec        game-spec-builder
→ visual spec                     art-style-builder
→ asset IR                        game-asset-planner
→ generation job                  game-asset-generator
→ runtime artifact                game-asset-normalizer
→ contract verification           game-asset-qc
→ engine packaging                game-engine-integrator
→ contextual verification         runtime-visual-validator
```

Each stage narrows ambiguity, and each one refuses to invent what an earlier stage failed to decide.

## 3. Deterministic work belongs in code

Three stages carry scripts, because their core work is arithmetic:

| Stage | Script | Computes |
|---|---|---|
| normalization | `normalize.py` | alpha bounds, trim, scale, canvas, anchor, pivot, hashes |
| asset QC | `technical_check.py` | dimensions, alpha, clipping, padding, lineage, contrast, colour-vision separation |
| engine integration | `budget_check.py` | file size, atlas dimension, texture memory against declared budgets |

The agent runs the tool and judges the result. It does not re-derive the numbers by eye — a measurement that cannot be reproduced is not evidence, and `content_hash` has to be a real digest for anything downstream to mean anything.

## 4. Single sources of truth

| Concern | Lives in | Never restated in |
|---|---|---|
| stage order, enums, lifecycle transitions, lineage rules, budgets | `contracts/toolkit-contract.yaml` | skill prose |
| symptom → root owner → invalidation scope → revalidation scope | `contracts/routing.yaml` | skill prose |
| the rework envelope | `contracts/rework-handoff-contract.yaml` | skill prose |
| artifact shapes | `contracts/schemas/` | skill prose |

Skill documents explain *how* to apply these and may quote a row for illustration. They do not carry their own copy.

This is not tidiness. The routing table was previously restated in five documents; they drifted, and two incompatible vocabularies for the same five escalation levels shipped simultaneously. `validate_contracts.py` now compares sets rather than grepping for sentences, so that failure mode is caught in CI.

Contract files are mirrored into skill directories by `sync_contracts.py`, because an installed skill is a self-contained directory and cannot reach a repository-root `contracts/`.

## 5. Failure routing

A downstream symptom is routed to its root owner, never to where it was noticed. The full table is `contracts/routing.yaml`; the shape of a decision:

```text
symptom observed:     runtime scene
root owner:           game-asset-normalizer
invalidation scope:   LOCAL_ASSET
revalidation scope:   asset_qc, engine_integration, affected_runtime_contexts
preserved:            generation contract, generated candidate, art style
```

Four separate decisions. Collapsing them is how one bad pivot triggers a family regeneration.

Two symptom classes deliberately have **no** default owner — `CONTEXT_SENSITIVE_ASSET_FAILURE` and `ACCESSIBILITY_FAILURE`. Both have three plausible upstream owners, and auto-routing either one sends the wrong stage into cycles that cannot fix it.

## 6. Dependency-aware invalidation

Upstream revisions invalidate only dependent descendants.

```text
Gate state model changes
→ Gate specs invalidated
→ Gate generations invalidated
→ Gate normalization invalidated
→ Gate QC invalidated
→ Gate runtime reports invalidated

Character assets stay valid.
```

This only works because identity is computable. Every record names its inputs by `content_hash`, and effective input equivalence is proven by matching digests — never by visual similarity, file size, or timestamps. `validate_project.py` verifies every recorded hash against the bytes on disk.

## 7. Lifecycle transitions are enforced

`toolkit-contract.yaml` → `lifecycle_transitions` lists, for all 14 asset states, the states each may move to and the evidence that authorizes each move. The orchestrator rejects anything not in the table.

A promoting status is not sufficient on its own: `NORMALIZED → QC_APPROVED` also requires the QC report's `evaluated.normalized_output.content_hash` to equal the active output. A green report bound to a stale hash is not evidence about the current asset.

## 8. Profiles

`full` runs every stage. `lite` runs six, inlines per-asset specs into the manifest, and stops at `QC_APPROVED`.

Lite exists because artifact count is a real adoption cost and eight stages is the wrong shape for a jam. It relaxes file layout — never the locked-versus-inferred distinction, scoped anchor roles, negative constraints with positive counterparts, canonical rework scopes, or hash lineage. Those are what make rework survivable, and they cost one field per record.

## 9. Human checkpoints

- Game Spec lock
- Art Style lock
- Calibration style anchors
- First P0 gameplay asset family
- Broad `L4_DIRECTION_RESET`
- Systemic runtime fixes that reopen locked upstream truth

Routine routing that the contracts already determine does not interrupt anyone.

## 10. What is not yet measured

The routing table, handoff envelopes, and lineage negative cases are executable evals (`scripts/run_evals.py`). Skill triggering and gate-holding under pressure need a model, and `scripts/run_model_evals.py` runs them against one:

```bash
python3 scripts/run_model_evals.py --backend anthropic
python3 scripts/run_model_evals.py --backend command --command "<your cli>"
```

Scoring is deterministic — each case asks for a small JSON object and compares fields, because a harness that greps prose for encouraging words reports a score the skills did not earn. Without a backend the harness exits `2` and says `SKIPPED`, never `PASS`.

CI cannot run a model, so it runs the next best thing: `run_evals.py` self-tests the harness against two fixtures, one matching every expectation and one with three deliberately wrong answers. A scorer that would accept the wrong run fails the build.

What is still true: **nobody has published a score.** The harness exists, its scoring is verified, and the claim that the trigger-shaped descriptions improve skill selection remains a hypothesis until someone runs it with a model and reports the number.
