#!/usr/bin/env python3
"""Run the eval suites that need a model, against whatever model you have.

`run_evals.py` runs everything a script can decide: routing rows, handoff
schemas, lineage negatives. Two suites it cannot run are the two that matter
most for a skill toolkit, because they measure the skills rather than the
contracts:

  triggering  does a real utterance reach the right skill, and not its neighbour
  gates       does the refusal hold when someone applies deadline pressure

Both were specified and left unrun, which made "the rewritten descriptions
improve skill selection" a hypothesis rather than a result. This harness makes
them runnable without pinning the repository to one provider.

    python3 scripts/run_model_evals.py --backend anthropic
    python3 scripts/run_model_evals.py --backend command --command "llm -m gpt-4o"
    python3 scripts/run_model_evals.py --backend stub --fixture evals/fixtures/self-test.yaml

Scoring is deterministic. Every case asks the model for a small JSON object and
compares fields, rather than grepping prose for encouraging words - a keyword
that happens to appear is not a passing answer, and a harness that accepts one
would report a score the skills did not earn.

Exit 0 when every scored expectation held, 1 otherwise, 2 when no backend is
available (which is a skip, not a pass).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request
import yaml

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"
SKILLS = ROOT / "skills"

TRIGGERING_PROMPT = """You are choosing which of these skills should handle a user's message.

{catalogue}

User message:
{input}

Reply with only a JSON object:
{{"skill": "<exact skill name from the list>", "why": "<one short sentence>"}}"""

GATES_PROMPT = """You are operating as the `{skill}` skill. Its instructions are below.

--- BEGIN SKILL ---
{body}
--- END SKILL ---

A user says:
{input}

Reply with only a JSON object:
{{"refuses": <true|false>,
 "status": "<the status you would record, or null>",
 "missing_evidence": ["<what evidence is missing, if any>"],
 "cites": ["<contract rules, fields, or reason codes you rely on>"],
 "escalates_to": "<escalation level if one applies, else null>"}}"""


def load(name: str) -> dict:
    return yaml.safe_load((CASES / f"{name}.yaml").read_text(encoding="utf-8"))


def skill_catalogue() -> str:
    """The descriptions a real runtime uses to pick a skill - nothing more.

    Selection happens on frontmatter, so the eval must see frontmatter. Feeding
    the whole skill body would measure a different mechanism and score better
    than the product does.
    """
    entries = []
    for skill_dir in sorted(SKILLS.iterdir()):
        document = skill_dir / "SKILL.md"
        if not document.exists():
            continue
        front = document.read_text(encoding="utf-8").split("---")[1]
        meta = yaml.safe_load(front)
        entries.append(f"- {meta['name']}: {meta['description']}")
    return "\n".join(entries)


def skill_body(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


# --- backends --------------------------------------------------------------

def backend_anthropic(prompt: str, model: str) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    request = urllib.request.Request(
        os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
        + "/v1/messages",
        data=json.dumps({
            "model": model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        payload = json.loads(response.read())
    return "".join(block.get("text", "") for block in payload.get("content", []))


def backend_command(prompt: str, command: str) -> str:
    result = subprocess.run(command, shell=True, input=prompt,
                            capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"backend command failed: {result.stderr.strip()[:300]}")
    return result.stdout


def backend_stub(case_id: str, fixture: dict) -> str:
    if case_id not in fixture:
        raise RuntimeError(f"stub fixture has no answer for {case_id}")
    return json.dumps(fixture[case_id])


def parse_json(text: str) -> dict:
    """Tolerate a model that wraps its JSON in prose or a code fence."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in response: {text.strip()[:200]}")
    return json.loads(match.group(0))


# --- scoring ---------------------------------------------------------------

def score_triggering(case: dict, answer: dict) -> list[str]:
    expect = case["expect"]
    chosen = answer.get("skill")
    failures = []
    acceptable = set(expect.get("acceptable_skills") or [])
    if expect.get("skill"):
        acceptable.add(expect["skill"])
    if acceptable and chosen not in acceptable:
        failures.append(f"chose {chosen!r}, expected one of {sorted(acceptable)}")
    if chosen in (expect.get("not_skills") or []):
        failures.append(f"chose {chosen!r}, which this case explicitly excludes")
    return failures


def score_gates(case: dict, answer: dict) -> tuple[list[str], list[str]]:
    """Returns (failures, unscored expectation keys).

    Some expectations - `offers`, for instance - are lists of paraphrasable
    actions that no exact comparison can judge. They are reported as unscored
    rather than quietly counted as passing.
    """
    expect = case["expect"]
    failures, unscored = [], []

    for key, wanted in expect.items():
        if key == "refuses":
            if bool(answer.get("refuses")) != bool(wanted):
                failures.append(f"refuses={answer.get('refuses')!r}, expected {wanted!r}")
        elif key == "status":
            if answer.get("status") != wanted:
                failures.append(f"status={answer.get('status')!r}, expected {wanted!r}")
        elif key == "escalates_to":
            if answer.get("escalates_to") != wanted:
                failures.append(f"escalates_to={answer.get('escalates_to')!r}, expected {wanted!r}")
        elif key == "names_missing_evidence":
            named = [item for item in (answer.get("missing_evidence") or []) if item]
            if bool(named) != bool(wanted):
                failures.append("did not name the missing evidence" if wanted
                                else "named missing evidence when none was expected")
        elif key == "cites":
            haystack = " ".join(str(item) for item in (answer.get("cites") or []))
            needles = wanted if isinstance(wanted, list) else [wanted]
            for needle in needles:
                if needle.lower() not in haystack.lower():
                    failures.append(f"never cited {needle!r} (cited: {haystack[:120]!r})")
        else:
            unscored.append(key)

    return failures, unscored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--backend", choices=["anthropic", "command", "stub"], default="anthropic")
    parser.add_argument("--model", default="claude-sonnet-4-5",
                        help="model id for the anthropic backend")
    parser.add_argument("--command", default=None,
                        help="shell command for the command backend; the prompt arrives on stdin")
    parser.add_argument("--fixture", default=None, help="canned answers for the stub backend")
    parser.add_argument("--suite", choices=["triggering", "gates"], default=None)
    parser.add_argument("--gate-skill", default="game-art-production-orchestrator",
                        help="skill whose instructions the gates suite runs under")
    args = parser.parse_args()

    fixture = {}
    if args.backend == "stub":
        if not args.fixture:
            raise SystemExit("--backend stub requires --fixture")
        fixture = yaml.safe_load(Path(args.fixture).read_text(encoding="utf-8")) or {}
    elif args.backend == "command" and not args.command:
        raise SystemExit("--backend command requires --command")
    elif args.backend == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        print("MODEL EVALS: SKIPPED")
        print("- no ANTHROPIC_API_KEY in the environment")
        print("- these suites need a model; a skip is not a pass")
        print("- alternatives: --backend command \"<your cli>\", or --backend stub for a harness self-test")
        raise SystemExit(2)

    def ask(case_id: str, prompt: str) -> str:
        if args.backend == "stub":
            return backend_stub(case_id, fixture)
        if args.backend == "command":
            return backend_command(prompt, args.command)
        return backend_anthropic(prompt, args.model)

    suites = [args.suite] if args.suite else ["triggering", "gates"]
    catalogue = skill_catalogue()
    body = skill_body(args.gate_skill)

    passed, failed, unscored_keys, errors = 0, [], set(), []

    for suite in suites:
        for case in load(suite)["cases"]:
            if suite == "triggering":
                prompt = TRIGGERING_PROMPT.format(catalogue=catalogue, input=case["input"].strip())
            else:
                prompt = GATES_PROMPT.format(skill=args.gate_skill, body=body,
                                             input=case["input"].strip())
            try:
                answer = parse_json(ask(case["id"], prompt))
            except Exception as error:  # noqa: BLE001 - reported, not swallowed
                errors.append(f"{case['id']}: {error}")
                continue

            if suite == "triggering":
                problems, unscored = score_triggering(case, answer), []
            else:
                problems, unscored = score_gates(case, answer)
            unscored_keys |= set(unscored)

            if problems:
                failed.append(f"{case['id']}: " + "; ".join(problems))
            else:
                passed += 1

    print("MODEL EVALS: " + ("FAIL" if failed or errors else "PASS"))
    print(f"- backend: {args.backend}" + (f" ({args.model})" if args.backend == "anthropic" else ""))
    print(f"- suites: {', '.join(suites)}")
    print(f"- passed: {passed}  failed: {len(failed)}  errored: {len(errors)}")
    for item in failed:
        print(f"- FAIL {item}")
    for item in errors:
        print(f"- ERROR {item}")
    if unscored_keys:
        print(f"! expectation keys no exact comparison can judge, reported not counted: "
              f"{', '.join(sorted(unscored_keys))}")
    raise SystemExit(1 if failed or errors else 0)


if __name__ == "__main__":
    main()
