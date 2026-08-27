## Game Production Toolkit

Use `.agents/skills/game-art-production-orchestrator` as the top-level production router.

Rules:

- Treat locked GameSpec and ArtStyle as source of truth.
- Resolve every artifact path through `project.yaml` — including `game-spec.yaml` and `art-style.yaml`.
- Never silently convert inferred requirements into confirmed ones.
- Do not bypass stage readiness gates.
- Route failures to the root owner in `contracts/routing.yaml` instead of patching symptoms downstream.
- Invalidate only dependency-affected descendants.
- Run the deterministic tool before judging its stage: `normalize.py` for normalization, `technical_check.py` for QC, `budget_check.py` for engine integration.
- Record `version` and `content_hash` on every artifact a promotion depends on. `unknown` is not a lineage value.
- Do not promote an asset to SHIPPABLE until runtime visual validation passes for that exact lineage.

Validate the project at any time:

```bash
python3 scripts/validate_project.py .
```
