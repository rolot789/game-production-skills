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

## Skill changes

When changing a skill:

1. Keep `SKILL.md` as the authoritative entry point.
2. Update templates or reference files when the contract changes.
3. Update validators/examples when schemas change.
4. Run the toolkit doctor and package checks before merge.

## Release

Versions follow Semantic Versioning.

- patch: fixes and non-breaking wording/validation changes
- minor: new skills or backward-compatible capabilities
- major: breaking skill contracts, CLI behavior, or package layout
