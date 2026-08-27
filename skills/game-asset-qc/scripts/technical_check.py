#!/usr/bin/env python3
"""Deterministic technical conformance checks for a normalized runtime asset.

QC has two halves. One half is judgment - does this asset honor the art
direction, does the state read, is the family coherent. The other half is
arithmetic: dimensions, colour mode, alpha, clipping, transparency policy,
padding, hash lineage, contrast, and colour-vision separability.

Only the first half needs an agent. This script does the second half and emits
a `technical` block plus an `accessibility` block for the QC report, so the
agent spends its attention on the part that actually requires it.

    python3 technical_check.py \\
        --asset normalized/AST-001/runtime/AST-001.png \\
        --spec assets/specs/AST-001.yaml \\
        --record normalized/AST-001/normalization-record.yaml \\
        --project-root . \\
        [--sibling normalized/AST-002/runtime/AST-002.png ...] \\
        [--background "#2A2E35"]

Exit status 0 when every check passes, 1 on any FAIL. FAIL means the QC report
cannot be `approved`; it does not by itself decide the root owner.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment guard
    print("technical_check.py requires Pillow: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("technical_check.py requires pyyaml: python3 -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)

# Machado et al. colour-vision deficiency matrices (severity 1.0), applied in
# linear-ish sRGB. Good enough to catch a hue-only state distinction, which is
# the failure this check exists to find.
CVD_MATRICES = {
    "protanopia": ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047413),
                     (-0.011820, 0.042940, 0.968881)),
    "tritanopia": ((1.255528, -0.076749, -0.178779),
                   (-0.078411, 0.930809, 0.147602),
                   (0.004733, 0.691367, 0.303900)),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_luminance(rgb) -> float:
    def channel(value):
        srgb = value / 255.0
        return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(a, b) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def parse_color(text: str):
    text = text.strip().lstrip("#")
    if len(text) == 6:
        return tuple(int(text[i:i + 2], 16) for i in (0, 2, 4))
    raise SystemExit(f"unrecognized colour {text!r}; expected #RRGGBB")


def mean_visible_color(image: Image.Image):
    """Alpha-weighted mean colour of the visible pixels."""
    total = [0.0, 0.0, 0.0]
    weight = 0.0
    for r, g, b, a in list(image.convert("RGBA").getdata()):
        if a == 0:
            continue
        alpha = a / 255.0
        total[0] += r * alpha
        total[1] += g * alpha
        total[2] += b * alpha
        weight += alpha
    if weight == 0:
        return None
    return tuple(round(channel / weight) for channel in total)


def simulate_cvd(rgb, mode):
    matrix = CVD_MATRICES[mode]
    out = []
    for row in matrix:
        value = sum(component * channel for component, channel in zip(row, rgb))
        out.append(max(0, min(255, round(value))))
    return tuple(out)


def flatten_over(image: Image.Image, background, size):
    """Composite an RGBA asset over a solid background at the intended display size."""
    resized = image.convert("RGBA").resize(size, Image.LANCZOS)
    plate = Image.new("RGBA", size, tuple(background) + (255,))
    plate.alpha_composite(resized)
    return plate.convert("RGB")


def cvd_luminance_map(image: Image.Image, mode):
    """Perceptual luminance of an image after colour-vision-deficiency simulation."""
    pixels = list(image.getdata())
    return [
        0.2126 * s[0] + 0.7152 * s[1] + 0.0722 * s[2]
        for s in (simulate_cvd(p, mode) for p in pixels)
    ]


def state_separation(a: Image.Image, b: Image.Image, background, size, mode) -> float:
    """RMS luminance difference between two states as a colour-blind viewer sees them.

    Comparing mean colours would be the obvious implementation and it is wrong:
    two states that share a frame and differ only in panel geometry have nearly
    identical mean colour while being trivially distinguishable. What matters is
    whether the rendered results differ, so compare the images themselves.
    """
    left = cvd_luminance_map(flatten_over(a, background, size), mode)
    right = cvd_luminance_map(flatten_over(b, background, size), mode)
    squared = sum((x - y) ** 2 for x, y in zip(left, right))
    return (squared / len(left)) ** 0.5


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--asset", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--record", default=None, help="normalization-record.yaml for lineage verification")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--sibling", action="append", default=[],
                        help="sibling family member to compare state separability against")
    parser.add_argument("--background", action="append", default=[],
                        help="background colour the asset must stay readable against, as #RRGGBB")
    parser.add_argument("--min-contrast", type=float, default=3.0)
    parser.add_argument("--min-state-separation", type=float, default=8.0,
                        help="minimum RMS luminance separation between family states, at display size, "
                             "under colour-vision simulation")
    args = parser.parse_args()

    asset_path = Path(args.asset).resolve()
    spec = yaml.safe_load(Path(args.spec).read_text(encoding="utf-8"))
    asset_id = spec.get("asset_id", asset_path.stem)
    norm = spec.get("normalization") or {}
    runtime = spec.get("runtime") or {}

    checks: dict[str, str] = {}
    accessibility: list[dict] = []
    notes: list[str] = []

    image = Image.open(asset_path)
    rgba = image.convert("RGBA")

    # --- technical conformance ---------------------------------------------
    target = norm.get("target_canvas")
    if target:
        expected = (int(target["width"]), int(target["height"]))
        checks["canvas_dimensions"] = "PASS" if image.size == expected else "FAIL"
        if image.size != expected:
            notes.append(f"canvas is {image.size}, spec requires {expected}")
    else:
        checks["canvas_dimensions"] = "INSUFFICIENT_EVIDENCE"

    background_policy = runtime.get("background_policy", "transparent")
    alpha_extrema = rgba.getchannel("A").getextrema()
    if background_policy == "transparent":
        checks["alpha_mode"] = "PASS" if image.mode in ("RGBA", "LA", "PA") else "FAIL"
        checks["has_transparency"] = "PASS" if alpha_extrema[0] == 0 else "FAIL"
    elif background_policy == "opaque":
        checks["alpha_mode"] = "PASS" if alpha_extrema[0] == 255 else "FAIL"
        checks["has_transparency"] = "NOT_APPLICABLE"
    else:
        checks["alpha_mode"] = "NOT_APPLICABLE"
        checks["has_transparency"] = "NOT_APPLICABLE"

    bbox = rgba.getbbox()
    if bbox is None:
        checks["content_present"] = "FAIL"
        notes.append("asset is fully transparent")
    else:
        checks["content_present"] = "PASS"
        touches_edge = bbox[0] == 0 or bbox[1] == 0 or bbox[2] == image.width or bbox[3] == image.height
        if background_policy == "transparent":
            checks["no_edge_clipping"] = "FAIL" if touches_edge else "PASS"
            if touches_edge:
                notes.append(f"content bbox {bbox} touches the canvas edge; padding or trim may have clipped it")
        else:
            checks["no_edge_clipping"] = "NOT_APPLICABLE"

        padding = int(norm.get("padding", 0))
        if padding and background_policy == "transparent":
            inside = (
                bbox[0] >= padding and bbox[1] >= 0
                and bbox[2] <= image.width - padding and bbox[3] <= image.height
            )
            checks["padding_respected"] = "PASS" if inside else "FAIL"
        else:
            checks["padding_respected"] = "NOT_APPLICABLE"

    # --- lineage ------------------------------------------------------------
    if args.record:
        record = yaml.safe_load(Path(args.record).read_text(encoding="utf-8"))
        recorded = (record.get("output") or {}).get("content_hash")
        actual = sha256_file(asset_path)
        checks["lineage_hash_matches"] = "PASS" if recorded == actual else "FAIL"
        if recorded != actual:
            notes.append(
                f"normalization record claims {recorded}, asset on disk is {actual}; "
                f"this QC run would be judging a different file than the record describes"
            )
        checks["normalization_validation_passed"] = (
            "PASS" if (record.get("validation") or {}).get("status") == "pass" else "FAIL"
        )
    else:
        checks["lineage_hash_matches"] = "INSUFFICIENT_EVIDENCE"
        checks["normalization_validation_passed"] = "INSUFFICIENT_EVIDENCE"

    # --- accessibility ------------------------------------------------------
    mean_color = mean_visible_color(rgba) if bbox else None
    a11y_required = (spec.get("accessibility") or {}).get("gameplay_critical", False)

    if mean_color and args.background:
        worst = None
        for raw in args.background:
            ratio = contrast_ratio(mean_color, parse_color(raw))
            worst = ratio if worst is None else min(worst, ratio)
        result = "PASS" if worst >= args.min_contrast else "FAIL"
        accessibility.append({
            "check_id": "A11Y_CONTRAST",
            "result": result,
            "measured": round(worst, 2),
            "evidence": f"alpha-weighted mean {mean_color} against {len(args.background)} declared background(s), "
                        f"floor {args.min_contrast}",
        })
    elif a11y_required:
        accessibility.append({
            "check_id": "A11Y_CONTRAST",
            "result": "INSUFFICIENT_EVIDENCE",
            "measured": None,
            "evidence": "no --background declared for a gameplay-critical asset",
        })

    if args.sibling:
        display = runtime.get("intended_display_size") or {}
        size = (int(display.get("width", 64)), int(display.get("height", 64)))
        backgrounds = [parse_color(raw) for raw in args.background] or [(128, 128, 128)]

        worst = None
        for sibling_path in args.sibling:
            sibling = Image.open(sibling_path)
            for background in backgrounds:
                for mode in CVD_MATRICES:
                    separation = state_separation(rgba, sibling, background, size, mode)
                    if worst is None or separation < worst[0]:
                        worst = (separation, mode, Path(sibling_path).stem, background)
        if worst is not None:
            separation, mode, sibling_id, background = worst
            result = "PASS" if separation >= args.min_state_separation else "FAIL"
            accessibility.append({
                "check_id": "A11Y_COLOR_VISION",
                "result": result,
                "measured": round(separation, 2),
                "evidence": f"RMS luminance separation from {sibling_id} at {size[0]}x{size[1]} under "
                            f"{mode} simulation over #{'%02X%02X%02X' % background}, "
                            f"floor {args.min_state_separation}",
            })
            if result == "FAIL":
                notes.append(
                    f"states are not separable without colour: at {size[0]} px under {mode}, this asset "
                    f"differs from {sibling_id} by only {separation:.2f} RMS luminance. A gameplay-critical "
                    f"distinction needs a channel that survives colour-vision deficiency "
                    f"(value, shape, icon, or motion)."
                )

    channels = ((spec.get("state") or {}).get("encoding_channels") or [])
    if a11y_required and channels:
        non_color = [c for c in channels if c != "hue"]
        accessibility.append({
            "check_id": "A11Y_NON_COLOR_CHANNEL",
            "result": "PASS" if non_color else "FAIL",
            "measured": ",".join(channels),
            "evidence": "state.encoding_channels declares a non-hue channel" if non_color
                        else "state.encoding_channels declares hue only",
        })

    # --- output -------------------------------------------------------------
    failed = [name for name, result in checks.items() if result == "FAIL"]
    failed += [f"{item['check_id']}" for item in accessibility if item["result"] == "FAIL"]

    block = {
        "technical": {
            "tool": "skills/game-asset-qc/scripts/technical_check.py",
            "status": "fail" if failed else "pass",
            "checks": checks,
        },
        "accessibility": accessibility,
        "measured": {
            "size": list(image.size),
            "mode": image.mode,
            "content_bbox": list(bbox) if bbox else None,
            "mean_visible_color": list(mean_color) if mean_color else None,
            "bytes": asset_path.stat().st_size,
            "content_hash": sha256_file(asset_path),
        },
        "notes": notes,
    }

    print(yaml.safe_dump(block, sort_keys=False, allow_unicode=True).rstrip())
    if failed:
        print(f"\n# TECHNICAL CHECK FAILED for {asset_id}: {', '.join(failed)}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
