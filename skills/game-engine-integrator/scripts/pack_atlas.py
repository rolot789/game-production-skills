#!/usr/bin/env python3
"""Pack QC-approved normalized assets into a real texture atlas.

Before this script the stage claimed atlas packing and shipped no packer.
`budget_check.py` reported `atlas_count: 0` and put the largest *sprite*
dimension under `max_atlas_dimension`, then compared it against the atlas
budget - a check that passes for a reason unrelated to the risk it names,
which is worse than no check because it reads green.

Membership is not this script's decision. Draw order, lifetime, and scene
locality decide which assets belong in one atlas, and those are judgments the
agent makes from the integration plan. This script takes the members it is
given and does the part that is arithmetic: placement, padding, dimensions,
and hashing.

    python3 pack_atlas.py --project-root . --atlas-id FAM-GATE \\
        --member AST-GATE-CLOSED --member AST-GATE-OPEN

Exit 0 when the atlas was written and fits the declared budget, 1 when a
member is ineligible or the atlas cannot fit `max_atlas_dimension`.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment guard
    print("pack_atlas.py requires Pillow: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("pack_atlas.py requires pyyaml: python3 -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

QC_PROMOTES = ("approved", "approved_with_minor_findings")

# Below this, bilinear filtering samples a neighbour's pixels at non-integer
# scales and members bleed into each other. It is the most common atlas defect
# and the cheapest to prevent.
MIN_SAFE_PADDING = 2


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def shelf_pack(boxes: list[tuple[str, int, int]], width: int, padding: int):
    """Place boxes on horizontal shelves. Returns placements or None if too tall.

    Shelf packing rather than MaxRects on purpose: the result must be identical
    on every machine and every run, because the atlas image is hashed and a
    packer that reorders under equal-area ties would make the atlas differ
    without any input differing.
    """
    placements = {}
    x = y = shelf_height = 0
    for asset_id, box_w, box_h in boxes:
        if box_w + 2 * padding > width:
            return None
        if x + box_w + 2 * padding > width:
            x = 0
            y += shelf_height
            shelf_height = 0
        placements[asset_id] = (x + padding, y + padding, box_w, box_h)
        x += box_w + 2 * padding
        shelf_height = max(shelf_height, box_h + 2 * padding)
    return placements, y + shelf_height


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--atlas-id", required=True)
    parser.add_argument("--member", action="append", required=True,
                        help="asset id to include; repeat once per member")
    parser.add_argument("--target-id", default=None)
    parser.add_argument("--padding", type=int, default=MIN_SAFE_PADDING)
    parser.add_argument("--max-dimension", type=int, default=None,
                        help="defaults to project.yaml budgets.max_atlas_dimension")
    parser.add_argument("--power-of-two", action="store_true",
                        help="round atlas dimensions up to a power of two; needed by targets using "
                             "compressed texture formats or older GL, wasteful otherwise")
    parser.add_argument("--dry-run", action="store_true")
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
    max_dimension = args.max_dimension or budgets.get("max_atlas_dimension")

    normalized_root = root / paths.get("normalized", "normalized/")
    qc_root = root / paths.get("qc", "qc/")
    out_dir = root / paths.get("engine_integration", "engine-integration/") / args.atlas_id

    notes: list[str] = []
    if args.padding < MIN_SAFE_PADDING:
        notes.append(
            f"padding is {args.padding} px; below {MIN_SAFE_PADDING} px neighbouring members bleed "
            f"under bilinear filtering at non-integer scale"
        )

    # ---- eligibility ------------------------------------------------------
    # An atlas built from assets whose QC does not describe them is an atlas of
    # unverified pixels. This is the same lineage rule the stage already states
    # in prose; here it is enforced before any packing happens.
    members = []
    for asset_id in args.member:
        source = normalized_root / asset_id / "runtime" / f"{asset_id}.png"
        if not source.exists():
            raise SystemExit(f"{asset_id}: no normalized runtime asset at {source.relative_to(root)}")
        source_hash = sha256_file(source)

        qc_path = qc_root / asset_id / "qc-report.yaml"
        if not qc_path.exists():
            raise SystemExit(f"{asset_id}: no QC report at {qc_path.relative_to(root)}; "
                             f"only QC-approved assets may be packed")
        qc = yaml.safe_load(qc_path.read_text(encoding="utf-8"))
        if qc.get("status") not in QC_PROMOTES:
            raise SystemExit(f"{asset_id}: QC status {qc.get('status')!r} does not promote")
        evaluated = ((qc.get("evaluated") or {}).get("normalized_output") or {}).get("content_hash")
        if evaluated != source_hash:
            raise SystemExit(
                f"{asset_id}: the QC report evaluated {evaluated}, the file on disk is {source_hash}. "
                f"That QC verdict does not describe this asset."
            )

        with Image.open(source) as image:
            width, height = image.size
        member = {
            "asset_id": asset_id,
            "source": str(source.relative_to(root)),
            "content_hash": source_hash,
            "width": width,
            "height": height,
        }

        # An animation frame carries its ordering in the AssetSpec. Without it
        # the manifest is a bag of rects and the engine has no way to know which
        # rect is frame 0 - which is the difference between an atlas and a
        # usable sprite sheet.
        spec_path = root / f"{paths.get('asset_specs', 'assets/specs/')}{asset_id}.yaml"
        if spec_path.exists():
            animation = (yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}).get("animation")
            if animation:
                member["animation"] = animation
        members.append(member)

    # ---- packing ----------------------------------------------------------
    # Tallest first is what makes shelf packing tight; the id breaks ties so the
    # order - and therefore the atlas bytes - is stable across runs.
    boxes = sorted(
        ((m["asset_id"], m["width"], m["height"]) for m in members),
        key=lambda box: (-box[2], box[0]),
    )
    widest = max(m["width"] for m in members) + 2 * args.padding

    # Candidate widths: the prefix sums of the boxes (every width at which one
    # more member fits on a row), plus the powers of two, which are what a
    # target needing POT textures can actually use. Trying only powers of two
    # wasted more than half the sheet on a three-member family.
    candidates = set()
    running = 0
    for _, box_w, _ in boxes:
        running += box_w + 2 * args.padding
        candidates.add(max(running, widest))
    power = 1
    while power <= (max_dimension or 8192):
        if power >= widest:
            candidates.add(power)
        power *= 2

    def round_up(value: int) -> int:
        if not args.power_of_two:
            return value
        result = 1
        while result < value:
            result *= 2
        return result

    best = None
    for width in sorted(candidates):
        width = round_up(width)
        if max_dimension is not None and width > max_dimension:
            continue
        packed = shelf_pack(boxes, width, args.padding)
        if packed is None:
            continue
        placements, used_height = packed
        height = round_up(used_height)
        if max_dimension is not None and height > max_dimension:
            continue
        # Smallest area wins; the remaining keys only break ties, so the chosen
        # atlas - and therefore its hash - does not depend on set iteration order.
        key = (width * height, max(width, height), width)
        if best is None or key < best[0]:
            best = (key, width, height, placements)

    if best is None:
        print(
            f"ATLAS PACK FAILED for {args.atlas_id}: members do not fit within "
            f"max_atlas_dimension {max_dimension}.\n"
            f"# This is BUDGET_VIOLATION. If it cannot be met without changing asset content, "
            f"reroute to DECOMPOSITION_DEFECT or REPRESENTATION_STRATEGY_DEFECT - never "
            f"re-encode or downscale QC-approved pixels to fit.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    _, atlas_w, atlas_h, placements = best

    for member in members:
        x, y, width, height = placements[member["asset_id"]]
        member["rect"] = {"x": x, "y": y, "width": width, "height": height}
    members.sort(key=lambda m: m["asset_id"])

    # Group animation frames into ordered clips with their timing. This is what
    # makes the manifest a frame map rather than a packing report: engine-target
    # policy already describes the atlas manifest as "a single sprite sheet plus
    # a JSON frame map", and until now it was only the first half.
    clips = {}
    for member in members:
        animation = member.get("animation")
        if not animation:
            continue
        clip = clips.setdefault(animation["clip_id"], {
            "clip_id": animation["clip_id"],
            "frame_count": animation["frame_count"],
            "fps": animation.get("fps"),
            "loop": animation.get("loop", "once"),
            "canonical_frame": animation.get("canonical_frame"),
            "frames": [],
        })
        clip["frames"].append({
            "index": animation["frame_index"],
            "asset_id": member["asset_id"],
            "rect": member["rect"],
            "hold_frames": animation.get("hold_frames", 1),
        })

    for clip in clips.values():
        clip["frames"].sort(key=lambda frame: frame["index"])
        declared = clip["frame_count"]
        present = [frame["index"] for frame in clip["frames"]]
        if present != list(range(declared)):
            # Packing an incomplete clip produces a sheet that plays wrong, so
            # it fails here rather than being discovered in the game.
            print(
                f"ATLAS PACK FAILED for {args.atlas_id}: clip {clip['clip_id']} declares "
                f"{declared} frames but the atlas contains {present}.\n"
                f"# Pack every frame of a clip together, or the frame map indexes frames "
                f"that are not in this sheet.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        if clip["fps"]:
            clip["duration_ms"] = round(
                sum(frame["hold_frames"] for frame in clip["frames"]) * 1000 / clip["fps"], 3)

    manifest = {
        "schema_version": 3,
        "atlas_id": args.atlas_id,
        "target": {"id": target_id, "engine": engine.get("target", "custom")},
        "atlas": {
            "path": None,
            "width": atlas_w,
            "height": atlas_h,
            "content_hash": None,
            "estimated_texture_memory_bytes": atlas_w * atlas_h * 4,
        },
        "padding_px": args.padding,
        "power_of_two": args.power_of_two,
        "members": members,
        "clips": list(clips.values()),
        "packer": {
            "algorithm": "shelf, tallest-first, id-stable",
            "tool": "skills/game-engine-integrator/scripts/pack_atlas.py",
        },
        "notes": notes,
    }

    if args.dry_run:
        print(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).rstrip())
        return

    atlas = Image.new("RGBA", (atlas_w, atlas_h), (0, 0, 0, 0))
    for member in members:
        with Image.open(root / member["source"]) as sprite:
            atlas.paste(sprite.convert("RGBA"), (member["rect"]["x"], member["rect"]["y"]))

    out_dir.mkdir(parents=True, exist_ok=True)
    atlas_path = out_dir / f"{args.atlas_id}.png"
    atlas.save(atlas_path, format="PNG", optimize=True)

    manifest["atlas"]["path"] = str(atlas_path.relative_to(root))
    manifest["atlas"]["content_hash"] = sha256_file(atlas_path)
    (out_dir / "atlas-manifest.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")

    occupied = sum(m["width"] * m["height"] for m in members)
    print(f"packed {args.atlas_id}: {len(members)} members  {atlas_w}x{atlas_h}  "
          f"padding {args.padding}px  fill {occupied / (atlas_w * atlas_h):.0%}")
    for clip in clips.values():
        print(f"- clip     {clip['clip_id']}  {len(clip['frames'])} frames  "
              f"{clip['fps']} fps  {clip['loop']}")
    print(f"- atlas    {manifest['atlas']['path']}  {manifest['atlas']['content_hash'][:12]}")
    print(f"- manifest {(out_dir / 'atlas-manifest.yaml').relative_to(root)}")
    for note in notes:
        print(f"! {note}")


if __name__ == "__main__":
    main()
