#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import sys
import yaml

EXPECTED = [
    "game-spec-builder",
    "art-style-builder",
    "game-asset-planner",
    "game-asset-generator",
    "game-asset-normalizer",
    "game-asset-qc",
    "game-engine-integrator",
    "runtime-visual-validator",
    "game-art-production-orchestrator",
]

def read_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        raise ValueError("missing YAML frontmatter")
    return yaml.safe_load(m.group(1))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("toolkit", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.toolkit).resolve()
    errors = []

    registry = root / "contracts" / "toolkit-contract.yaml"
    if not registry.exists():
        errors.append("missing contracts/toolkit-contract.yaml")
    else:
        data = yaml.safe_load(registry.read_text(encoding="utf-8"))
        reg_skills = {v["skill"] for v in data.get("stages", {}).values()}
        reg_skills.add(data.get("orchestrator", {}).get("skill"))
        missing_reg = set(EXPECTED) - reg_skills
        if missing_reg:
            errors.append(f"registry missing skills: {sorted(missing_reg)}")

    for skill in EXPECTED:
        d = root / "skills" / skill
        if not d.exists():
            errors.append(f"missing skill directory: {skill}")
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill}: missing SKILL.md")
            continue
        try:
            fm = read_frontmatter(skill_md)
            if fm.get("name") != skill:
                errors.append(f"{skill}: frontmatter name is {fm.get('name')!r}")
            if not fm.get("description"):
                errors.append(f"{skill}: missing description")
        except Exception as e:
            errors.append(f"{skill}: {e}")

    if errors:
        print("TOOLKIT DOCTOR: FAIL")
        for e in errors:
            print(f"- {e}")
        raise SystemExit(1)

    print("TOOLKIT DOCTOR: PASS")
    print(f"- skills: {len(EXPECTED)}")
    print("- registry: valid")
    print("- SKILL.md frontmatter: valid")

if __name__ == "__main__":
    main()
