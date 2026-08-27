# Contributing

## Branches

Create focused branches from `main`:

- `feat/<topic>` for new capabilities
- `fix/<topic>` for bug fixes
- `docs/<topic>` for documentation
- `chore/<topic>` for maintenance and release work

Do not push feature work directly to `main`.

## Commits

Use Conventional Commits:

```text
feat: add a new skill or capability
fix: correct broken behavior
docs: documentation-only change
refactor: internal change without behavior change
test: add or adjust validation
chore: tooling, packaging, release, or maintenance
```

Keep commits scoped and independently understandable.

## Pull requests

Every pull request should include:

- what changed
- why it changed
- affected skills / contracts
- validation performed
- whether the change invalidates downstream examples or generated artifacts

Prefer squash merge so `main` remains a concise release-oriented history.

## Before you push

```bash
python3 scripts/doctor.py .
python3 scripts/sync_contracts.py --check
python3 scripts/validate_contracts.py
python3 scripts/test_install.py
python3 examples/gate-family/tools/build_example.py && git diff --exit-code examples/gate-family
python3 scripts/validate_project.py examples/gate-family
python3 scripts/run_evals.py
npm run check && npm run pack:check
```

CI runs exactly this.

## Skill changes

1. `SKILL.md` is the entry point. Its `description` must start with a trigger condition — `Use when …` — followed by what the skill does and which sibling handles the adjacent case. Nine skills share a vocabulary, and selection happens by description match; a capability statement without a trigger competes with its neighbours for every request. `validate_contracts.py` enforces the `Use when` requirement.
2. **Do not restate a contract in prose.** Stage order, enums, lifecycle transitions, routing, and the rework envelope live in `contracts/` and are referenced, not copied. This rule exists because the routing table was once duplicated across five documents, drifted, and shipped two incompatible names for the same five escalation levels.
3. Any relative path a skill document names must resolve inside the skill directory. Installed skills are self-contained and cannot reach a repository-root `contracts/`.
4. If a skill needs to read a contract, add it to `contracts/mirror-manifest.yaml` and run `python3 scripts/sync_contracts.py`. Never hand-edit a file under `skills/*/references/` that carries the generated-mirror header.

## Contract changes

1. Edit the source in `contracts/`, then re-run `sync_contracts.py`.
2. Bump `version` consistently — the contract, both profiles, the routing and rework contracts, the mirror manifest, the templates, and the example. `validate_contracts.py` checks the alignment.
3. Adding a lifecycle state means adding its transitions. A state no transition can reach is a validator failure.
4. Adding a symptom class means giving it a root owner (or explicit candidates), an invalidation scope, and a revalidation scope, all resolvable.

## Schema changes

1. Schemas are JSON Schema, validated by the dependency-free subset validator in `scripts/lib/minischema.py`.
2. If a schema needs a keyword the validator does not implement, extend the validator — do not add the keyword and let it be silently ignored. `validate_contracts.py` fails on unsupported keywords for exactly that reason.
3. Update `examples/gate-family` and re-run its build script; the example is a schema fixture as well as documentation.

## Adding deterministic work

If a stage's work is arithmetic, it belongs in a script under `skills/<skill>/scripts/`, declared as that stage's `deterministic_tool` in the contract, and invoked from the SKILL.md. The agent reads the output; it does not re-derive the numbers.

## Evals

Behavioural changes should come with a case in `evals/cases/`. Routing, handoff, and lineage cases execute; triggering and gate cases are specifications for a model harness. Every case carries a `rationale` — a case without a stated reason becomes unmaintainable the first time it fails.

## Release

Versions follow Semantic Versioning.

- patch: fixes and non-breaking wording/validation changes
- minor: new skills or backward-compatible capabilities
- major: breaking skill contracts, CLI behavior, or package layout
