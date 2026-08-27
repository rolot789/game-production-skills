# Evals

Nobody knows whether this toolkit improves outcomes. That is the honest state of it, and it is the reason to stop adding policy prose and start measuring.

These cases define what "working" means, in a form a model harness can run.

## What is measured

| Suite | Question | Executable here? |
|---|---|---|
| `triggering` | does the right skill fire for a real user utterance? | no — needs a model |
| `routing` | does a symptom reach its root owner? | **yes** — deterministic against `contracts/routing.yaml` |
| `gates` | does the agent refuse to promote without evidence? | no — needs a model |
| `lineage` | are hashes and versions recorded, and stale approvals rejected? | partly — the negative cases run |
| `handoff` | do routed handoffs use the canonical envelope? | **yes** — validated against the schema |

## Running

```bash
python3 scripts/run_evals.py
```

That executes every case marked `executable: true` and reports pass/fail. Non-executable cases are checked for structural validity — that they name a real skill, a real reason code, a real lifecycle state — so the suite cannot rot into referencing things that no longer exist.

To run against a model harness, feed each `triggering` and `gates` case's `input` to the agent with the skills installed and score against `expect`. The case format is deliberately harness-agnostic: no assumption about which runner executes it.

## Why these five

Each targets a failure this toolkit has actually exhibited or is structurally prone to:

- **triggering** — nine skills share the vocabulary `locked`, `style`, `asset`, `runtime`, `contract`. Selection is by description match, so overlap is a real risk and the descriptions were rewritten to be trigger-shaped. That rewrite is a hypothesis; these cases test it.
- **routing** — the routing table was duplicated across five documents and drifted. It is now single-source, and these cases pin the mapping so a future edit that changes an owner is visible.
- **gates** — the pipeline's core promise is that partial evidence never promotes. It is worth checking that an agent under mild pressure still refuses.
- **lineage** — `content_hash` discipline is what makes invalidation executable. The negative cases confirm the validator rejects what it should.
- **handoff** — three competing field vocabularies existed at once. The schema now forbids the aliases; these cases confirm it.

## Adding a case

```yaml
id: TRG-010
suite: triggering
executable: false
input: "the gate sprites are all different sizes"
expect:
  skill: game-asset-normalizer
  not_skills: [game-asset-generator, game-asset-qc]
rationale: >-
  Size inconsistency across a family is a normalization concern. Routing it to
  the generator produces regenerations that cannot fix a mechanical problem.
```

Keep `rationale` — a case without a stated reason becomes unmaintainable the first time it fails and nobody remembers what it was protecting.
