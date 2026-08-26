#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil
import re
import yaml

def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.strip()).strip("-").lower()
    return s or "game-project"

def main():
    parser = argparse.ArgumentParser(description="Bootstrap game-production-toolkit project folders.")
    parser.add_argument("repo")
    parser.add_argument("--name", required=True)
    parser.add_argument("--overwrite-state", action="store_true")
    args = parser.parse_args()

    toolkit = Path(__file__).resolve().parents[1]
    template = toolkit / "templates" / "project"
    repo = Path(args.repo).resolve()

    # Create directory skeleton / copy non-destructively
    for p in template.rglob("*"):
        rel = p.relative_to(template)
        dest = repo / rel
        if p.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        else:
            if dest.exists() and not (args.overwrite_state and rel.as_posix() == ".pipeline/game-art-production-state.yaml"):
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)

    state_path = repo / ".pipeline" / "game-art-production-state.yaml"
    state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
    state["project"]["name"] = args.name
    state["project"]["id"] = slugify(args.name)
    state_path.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True), encoding="utf-8")

    proj_path = repo / "project.yaml"
    proj = yaml.safe_load(proj_path.read_text(encoding="utf-8"))
    proj["project"]["name"] = args.name
    proj["project"]["id"] = slugify(args.name)
    proj_path.write_text(yaml.safe_dump(proj, sort_keys=False, allow_unicode=True), encoding="utf-8")

    print(f"bootstrapped: {args.name}")
    print(f"repo: {repo}")
    print(f"state: {state_path}")

if __name__ == "__main__":
    main()
