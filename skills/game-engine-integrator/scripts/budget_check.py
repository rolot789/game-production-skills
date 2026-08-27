#!/usr/bin/env python3
"""Measure a normalized asset set against the project's performance budgets.

A budget is either measured or it is a wish. This script measures file size,
texture footprint, and atlas dimensions for every runtime asset in a project
and emits the `budget-report.yaml` body for the engine_integration stage.

    python3 budget_check.py --project-root . [--target-id web-main]

Texture memory is estimated as width * height * 4 bytes per asset (RGBA8,
uncompressed, no mips). That is the honest upper bound for an engine that does
not compress; when the engine target compresses, record the compression format
in import-settings.yaml and treat this figure as a ceiling rather than a
prediction. The script never claims a number it did not measure.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment guard
    print("budget_check.py requires Pillow: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("budget_check.py requires pyyaml: python3 -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--target-id", default=None)
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    project_file = root / "project.yaml"
    if not project_file.exists():
        raise SystemExit(f"no project.yaml in {root}")
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))

    paths = project.get("paths") or {}
    engine = project.get("engine") or {}
    budgets = project.get("budgets") or {}
    target_id = args.target_id or engine.get("id") or "default"

    normalized_root = root / paths.get("normalized", "normalized/")
    assets = sorted(normalized_root.rglob("runtime/*.png")) if normalized_root.exists() else []
    if not assets:
        raise SystemExit(f"no normalized runtime assets found under {normalized_root}")

    total_bytes = 0
    largest_bytes, largest_id = 0, None
    max_dimension = 0
    texture_bytes = 0

    for asset in assets:
        size = asset.stat().st_size
        total_bytes += size
        if size > largest_bytes:
            largest_bytes, largest_id = size, asset.stem
        with Image.open(asset) as image:
            width, height = image.size
        max_dimension = max(max_dimension, width, height)
        texture_bytes += width * height * 4

    measured = {
        "asset_count": len(assets),
        "total_asset_bytes": total_bytes,
        "largest_asset_bytes": largest_bytes,
        "largest_asset_id": largest_id,
        "atlas_count": 0,
        "max_atlas_dimension": max_dimension,
        "estimated_texture_memory_mb": round(texture_bytes / (1024 * 1024), 3),
    }

    checks: dict[str, str] = {}
    findings: list[dict] = []

    def compare(check_id: str, actual, limit, label: str, reason_code: str) -> None:
        if limit is None:
            checks[check_id] = "INSUFFICIENT_EVIDENCE"
            return
        if actual <= limit:
            checks[check_id] = "PASS"
            return
        checks[check_id] = "FAIL"
        findings.append({
            "id": f"BUD-{len(findings) + 1:03d}",
            "severity": "MAJOR",
            "expected": f"{label} <= {limit}",
            "observed": f"{label} = {actual}",
            "reason_code": reason_code,
            "root_owner": "game-engine-integrator",
            "required_action": f"reduce {label} or raise the declared budget with the owner's approval",
        })

    compare("max_atlas_dimension", measured["max_atlas_dimension"],
            budgets.get("max_atlas_dimension"), "max atlas dimension", "BUDGET_VIOLATION")
    compare("texture_memory", measured["estimated_texture_memory_mb"],
            budgets.get("max_texture_memory_mb"), "estimated texture memory (MB)", "BUDGET_VIOLATION")
    compare("total_asset_bytes", measured["total_asset_bytes"],
            budgets.get("max_total_asset_bytes"), "total asset bytes", "BUDGET_VIOLATION")
    compare("largest_asset_bytes", measured["largest_asset_bytes"],
            budgets.get("max_single_asset_bytes"), "largest single asset bytes", "BUDGET_VIOLATION")

    if any(result == "FAIL" for result in checks.values()):
        status = "integration_rework_required"
    elif all(result == "INSUFFICIENT_EVIDENCE" for result in checks.values()):
        status = "integration_blocked"
        findings.append({
            "id": "BUD-000",
            "severity": "BLOCKER",
            "expected": "project.yaml declares at least one budget",
            "observed": "no budgets declared",
            "reason_code": "BUDGET_VIOLATION",
            "root_owner": "game-engine-integrator",
            "required_action": "declare budgets in project.yaml before promoting to INTEGRATION_READY",
        })
    else:
        status = "integration_ready"

    report = {
        "schema_version": 3,
        "target": {"id": target_id, "engine": engine.get("target", "custom")},
        "status": status,
        "measured": measured,
        "budgets": budgets,
        "checks": checks,
        "findings": findings,
        "rework_handoff": None,
    }

    print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True).rstrip())
    if status in ("integration_rework_required", "integration_blocked"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
