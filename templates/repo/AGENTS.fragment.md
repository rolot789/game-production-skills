## Game Production Toolkit

Use `.agents/skills/game-art-production-orchestrator` as the top-level production router.

Rules:

- Treat locked GameSpec and ArtStyle as source of truth.
- Never silently convert inferred requirements into confirmed ones.
- Do not bypass stage readiness gates.
- Preserve generation and validation provenance.
- Route failures to root owner instead of patching symptoms downstream.
- Invalidate only dependency-affected descendants.
- Do not promote an asset to SHIPPABLE until runtime visual validation passes.
