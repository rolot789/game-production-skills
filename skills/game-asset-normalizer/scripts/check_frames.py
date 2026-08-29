#!/usr/bin/env python3
"""Verify that the frames of one animation clip form a playable sequence.

A clip is the case where per-frame inspection is least useful. Every defect
this script finds is invisible when you look at one frame at a time and obvious
the moment the clip plays:

  pivot drift        the character bobs while walking
  canvas mismatch    the sprite jumps between frames
  bbox drift         content slides inside a canvas that is supposed to be fixed
  duplicate frame    two frames are the same image, so the clip stutters
  loop break         the last frame does not return to the first

All five are arithmetic over the normalized outputs, which is why they belong
in a script rather than in an agent's judgment.

The sixth thing you want to know - did the model *redraw* a frame instead of
posing it - is measured but not decided here. See `poses_share_a_subject`.

    python3 check_frames.py --project-root . --clip CLIP-GATE-OPENING \\
        --spec assets/specs/AST-GATE-OPENING-000.yaml \\
        --spec assets/specs/AST-GATE-OPENING-001.yaml ...

Exit 0 when every check passes, 1 on any FAIL. A FAIL does not by itself name
an owner: pivot and canvas defects are normalizer-owned
(FAMILY_ALIGNMENT_DEFECT), a redrawn frame is generator-owned (IDENTITY_DRIFT),
and a missing in-between is planner-owned (DECOMPOSITION_DEFECT).
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from PIL import Image, ImageChops
except ImportError:  # pragma: no cover - environment guard
    print("check_frames.py requires Pillow: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("check_frames.py requires pyyaml: python3 -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

# A frame that differs from its neighbour by less than this share of the union
# silhouette is not a new pose - it is the same drawing again. This one is safe
# to decide: identical is identical.
DUPLICATE_BELOW = 0.005


def silhouette(image: Image.Image) -> Image.Image:
    """Binary coverage mask. Compares shape, not colour, so a palette shift is
    not mistaken for a pose change."""
    return image.convert("RGBA").getchannel("A").point(lambda a: 255 if a > 8 else 0)


def symmetric_difference(a: Image.Image, b: Image.Image) -> float:
    """Share of the combined silhouette that only one of the two frames covers."""
    left, right = silhouette(a), silhouette(b)
    difference = ImageChops.difference(left, right).point(lambda v: 255 if v > 0 else 0)
    union = ImageChops.lighter(left, right)
    union_area = sum(union.point(lambda v: 1 if v else 0).getdata())
    if union_area == 0:
        return 0.0
    return sum(difference.point(lambda v: 1 if v else 0).getdata()) / union_area


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--clip", required=True)
    parser.add_argument("--spec", action="append", required=True,
                        help="AssetSpec for one frame; repeat per frame, order does not matter")
    parser.add_argument("--pivot-tolerance", type=float, default=0.0,
                        help="permitted runtime_pivot drift between frames, in normalized units")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    project_file = root / "project.yaml"
    project = yaml.safe_load(project_file.read_text(encoding="utf-8")) if project_file.exists() else {}
    normalized_root = root / (project.get("paths") or {}).get("normalized", "normalized/")

    frames = []
    for spec_path in args.spec:
        spec = yaml.safe_load((root / spec_path).read_text(encoding="utf-8"))
        animation = spec.get("animation") or {}
        if animation.get("clip_id") != args.clip:
            continue
        asset_id = spec["asset_id"]
        record_path = normalized_root / asset_id / "normalization-record.yaml"
        if not record_path.exists():
            raise SystemExit(f"{asset_id}: not normalized yet ({record_path.relative_to(root)} missing)")
        record = yaml.safe_load(record_path.read_text(encoding="utf-8"))
        frames.append({
            "asset_id": asset_id,
            "index": animation["frame_index"],
            "frame_count": animation["frame_count"],
            "loop": animation.get("loop", "once"),
            "canonical_frame": animation.get("canonical_frame"),
            "fps": animation.get("fps"),
            "path": root / record["output"]["path"],
            "pivot": record["geometry"]["runtime_pivot"],
            "canvas": [record["output"]["width"], record["output"]["height"]],
        })

    if not frames:
        raise SystemExit(f"no frames found for clip {args.clip!r} in the given specs")
    frames.sort(key=lambda frame: frame["index"])

    checks: dict[str, str] = {}
    notes: list[str] = []
    measured: dict = {}

    # --- the clip is complete and consistently declared ----------------------
    declared = {frame["frame_count"] for frame in frames}
    indices = [frame["index"] for frame in frames]
    checks["frame_count_agrees"] = "PASS" if len(declared) == 1 else "FAIL"
    if len(declared) != 1:
        notes.append(f"frames disagree about frame_count: {sorted(declared)}")

    expected = list(range(max(declared)))
    checks["frames_complete"] = "PASS" if indices == expected else "FAIL"
    if indices != expected:
        missing = sorted(set(expected) - set(indices))
        notes.append(f"frame indices are {indices}; expected {expected}"
                     + (f", missing {missing} (DECOMPOSITION_DEFECT)" if missing else ""))

    # --- mechanical alignment ------------------------------------------------
    canvases = {tuple(frame["canvas"]) for frame in frames}
    checks["shared_canvas"] = "PASS" if len(canvases) == 1 else "FAIL"
    if len(canvases) != 1:
        notes.append(f"frames were normalized onto different canvases: {sorted(canvases)}; "
                     f"the sprite jumps between frames (FAMILY_ALIGNMENT_DEFECT)")

    pivots = {tuple(frame["pivot"]) for frame in frames}
    drift = 0.0
    if len(pivots) > 1:
        base = frames[0]["pivot"]
        drift = max(max(abs(frame["pivot"][0] - base[0]), abs(frame["pivot"][1] - base[1]))
                    for frame in frames)
    measured["max_pivot_drift"] = round(drift, 6)
    checks["pivot_stable"] = "PASS" if drift <= args.pivot_tolerance else "FAIL"
    if drift > args.pivot_tolerance:
        notes.append(f"runtime_pivot drifts by {drift:.4f} across the clip; this is exactly what "
                     f"makes a walk cycle bob (FAMILY_ALIGNMENT_DEFECT, owner game-asset-normalizer)")

    images = {frame["asset_id"]: Image.open(frame["path"]) for frame in frames}
    boxes = {frame["asset_id"]: images[frame["asset_id"]].convert("RGBA").getbbox() for frame in frames}

    # --- pose continuity -----------------------------------------------------
    canonical_index = next((frame["canonical_frame"] for frame in frames
                            if frame["canonical_frame"] is not None), None)
    deltas = []
    for previous, current in zip(frames, frames[1:]):
        delta = symmetric_difference(images[previous["asset_id"]], images[current["asset_id"]])
        deltas.append({"from": previous["asset_id"], "to": current["asset_id"], "delta": round(delta, 4)})
    measured["inter_frame_delta"] = deltas

    duplicates = [step for step in deltas if step["delta"] < DUPLICATE_BELOW]
    checks["no_duplicate_frames"] = "PASS" if not duplicates else "FAIL"
    for step in duplicates:
        notes.append(f"{step['from']} and {step['to']} are the same drawing "
                     f"(silhouette delta {step['delta']}); the clip stutters here")

    # Measured, deliberately not decided.
    #
    # The obvious check is "a frame too far from the canonical pose is a redraw",
    # and it does not work. On this toolkit's own worked example a legitimate
    # end-of-travel frame sits 0.52 from the canonical pose while a frame
    # replaced with an entirely different shape sits 0.47 - the redraw is
    # *closer*. Core-coverage and monotonicity variants invert the same way.
    #
    # The reason is structural: when the moving part is a large share of the
    # silhouette, "posed far" and "redrawn" are not separable by silhouette
    # distance. What separates them is whether the region the AssetSpec calls
    # invariant survived, and no script can map `outer_frame_geometry` to pixels.
    #
    # So the numbers are surfaced and the verdict is left to whoever can look at
    # the frames. A tuned threshold here would pass on this example and mislead
    # on every clip shaped differently, which is the failure mode this toolkit
    # exists to prevent.
    checks["poses_share_a_subject"] = "INSUFFICIENT_EVIDENCE"
    if canonical_index is not None:
        canonical = next(frame for frame in frames if frame["index"] == canonical_index)
        measured["delta_from_canonical"] = [
            {"asset_id": frame["asset_id"], "index": frame["index"],
             "delta": round(symmetric_difference(
                 images[canonical["asset_id"]], images[frame["asset_id"]]), 4)}
            for frame in frames if frame["index"] != canonical_index
        ]
        notes.append(
            "delta_from_canonical is reported, not judged: silhouette distance cannot separate a "
            "far pose from a redraw. Compare the frames against the family's must_preserve list; "
            "a broken invariant is IDENTITY_DRIFT, owner game-asset-generator."
        )
    else:
        notes.append("no frame declares animation.canonical_frame, so there is no reference pose to "
                     "measure identity drift against")

    # Content sliding inside a fixed canvas reads as drift even when the pivot
    # is stable, because the pivot describes the canvas and not the drawing.
    spans = [max(box[2] - box[0], box[3] - box[1]) for box in boxes.values() if box]
    origins = [(box[0], box[1]) for box in boxes.values() if box]
    bbox_drift = max(max(abs(x - origins[0][0]), abs(y - origins[0][1])) for x, y in origins) if origins else 0
    measured["max_bbox_origin_drift_px"] = bbox_drift
    checks["bbox_drift_bounded"] = "PASS" if not spans or bbox_drift <= max(spans) * 0.25 else "FAIL"
    if checks["bbox_drift_bounded"] == "FAIL":
        notes.append(f"content origin moves {bbox_drift}px inside a fixed canvas; if the motion is "
                     f"intended it belongs in the runtime transform, not baked per frame")

    # --- loop closure --------------------------------------------------------
    loop_mode = frames[0]["loop"]
    if loop_mode == "loop" and len(frames) > 2:
        closure = symmetric_difference(images[frames[-1]["asset_id"]], images[frames[0]["asset_id"]])
        typical = sum(step["delta"] for step in deltas) / len(deltas)
        measured["loop_closure_delta"] = round(closure, 4)
        measured["typical_step_delta"] = round(typical, 4)
        checks["loop_closes"] = "PASS" if closure <= typical * 2.0 else "FAIL"
        if checks["loop_closes"] == "FAIL":
            notes.append(f"the last frame is {closure} away from the first while a typical step is "
                         f"{typical:.4f}; the loop visibly snaps")
    else:
        checks["loop_closes"] = "NOT_APPLICABLE"

    block = {
        "clip": {
            "id": args.clip,
            "frames": len(frames),
            "fps": frames[0]["fps"],
            "loop": loop_mode,
            "canonical_frame": canonical_index,
        },
        "tool": "skills/game-asset-normalizer/scripts/check_frames.py",
        "status": "fail" if any(result == "FAIL" for result in checks.values()) else "pass",
        "checks": checks,
        "measured": measured,
        "notes": notes,
    }
    print(yaml.safe_dump(block, sort_keys=False, allow_unicode=True).rstrip())

    failed = [name for name, result in checks.items() if result == "FAIL"]
    if failed:
        print(f"\n# FRAME CHECK FAILED for {args.clip}: {', '.join(failed)}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
