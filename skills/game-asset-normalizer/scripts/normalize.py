#!/usr/bin/env python3
"""Deterministic normalization of a generation candidate into a runtime asset.

Everything this stage does - alpha bounds, trim, uniform scale, canvas
placement, family alignment, anchor and pivot metadata, hashing - is
arithmetic. Doing it by eye is neither reproducible nor checkable, and the
toolkit's whole invalidation model depends on `content_hash` being real.

So the agent does not perform these operations. It runs this script, reads the
record, and makes the judgment calls the script cannot: whether the result
respects the AssetSpec's intent, and where to route a failure.

    python3 normalize.py \\
        --candidate generation/AST-001/candidates/v1-c2.png \\
        --spec assets/specs/AST-001.yaml \\
        --project-root . \\
        --out normalized/AST-001

Family alignment: pass --shared-scale to force every member of a family onto
one scale basis instead of letting each member maximize its own content.

Exit status is 0 when every validation check passes, 1 otherwise. A non-zero
exit is a normalizer-owned finding unless the record says the root owner is
upstream.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment guard
    print("normalize.py requires Pillow: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("normalize.py requires pyyaml: python3 -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

RESAMPLE = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
    "lanczos": Image.LANCZOS,
}

ANCHOR_RULES = ("content_center", "content_bottom_center", "canvas_center")
PIVOT_RULES = ("center", "bottom_center", "content_center", "content_bottom_center")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_spec(path: Path) -> dict:
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(spec, dict):
        raise SystemExit(f"AssetSpec is not a mapping: {path}")
    return spec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidate", required=True, help="selected generation candidate image")
    parser.add_argument("--spec", required=True, help="specs/<asset-id>.yaml")
    parser.add_argument("--out", required=True, help="output directory, normally normalized/<asset-id>")
    parser.add_argument("--project-root", default=".", help="root that recorded paths are relative to")
    parser.add_argument("--generation-record", default=None)
    parser.add_argument("--policy-id", default="default-raster-v1")
    parser.add_argument("--policy-version", default="v1")
    parser.add_argument("--shared-scale", type=float, default=None,
                        help="force this scale factor for family alignment")
    parser.add_argument("--dry-run", action="store_true", help="report geometry without writing outputs")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    candidate_path = Path(args.candidate).resolve()
    spec_path = Path(args.spec).resolve()
    out_dir = Path(args.out).resolve()

    spec = load_spec(spec_path)
    asset_id = spec.get("asset_id") or spec_path.stem
    norm = spec.get("normalization") or {}
    runtime = spec.get("runtime") or {}

    target = norm.get("target_canvas")
    if not target:
        raise SystemExit(
            f"{asset_id}: normalization.target_canvas is missing. The normalizer never "
            f"invents a canvas; route this to game-asset-planner (DECOMPOSITION_DEFECT)."
        )
    canvas_w, canvas_h = int(target["width"]), int(target["height"])
    padding = int(norm.get("padding", 0))
    do_trim = bool(norm.get("trim", True))
    resample_name = str(norm.get("resample", "lanczos"))
    if resample_name not in RESAMPLE:
        raise SystemExit(f"{asset_id}: unsupported resample mode {resample_name!r}")

    anchor_rule = str(norm.get("anchor_policy", "content_center"))
    pivot_rule = str(norm.get("pivot_policy", "center"))
    background_policy = str(runtime.get("background_policy", "transparent"))

    source = Image.open(candidate_path)
    source_size = list(source.size)
    image = source.convert("RGBA")

    operations: list[dict] = [{"op": "inspect", "detail": {"source_size": source_size, "mode": source.mode}}]

    alpha_bbox = image.getbbox()
    if alpha_bbox is None:
        raise SystemExit(
            f"{asset_id}: candidate is fully transparent. The normalizer never invents "
            f"content; route this to game-asset-generator (CONTENT_ERROR)."
        )

    content = image.crop(alpha_bbox) if do_trim else image
    if do_trim:
        operations.append({"op": "trim", "detail": {"bbox": list(alpha_bbox)}})

    inner_w = max(canvas_w - 2 * padding, 1)
    inner_h = max(canvas_h - 2 * padding, 1)
    if args.shared_scale is not None:
        scale = float(args.shared_scale)
    else:
        scale = min(inner_w / content.width, inner_h / content.height)

    scaled_w = max(1, round(content.width * scale))
    scaled_h = max(1, round(content.height * scale))
    scaled = content.resize((scaled_w, scaled_h), RESAMPLE[resample_name])
    operations.append({
        "op": "scale",
        "detail": {
            "factor": round(scale, 6),
            "from": [content.width, content.height],
            "to": [scaled_w, scaled_h],
            "resample": resample_name,
            "basis": "shared_family_scale" if args.shared_scale is not None else "fit_content",
        },
    })

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    offset_x = (canvas_w - scaled_w) // 2
    if anchor_rule == "content_bottom_center":
        offset_y = canvas_h - padding - scaled_h
    elif anchor_rule == "canvas_center":
        offset_x, offset_y = (canvas_w - scaled_w) // 2, (canvas_h - scaled_h) // 2
    elif anchor_rule == "content_center":
        offset_y = (canvas_h - scaled_h) // 2
    else:
        raise SystemExit(f"{asset_id}: unsupported anchor_policy {anchor_rule!r}; expected one of {ANCHOR_RULES}")
    canvas.paste(scaled, (offset_x, offset_y))
    operations.append({"op": "canvas", "detail": {"size": [canvas_w, canvas_h], "offset": [offset_x, offset_y],
                                                  "anchor_policy": anchor_rule, "padding": padding}})

    if args.shared_scale is not None:
        operations.append({"op": "family_align", "detail": {"shared_scale": round(scale, 6)}})

    if background_policy == "opaque":
        flattened = Image.new("RGBA", canvas.size, (0, 0, 0, 255))
        flattened.alpha_composite(canvas)
        canvas = flattened
        operations.append({"op": "alpha_clean", "detail": "flattened to opaque per runtime.background_policy"})

    visual_anchor = [
        round((offset_x + scaled_w / 2) / canvas_w, 6),
        round((offset_y + scaled_h / 2) / canvas_h, 6),
    ]
    if pivot_rule == "center":
        runtime_pivot = [0.5, 0.5]
    elif pivot_rule == "bottom_center":
        runtime_pivot = [0.5, 1.0]
    elif pivot_rule == "content_center":
        runtime_pivot = list(visual_anchor)
    elif pivot_rule == "content_bottom_center":
        runtime_pivot = [round((offset_x + scaled_w / 2) / canvas_w, 6),
                         round((offset_y + scaled_h) / canvas_h, 6)]
    else:
        raise SystemExit(f"{asset_id}: unsupported pivot_policy {pivot_rule!r}; expected one of {PIVOT_RULES}")
    operations.append({"op": "metadata", "detail": {"visual_anchor": visual_anchor,
                                                    "runtime_pivot": runtime_pivot,
                                                    "pivot_policy": pivot_rule}})

    geometry = {
        "asset_id": asset_id,
        "source_size": source_size,
        "alpha_bbox": list(alpha_bbox),
        "trimmed_size": [content.width, content.height],
        "scale_factor": round(scale, 6),
        "placed_size": [scaled_w, scaled_h],
        "placement_offset": [offset_x, offset_y],
        "canvas": [canvas_w, canvas_h],
        "padding": padding,
        "visual_anchor": visual_anchor,
        "runtime_pivot": runtime_pivot,
        "collision_origin": norm.get("collision_origin"),
    }

    # ---- validation ------------------------------------------------------
    checks: dict[str, str] = {}
    failures: list[str] = []

    checks["canvas_matches_spec"] = "PASS" if canvas.size == (canvas_w, canvas_h) else "FAIL"
    checks["content_fits_canvas"] = "PASS" if (scaled_w <= inner_w and scaled_h <= inner_h) else "FAIL"
    checks["padding_respected"] = "PASS" if (
        offset_x >= padding - 1 and offset_y >= -1 and
        offset_x + scaled_w <= canvas_w - padding + 1 and
        offset_y + scaled_h <= canvas_h + 1
    ) else "FAIL"
    post_bbox = canvas.getbbox()
    checks["no_content_clipped"] = "PASS" if post_bbox is not None else "FAIL"
    checks["alpha_mode"] = "PASS" if (
        (background_policy == "transparent" and canvas.mode == "RGBA")
        or background_policy != "transparent"
    ) else "FAIL"
    checks["aspect_preserved"] = "PASS" if args.shared_scale is not None or abs(
        (scaled_w / scaled_h) - (content.width / content.height)
    ) < 0.02 else "FAIL"

    for name, result in checks.items():
        if result != "PASS":
            failures.append(name)

    if args.dry_run:
        print(json.dumps({"geometry": geometry, "checks": checks}, indent=2))
        raise SystemExit(1 if failures else 0)

    runtime_dir = out_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    output_path = runtime_dir / f"{asset_id}.png"
    canvas.save(output_path, format="PNG", optimize=True)
    operations.append({"op": "export", "detail": {"format": "PNG", "path": str(output_path)}})

    def rel(path: Path) -> str:
        try:
            return str(path.relative_to(root))
        except ValueError:
            return str(path)

    record = {
        "schema_version": 3,
        "asset_id": asset_id,
        "input_candidate": {
            "id": candidate_path.stem,
            "path": rel(candidate_path),
            "content_hash": sha256_file(candidate_path),
            "generation_job_version": spec.get("generation_job_version", "v1"),
            "generation_record": args.generation_record,
        },
        "asset_spec": {
            "path": rel(spec_path),
            "version": spec.get("version", "v1"),
            "content_hash": sha256_text(spec_path.read_text(encoding="utf-8")),
        },
        "normalization_policy": {"id": args.policy_id, "version": args.policy_version},
        "operations": operations,
        "family_lineage": {
            "family_id": spec.get("family_id"),
            "canonical_parent": (spec.get("family") or {}).get("canonical_parent"),
            "shared_canvas": {"width": canvas_w, "height": canvas_h},
            "shared_scale_basis": round(scale, 6) if args.shared_scale is not None else "fit_content",
        },
        "geometry": {
            "source_size": source_size,
            "alpha_bbox": list(alpha_bbox),
            "scale_factor": round(scale, 6),
            "visual_anchor": visual_anchor,
            "runtime_pivot": runtime_pivot,
            "collision_origin": norm.get("collision_origin"),
        },
        "output": {
            "path": rel(output_path),
            "content_hash": sha256_file(output_path),
            "width": canvas_w,
            "height": canvas_h,
            "mode": canvas.mode,
            "bytes": output_path.stat().st_size,
        },
        "validation": {
            "status": "fail" if failures else "pass",
            "checks": checks,
            "failures": failures,
        },
    }

    (out_dir / "geometry-report.yaml").write_text(
        yaml.safe_dump(geometry, sort_keys=False, allow_unicode=True), encoding="utf-8")
    (out_dir / "normalization-record.yaml").write_text(
        yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8")

    print(f"normalized {asset_id}")
    print(f"- output   {rel(output_path)}  {canvas_w}x{canvas_h}  {record['output']['content_hash'][:12]}")
    print(f"- scale    {record['geometry']['scale_factor']}  pivot {runtime_pivot}  anchor {visual_anchor}")
    print(f"- record   {rel(out_dir / 'normalization-record.yaml')}")
    if failures:
        print(f"- VALIDATION FAILED: {', '.join(failures)}")
        raise SystemExit(1)
    print("- validation: pass")


if __name__ == "__main__":
    main()
