#!/usr/bin/env python3
"""Mirror canonical contract files into the skill directories that read them.

An installed skill is a self-contained directory. A SKILL.md that points at
`contracts/rework-handoff-contract.yaml` resolves to nothing once the skill is
installed on its own, so every contract a skill must read is mirrored into that
skill's `references/` directory.

    python3 scripts/sync_contracts.py           # write the mirrors
    python3 scripts/sync_contracts.py --check   # fail if any mirror is stale

`--check` runs in CI so an edited contract that was never re-synced fails the
build instead of shipping a stale copy.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "contracts" / "mirror-manifest.yaml"
ROUTING = ROOT / "contracts" / "routing.yaml"
ROUTING_INDEX = ROOT / "contracts" / "routing-index.yaml"


def build_routing_index() -> str:
    """Derive the compact routing lookup from contracts/routing.yaml.

    Seven skills are each told to read a 279-line table to resolve one row, on
    every rework cycle. The full file is worth reading when a row needs its
    description or its note; the common case is a lookup, and a lookup does not
    need the prose.

    Generated, never hand-edited: an index that can disagree with the table it
    indexes is worse than no index.
    """
    routing = yaml.safe_load(ROUTING.read_text(encoding="utf-8"))
    lines = [
        "# GENERATED - DO NOT EDIT",
        "# source: contracts/routing.yaml",
        "# regenerate: python3 scripts/sync_contracts.py",
        "#",
        "# Compact lookup for failure routing. Resolve the symptom class with",
        "# `decision_procedure`, then take the owner and both scopes from `classes`.",
        "#",
        "# Read contracts/routing.yaml itself when you need a class's full",
        "# description or its note, when two classes look equally applicable, or",
        "# when escalating scope - systemic_escalation, multi_owner, and qc_escape",
        "# live there and are not summarized here.",
        f"version: {routing['version']}",
        "name: failure-routing-index",
        "",
        "decision_procedure:",
    ]
    for step in routing["decision_procedure"]:
        key = "if_yes" if "if_yes" in step else "if_no"
        lines.append(f"  - {step['step']}. {step['ask'].strip()}")
        lines.append(f"    {key}: {step[key].strip()}")

    lines += ["", "# id: root_owner | invalidation_scope | revalidation_scope | default_status",
              "classes:"]
    for entry in routing["symptom_classes"]:
        owner = entry["root_owner"] or "NONE - do not auto-route; candidates: " + ", ".join(
            entry.get("root_owner_candidates") or [])
        lines.append(f"  {entry['id']}:")
        lines.append(f"    owner: {owner}")
        lines.append(f"    invalidation: {entry['invalidation_scope']}")
        lines.append(f"    revalidation: [{', '.join(entry['revalidation_scope'])}]")
        lines.append(f"    status: {entry['default_status']}")
        if entry.get("note"):
            lines.append("    has_note: true")
    return "\n".join(lines) + "\n"


def mirror_content(source: Path, rel: str, header: str) -> str:
    body = source.read_text(encoding="utf-8")
    if source.suffix == ".json":
        # JSON has no comment syntax, so a mirrored schema is byte-identical to
        # its source. The manifest is what records that it is generated.
        return body
    return (
        f"{header}\n"
        f"# source: {rel}\n"
        f"# regenerate: python3 scripts/sync_contracts.py\n"
        f"{body}"
    )


def planned_mirrors():
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    mirror_root = manifest.get("mirror_root", "references")
    header = manifest.get("header_marker", "# GENERATED MIRROR - DO NOT EDIT")
    plan = []

    for entry in manifest.get("mirrors", []):
        source = ROOT / entry["source"]
        if not source.exists():
            raise SystemExit(f"mirror source missing: {entry['source']}")
        content = mirror_content(source, entry["source"], header)
        for skill in entry["targets"]:
            target = ROOT / "skills" / skill / mirror_root / source.name
            plan.append((entry["source"], skill, target, content))

    # Schemas are mirrored per skill rather than wholesale. A skill gets what it
    # writes plus the shared $defs; carrying all eleven cost every skill about
    # 10,000 tokens of schemas it never names.
    schemas = manifest.get("schema_mirrors") or {}
    if schemas:
        source_dir = ROOT / schemas["source_dir"]
        subdir = schemas.get("into", "schemas")
        always = schemas.get("always", [])
        for skill, wanted in schemas["targets"].items():
            for name in sorted(set(wanted) | set(always)):
                source = source_dir / name
                if not source.exists():
                    raise SystemExit(f"{skill}: schema mirror source missing: {name}")
                rel = f"{schemas['source_dir']}/{name}"
                target = ROOT / "skills" / skill / mirror_root / subdir / name
                plan.append((rel, skill, target, mirror_content(source, rel, header)))

    return plan


def stale_mirrors(plan) -> list[Path]:
    """Mirrored files that no longer correspond to anything in the manifest.

    Narrowing a mirror list has to remove the copies it dropped, or the skill
    keeps shipping schemas the manifest no longer claims - and a file nothing
    declares is exactly what the manifest exists to prevent.
    """
    expected = {target for _, _, target, _ in plan}
    orphans = []
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        schemas_dir = skill_dir / "references" / "schemas"
        if not schemas_dir.is_dir():
            continue
        orphans += [path for path in sorted(schemas_dir.glob("*.json")) if path not in expected]
    return orphans


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()

    index = build_routing_index()
    if args.check:
        current = ROUTING_INDEX.read_text(encoding="utf-8") if ROUTING_INDEX.exists() else None
        if current != index:
            print("CONTRACT MIRROR: FAIL")
            print(f"- {ROUTING_INDEX.relative_to(ROOT)} is stale; it is derived from routing.yaml")
            print("\nRun: python3 scripts/sync_contracts.py")
            raise SystemExit(1)
    else:
        ROUTING_INDEX.write_text(index, encoding="utf-8")

    plan = planned_mirrors()
    orphans = stale_mirrors(plan)
    stale, written = [], []

    for source, skill, target, content in plan:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            if args.check:
                reason = "missing" if not target.exists() else "stale"
                stale.append(f"{target.relative_to(ROOT)} ({reason}, source {source})")
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
                written.append(str(target.relative_to(ROOT)))

    if args.check:
        stale += [f"{path.relative_to(ROOT)} (orphaned; no manifest entry claims it)"
                  for path in orphans]
        if stale:
            print("CONTRACT MIRROR: FAIL")
            for item in stale:
                print(f"- {item}")
            print("\nRun: python3 scripts/sync_contracts.py")
            raise SystemExit(1)
        print("CONTRACT MIRROR: PASS")
        print(f"- {len(plan)} mirrored file(s) up to date")
        return

    for path in orphans:
        path.unlink()

    print("CONTRACT MIRROR: SYNCED")
    print(f"- {len(plan)} mirrored file(s), {len(written)} updated, {len(orphans)} removed")
    for item in written:
        print(f"  wrote {item}")


if __name__ == "__main__":
    main()
