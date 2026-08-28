#!/usr/bin/env python3
"""Screen a freshly generated candidate for a real transparent background.

Run this immediately after generation, before normalization. The check is
deliberately tiny - four boolean tests over the alpha channel - because its
value is in *when* it runs, not in how clever it is. The same failure was
previously caught at QC, two stages downstream, after normalization had already
processed a candidate that was never going to pass.

The failure it catches is not "the model has no alpha channel". Targets that
support transparency still produce RGBA files with an opaque white background
painted in, because "transparent background" is a phrase that also describes
stock cutouts and editor screenshots. An asset can therefore be technically
RGBA and completely unusable.

    python3 check_alpha.py --candidate generation/AST-001/candidates/v1-c1.png
    python3 check_alpha.py --candidate cand.png --policy opaque

Exit 0 when the candidate satisfies the policy, 1 when it does not. A failure is
OUTPUT_TECHNICAL_FAILURE, owned by game-asset-generator, and it escalates to
G3_CHANGE_GENERATION_STRATEGY rather than G1 - re-rolling the prompt does not
fix a target that just drew a background.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - environment guard
    print("check_alpha.py requires Pillow: python3 -m pip install Pillow", file=sys.stderr)
    raise SystemExit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--policy", default="transparent",
                        choices=["transparent", "opaque", "runtime_composited"],
                        help="runtime.background_policy from the AssetSpec (default: transparent)")
    parser.add_argument("--min-transparent-ratio", type=float, default=0.02,
                        help="a real cutout leaves some empty canvas; below this the alpha is decorative")
    args = parser.parse_args()

    path = Path(args.candidate)
    image = Image.open(path)

    if args.policy != "transparent":
        print(f"alpha: NOT_APPLICABLE  {path.name}  (policy {args.policy})")
        return

    checks: dict[str, bool] = {}
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    width, height = rgba.size

    # 1. Does the file carry an alpha channel at all?
    checks["has_alpha_channel"] = image.mode in ("RGBA", "LA", "PA")

    # 2. Is any pixel actually fully transparent?
    checks["has_transparent_pixels"] = alpha.getextrema()[0] == 0

    # 3. Are the corners transparent? A painted-on background fails here even
    #    when the file is RGBA, which is the case the QC check used to catch
    #    only after normalization had already run.
    corners = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)]
    checks["corners_transparent"] = all(alpha.getpixel(xy) == 0 for xy in corners)

    # 4. Is the transparent area more than a rounding error? Guards against a
    #    single stray transparent pixel satisfying check 2.
    transparent_pixels = alpha.histogram()[0]
    ratio = transparent_pixels / (width * height)
    checks["transparent_ratio"] = ratio >= args.min_transparent_ratio

    failed = [name for name, ok in checks.items() if not ok]
    verdict = "FAIL" if failed else "PASS"
    print(f"alpha: {verdict}  {path.name}  {width}x{height} {image.mode}  "
          f"transparent {ratio:.1%}")
    for name, ok in checks.items():
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")

    if failed:
        print(
            "\n# OUTPUT_TECHNICAL_FAILURE - the candidate has a background.\n"
            "# Do not re-roll the prompt (G1); a target that drew a background will draw\n"
            "# one again. Escalate to G3_CHANGE_GENERATION_STRATEGY: use the target's\n"
            "# transparency option explicitly, or change the output strategy.",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
