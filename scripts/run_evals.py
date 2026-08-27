#!/usr/bin/env python3
"""Run the eval suites that can be executed without a model.

Three of the five suites are deterministic:

  routing   the symptom-to-owner mapping, checked against contracts/routing.yaml
  handoff   concrete envelopes, checked against the handoff schema
  lineage   negative cases, checked by mutating a copy of the worked example and
            asserting validate_project.py rejects it

The other two (triggering, gates) need a model harness. This script validates
their structure so the suite cannot rot into referencing skills, reason codes,
or lifecycle states that no longer exist, and reports them as pending.

    python3 scripts/run_evals.py
    python3 scripts/run_evals.py --suite routing
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.minischema import SchemaStore, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "evals" / "cases"
ROUTING = ROOT / "contracts" / "routing.yaml"
EXAMPLE = ROOT / "examples" / "gate-family"


class Results:
    def __init__(self) -> None:
        self.passed = 0
        self.failed: list[str] = []
        self.pending = 0

    def ok(self) -> None:
        self.passed += 1

    def fail(self, case_id: str, detail: str) -> None:
        self.failed.append(f"{case_id}: {detail}")


def load(name: str) -> dict:
    return yaml.safe_load((CASES / f"{name}.yaml").read_text(encoding="utf-8"))


def run_routing(results: Results) -> None:
    routing = yaml.safe_load(ROUTING.read_text(encoding="utf-8"))
    table = {entry["id"]: entry for entry in routing["symptom_classes"]}

    for case in load("routing")["cases"]:
        code = case["reason_code"]
        row = table.get(code)
        if row is None:
            results.fail(case["id"], f"reason_code {code!r} is not in contracts/routing.yaml")
            continue
        problems = []
        for field, expected in case["expect"].items():
            actual = row.get(field)
            if actual != expected:
                problems.append(f"{field}: expected {expected!r}, routing.yaml has {actual!r}")
        if problems:
            results.fail(case["id"], "; ".join(problems))
        else:
            results.ok()


def run_handoff(results: Results) -> None:
    store = SchemaStore(ROOT / "contracts" / "schemas")
    routing = yaml.safe_load(ROUTING.read_text(encoding="utf-8"))
    known = {entry["id"] for entry in routing["symptom_classes"]}

    for case in load("handoff")["cases"]:
        errors = validate(case["envelope"], "rework-handoff.schema.json", store)
        for code in case["envelope"].get("reason_codes", []):
            if code not in known:
                errors.append(f"$.reason_codes: {code!r} is not in contracts/routing.yaml")

        if case["valid"]:
            if errors:
                results.fail(case["id"], f"expected valid, got: {errors[0]}")
            else:
                results.ok()
        else:
            needle = case.get("expect_error_contains", "")
            if not errors:
                results.fail(case["id"], "expected the schema to reject this envelope, it passed")
            elif needle and not any(needle in error for error in errors):
                results.fail(case["id"], f"rejected, but no error mentioned {needle!r}: {errors}")
            else:
                results.ok()


def apply_mutation(project: Path, mutation: dict) -> None:
    kind = mutation["type"]
    target = project / mutation["target"]

    if kind == "tamper_asset":
        data = bytearray(target.read_bytes())
        data[-1] = (data[-1] + 1) % 256
        target.write_bytes(bytes(data))
    elif kind == "set_field":
        document = yaml.safe_load(target.read_text(encoding="utf-8"))
        node = document
        for key in mutation["path"][:-1]:
            node = node[key]
        node[mutation["path"][-1]] = mutation["value"]
        target.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    elif kind == "append_untested_high_risk":
        document = yaml.safe_load(target.read_text(encoding="utf-8"))
        document["untested"].append({
            "context": "mobile portrait",
            "reason": "runtime unavailable",
            "risk": "high",
        })
        target.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    else:
        raise SystemExit(f"unknown mutation type: {kind}")


def run_lineage(results: Results) -> None:
    if not EXAMPLE.exists():
        results.fail("LIN-*", "examples/gate-family is missing; lineage cases need it")
        return

    for case in load("lineage")["cases"]:
        if not case.get("executable"):
            results.pending += 1
            continue

        workdir = Path(tempfile.mkdtemp(prefix="gps-eval-"))
        project = workdir / "gate-family"
        try:
            shutil.copytree(EXAMPLE, project)
            apply_mutation(project, case["mutation"])
            outcome = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "validate_project.py"), str(project)],
                capture_output=True, text=True,
            )
            expected_fail = case["expect"]["validator"] == "FAIL"
            actually_failed = outcome.returncode != 0
            needle = case["expect"].get("message_contains", "")

            if expected_fail != actually_failed:
                results.fail(case["id"],
                             f"expected validator {'FAIL' if expected_fail else 'PASS'}, "
                             f"got {'FAIL' if actually_failed else 'PASS'}")
            elif needle and needle not in outcome.stdout:
                results.fail(case["id"], f"rejected, but the message never mentioned {needle!r}")
            else:
                results.ok()
        finally:
            shutil.rmtree(workdir, ignore_errors=True)


def check_structure(results: Results) -> None:
    """Non-executable suites still have to reference things that exist."""
    available = {p.name for p in (ROOT / "skills").iterdir() if p.is_dir()}
    contract = yaml.safe_load((ROOT / "contracts" / "toolkit-contract.yaml").read_text(encoding="utf-8"))
    levels = set(contract["generation_rework_levels"])
    statuses = set()
    for stage in contract["stages"].values():
        statuses.update(stage.get("allowed_exit_status", []))

    for case in load("triggering")["cases"]:
        results.pending += 1
        expected = case["expect"]
        named = [expected.get("skill")] + expected.get("not_skills", []) + expected.get("acceptable_skills", [])
        for skill in [s for s in named if s]:
            if skill not in available:
                results.fail(case["id"], f"names a skill that does not exist: {skill}")

    for case in load("gates")["cases"]:
        results.pending += 1
        expected = case["expect"]
        if "status" in expected and expected["status"] not in statuses:
            results.fail(case["id"], f"names an unknown status: {expected['status']}")
        if "escalates_to" in expected and expected["escalates_to"] not in levels:
            results.fail(case["id"], f"names an unknown rework level: {expected['escalates_to']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--suite", choices=["routing", "handoff", "lineage", "structure"], default=None)
    args = parser.parse_args()

    results = Results()
    suites = [args.suite] if args.suite else ["routing", "handoff", "lineage", "structure"]

    if "routing" in suites:
        run_routing(results)
    if "handoff" in suites:
        run_handoff(results)
    if "lineage" in suites:
        run_lineage(results)
    if "structure" in suites:
        check_structure(results)

    if results.failed:
        print("EVALS: FAIL")
        for failure in results.failed:
            print(f"- {failure}")
        print(f"\n{results.passed} passed, {len(results.failed)} failed, {results.pending} pending a model harness")
        raise SystemExit(1)

    print("EVALS: PASS")
    print(f"- executed: {results.passed}")
    print(f"- pending a model harness: {results.pending}")
    print("- suites: routing (deterministic), handoff (schema), lineage (negative), structure")


if __name__ == "__main__":
    main()
