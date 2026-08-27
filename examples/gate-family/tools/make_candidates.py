#!/usr/bin/env python3
"""Produce the example's generation candidates deterministically.

The worked example needs real image bytes so the hashes, geometry reports, and
QC measurements in it are real rather than plausible-looking placeholders. No
image model runs in CI, so this script stands in for one.

That substitution is recorded honestly in each generation record:

    provenance:
      capability: deterministic-script
      model: examples/gate-family/tools/make_candidates.py
      seed: 0

which is exactly what the generator skill requires - provenance describes what
actually happened, never what would look impressive.

The three states differ in panel geometry, not only in colour, so the family
also demonstrates a state encoding that survives colour-vision simulation.

    python3 examples/gate-family/tools/make_candidates.py
"""

from __future__ import annotations

from pathlib import Path
import random

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]

FRAME = (168, 144, 112, 255)
FRAME_SHADOW = (126, 106, 82, 255)
PANEL = (216, 176, 133, 255)
PANEL_EDGE = (176, 138, 98, 255)
BOLT = (240, 228, 204, 255)


def grain(image: Image.Image, seed: int, amount: int = 7) -> None:
    """Restrained per-pixel value jitter, standing in for authored tactile grain."""
    rng = random.Random(seed)
    pixels = image.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if a == 0:
                continue
            delta = rng.randint(-amount, amount)
            pixels[x, y] = (
                max(0, min(255, r + delta)),
                max(0, min(255, g + delta)),
                max(0, min(255, b + delta)),
                a,
            )


def gate(state: str, seed: int) -> Image.Image:
    size = 512
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Outer frame: identical across the family. This is the invariant the
    # family contract protects, and the thing QC compares siblings on.
    left, top, right, bottom = 96, 64, 416, 448
    thickness = 34
    draw.rectangle([left, top, right, bottom], fill=FRAME_SHADOW)
    draw.rectangle([left + 6, top + 6, right - 6, bottom - 6], fill=FRAME)
    draw.rectangle(
        [left + thickness, top + thickness, right - thickness, bottom - thickness],
        fill=(0, 0, 0, 0),
    )

    opening = (left + thickness, top + thickness, right - thickness, bottom - thickness)
    opening_height = opening[3] - opening[1]

    # State is carried by panel geometry - a shape channel, not a hue channel.
    if state == "closed":
        panel_bottom = opening[3]
    elif state == "transition":
        panel_bottom = opening[1] + int(opening_height * 0.45)
    elif state == "open":
        panel_bottom = opening[1] + int(opening_height * 0.12)
    else:
        raise SystemExit(f"unknown state {state!r}")

    if panel_bottom > opening[1]:
        draw.rectangle([opening[0], opening[1], opening[2], panel_bottom], fill=PANEL)
        draw.rectangle([opening[0], opening[1], opening[2], panel_bottom], outline=PANEL_EDGE, width=5)
        # Bolts read as a secondary shape cue at small display sizes.
        for bolt_x in (opening[0] + 26, opening[2] - 26):
            for offset in range(opening[1] + 28, panel_bottom - 12, 84):
                draw.ellipse([bolt_x - 7, offset - 7, bolt_x + 7, offset + 7], fill=BOLT)

    grain(image, seed)
    return image


def main() -> None:
    for index, state in enumerate(("closed", "transition", "open")):
        asset_id = f"AST-GATE-{state.upper()}"
        out_dir = ROOT / "generation" / asset_id / "candidates"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "v1-c1.png"
        gate(state, seed=index).save(path, format="PNG", optimize=True)
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
