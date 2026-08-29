#!/usr/bin/env python3
"""Bring images produced outside this pipeline back in as tracked candidates.

The generator can always emit a complete job for an external tool. Until now
nothing could bring the result back, so `provenance.external_job: true` was a
dead end: the images existed, and the pipeline had no way to hash them, bind
them to the contract they were made from, or let normalization consume them.

This closes that loop. It does not generate anything and it does not judge
anything - it copies the bytes in, computes the identity every downstream stage
depends on, and records honestly where they came from.

    python3 import_candidates.py --project-root . --asset-id AST-GATE-CLOSED \\
        --image ~/out/gate_a.png --image ~/out/gate_b.png \\
        --capability external-tool --model "<the model that actually ran>" \\
        --seed not_exposed

What it deliberately does NOT do:

  - mark a candidate `selected`. Selection is a judgment about whether the
    image satisfies the contract, and the agent makes it.
  - record a screening verdict for any visual dimension. Only `output` is
    filled, from check_alpha.py, because that is the only dimension a script
    can measure. Inventing PASS for identity or palette would put a fabricated
    verdict into the record that QC later trusts.

Exit 0 when every image was imported, 1 when any failed its alpha screen.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("import_candidates.py requires pyyaml: python3 -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

CHECK_ALPHA = Path(__file__).resolve().parent / "check_alpha.py"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact_ref(root: Path, rel: str) -> dict:
    path = root / rel
    if not path.exists():
        raise SystemExit(f"required input does not exist: {rel}")
    document = yaml.safe_load(path.read_text(encoding="utf-8")) if path.suffix == ".yaml" else {}
    return {
        "path": rel,
        "version": (document or {}).get("version", "v1"),
        "content_hash": sha256_file(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--image", action="append", required=True,
                        help="image produced by the external tool; repeat per candidate")
    parser.add_argument("--capability", required=True,
                        help="what actually produced these, e.g. the tool or service name")
    parser.add_argument("--model", required=True,
                        help="the model that actually ran; 'not_exposed' when the tool does not say")
    parser.add_argument("--seed", default="not_exposed",
                        help="the seed the tool reported; leave as not_exposed rather than inventing one")
    parser.add_argument("--job-version", default=None,
                        help="defaults to the version in job.yaml, else v1")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    project_file = root / "project.yaml"
    if not project_file.exists():
        raise SystemExit(f"no project.yaml in {root}")
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    paths = project.get("paths") or {}

    asset_id = args.asset_id
    generation_dir = root / paths.get("generation", "generation/") / asset_id
    spec_rel = f"{paths.get('asset_specs', 'assets/specs/')}{asset_id}.yaml"

    # A candidate exists to satisfy a contract. Importing one without the
    # contract it was made from produces an image with no way to judge it, which
    # is the state this whole stage exists to prevent.
    contract_path = generation_dir / "generation-contract.yaml"
    if not contract_path.exists():
        raise SystemExit(
            f"{asset_id}: no generation-contract.yaml at "
            f"{contract_path.relative_to(root)}. Compile the contract before importing "
            f"candidates - an imported image with no contract cannot be screened against anything."
        )

    spec = yaml.safe_load((root / spec_rel).read_text(encoding="utf-8"))
    background_policy = ((spec.get("runtime") or {}).get("background_policy")) or "transparent"

    job_path = generation_dir / "job.yaml"
    job = yaml.safe_load(job_path.read_text(encoding="utf-8")) if job_path.exists() else {}
    job_version = args.job_version or job.get("job_version") or "v1"

    candidates_dir = generation_dir / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    (generation_dir / "records").mkdir(parents=True, exist_ok=True)

    # Continue the ordinal rather than restarting it: a re-import must not
    # overwrite a candidate an earlier record already names by hash.
    existing = [
        int(match.group(1))
        for path in candidates_dir.glob(f"{job_version}-c*")
        for match in [re.fullmatch(rf"{re.escape(job_version)}-c(\d+)", path.stem)] if match
    ]
    next_ordinal = max(existing, default=0) + 1

    style_authority = spec.get("style_authority") or {}
    inputs = {
        "asset_spec": artifact_ref(root, spec_rel),
        "art_style": artifact_ref(root, paths.get("art_style", "art/art-style.yaml")),
        "generation_contract": artifact_ref(root, str(contract_path.relative_to(root))),
        "anchor_ids": style_authority.get("anchor_ids") or [],
        "constraint_ids": style_authority.get("constraint_ids") or [],
        "canonical_parent_candidate": None,
    }

    imported, failed = [], []
    for offset, source in enumerate(args.image):
        source_path = Path(source).expanduser().resolve()
        if not source_path.exists():
            raise SystemExit(f"no such image: {source}")

        candidate_id = f"{job_version}-c{next_ordinal + offset}"
        target = candidates_dir / f"{candidate_id}{source_path.suffix.lower()}"
        shutil.copy2(source_path, target)
        candidate_hash = sha256_file(target)

        alpha = subprocess.run(
            [sys.executable, str(CHECK_ALPHA), "--candidate", str(target),
             "--policy", background_policy],
            capture_output=True, text=True,
        )
        alpha_passed = alpha.returncode == 0
        if not alpha_passed:
            failed.append(candidate_id)

        record = {
            "schema_version": 3,
            "asset_id": asset_id,
            "job_version": job_version,
            "candidate": {
                "id": candidate_id,
                "path": str(target.relative_to(root)),
                "content_hash": candidate_hash,
                "selected": False,
            },
            "inputs": inputs,
            # Only the dimension a script can measure. Every visual dimension is
            # left out rather than guessed, so a later PASS in this block means
            # someone actually looked.
            "screening": {"output": "PASS" if alpha_passed else "FAIL"},
            "provenance": {
                "capability": args.capability,
                "model": args.model,
                "seed": args.seed,
                "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "external_job": False,
                "source": "external_import",
                "imported_from": str(source_path),
            },
        }
        (generation_dir / "records" / f"{candidate_id}.yaml").write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8")
        imported.append(record)

    index_path = generation_dir / "candidate-index.yaml"
    index = yaml.safe_load(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    entries = index.get("candidates") or []
    entries.extend({
        "id": record["candidate"]["id"],
        "path": record["candidate"]["path"],
        "content_hash": record["candidate"]["content_hash"],
        "screening": record["screening"]["output"],
        "selected": False,
    } for record in imported)
    index.update({
        "asset_id": asset_id,
        "job_version": job_version,
        "candidates": entries,
        "budget": {
            "candidates_generated": len(entries),
            "candidates_max": ((job.get("budget") or {}).get("candidates_max", 4)),
            "stop_reason": "awaiting screening",
        },
    })
    index_path.write_text(yaml.safe_dump(index, sort_keys=False, allow_unicode=True), encoding="utf-8")

    for record in imported:
        print(f"imported {record['candidate']['id']}  {record['candidate']['content_hash'][:12]}  "
              f"alpha {record['screening']['output']}")
    print(f"- index    {index_path.relative_to(root)}")
    print("- screening: only `output` is recorded. Screen identity, style, family, and state "
          "readability yourself, then mark the selected candidate.")

    if failed:
        print(
            f"\n# OUTPUT_TECHNICAL_FAILURE for {', '.join(failed)} - imported, but the "
            f"background is painted on.\n"
            f"# This is G3_CHANGE_GENERATION_STRATEGY, not G1: the external tool will draw a\n"
            f"# background again. Change how transparency is requested from it.",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
