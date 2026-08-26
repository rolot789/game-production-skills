#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil
import sys

EXPECTED = [
    "game-spec-builder",
    "art-style-builder",
    "game-asset-planner",
    "game-asset-generator",
    "game-asset-normalizer",
    "game-asset-qc",
    "runtime-visual-validator",
    "game-art-production-orchestrator",
]

def main():
    parser = argparse.ArgumentParser(description="Install game-production-toolkit skills into a repository.")
    parser.add_argument("repo")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    toolkit = Path(__file__).resolve().parents[1]
    src_root = toolkit / "skills"
    repo = Path(args.repo).resolve()
    dest_root = repo / ".agents" / "skills"
    dest_root.mkdir(parents=True, exist_ok=True)

    for skill in EXPECTED:
        src = src_root / skill
        dest = dest_root / skill
        if not src.exists():
            raise SystemExit(f"Missing toolkit skill: {skill}")
        if dest.exists():
            if not args.overwrite:
                raise SystemExit(f"Already exists: {dest} (use --overwrite)")
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        print(f"installed: {skill}")

    print(f"\nInstalled {len(EXPECTED)} skills into {dest_root}")

if __name__ == "__main__":
    main()
