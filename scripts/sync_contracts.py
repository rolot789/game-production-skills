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

    # Directory mirrors keep the manifest readable when a skill needs a whole
    # family of files, such as the artifact schemas.
    for entry in manifest.get("directory_mirrors", []):
        source_dir = ROOT / entry["source_dir"]
        if not source_dir.is_dir():
            raise SystemExit(f"mirror source directory missing: {entry['source_dir']}")
        sources = sorted(source_dir.glob(entry.get("glob", "*")))
        if not sources:
            raise SystemExit(f"directory mirror matched nothing: {entry['source_dir']}")
        subdir = entry.get("into", source_dir.name)
        for skill in entry["targets"]:
            for source in sources:
                rel = f"{entry['source_dir']}/{source.name}"
                target = ROOT / "skills" / skill / mirror_root / subdir / source.name
                plan.append((rel, skill, target, mirror_content(source, rel, header)))

    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify without writing")
    args = parser.parse_args()

    plan = planned_mirrors()
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
        if stale:
            print("CONTRACT MIRROR: FAIL")
            for item in stale:
                print(f"- {item}")
            print("\nRun: python3 scripts/sync_contracts.py")
            raise SystemExit(1)
        print("CONTRACT MIRROR: PASS")
        print(f"- {len(plan)} mirrored file(s) up to date")
        return

    print("CONTRACT MIRROR: SYNCED")
    print(f"- {len(plan)} mirrored file(s), {len(written)} updated")
    for item in written:
        print(f"  wrote {item}")


if __name__ == "__main__":
    main()
