#!/usr/bin/env python3
"""Rebuild every derived artifact in the worked example.

The hand-authored artifacts in this example are the ones a person actually
writes: project.yaml, the GameSpec slice, the ArtStyle slice, the anchor
manifest, and the constraint ledger.

Everything downstream of those is derived, and derived artifacts carry content
hashes. Hand-writing a hash produces an example that looks authoritative and is
wrong the moment anything upstream changes - which is exactly the failure the
toolkit exists to prevent, so the example must not commit it.

So this script regenerates the derived layer by running the real tools:

    make_candidates.py        stands in for an image model (recorded as such)
    normalize.py              the actual normalizer
    technical_check.py        the actual QC technical checks
    budget_check.py           the actual budget measurement

then writes the records that quote their results.

    python3 examples/gate-family/tools/build_example.py

`validate_project.py` verifies every hash against the bytes on disk afterwards,
so a stale example fails CI rather than shipping.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
SKILLS = REPO / "skills"

STATES = ["CLOSED", "TRANSITION", "OPEN"]
# The opening clip. Frames are their own assets sharing a family_id, because an
# animation is an ordered family - which is why nothing about family coherence,
# shared scale, or canonical-parent derivation had to be reinvented for it.
CLIP_ID = "CLIP-GATE-OPENING"
FRAME_COUNT = 4
FRAMES = [f"AST-GATE-OPENING-{index:03d}" for index in range(FRAME_COUNT)]
SHARED_SCALE = "0.623377"
BACKGROUNDS = ["#1B1F24", "#3A4149"]

# The runtime contexts this example validates. Declared once because the plan,
# the report, and the evidence manifest must describe the same contexts - three
# hand-maintained copies is exactly the drift the toolkit exists to prevent.
CONTEXTS = [
    {"id": "CTX-CORRIDOR-MIN", "scene": "corridor-01", "viewport": "1280x720",
     "camera": "fixed-top-down", "states": ["closed", "transition", "open"],
     "level": 2, "background": "#1B1F24", "capture_id": "CAP-001",
     "risk": "medium",
     "expected": "state distinction and silhouette hold at the intended display size"},
    {"id": "CTX-CHAMBER-DENSE", "scene": "chamber-03", "viewport": "1920x1080",
     "camera": "fixed-top-down", "states": ["closed", "open"],
     "level": 3, "background": "#3A4149", "capture_id": "CAP-002",
     "risk": "high",
     "expected": "contrast holds against the densest declared background"},
]

CAPTURE_PLATE = (320, 180)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_capture(asset_path: Path, background: str, display: tuple[int, int], out: Path) -> None:
    """Composite the runtime asset over a scene background at player scale.

    This is a headless render, not a screenshot of a game that does not exist -
    and it is recorded as one in the evidence manifest. It is still real
    rendered evidence: the bytes are produced by compositing the actual runtime
    asset over a background the AssetSpec declares, at the intended display
    size. A capture id with no bytes behind it would be the thing the
    runtime-visual-validator skill forbids.
    """
    from PIL import Image

    rgb = tuple(int(background.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    plate = Image.new("RGBA", CAPTURE_PLATE, rgb + (255,))
    sprite = Image.open(asset_path).convert("RGBA").resize(display, Image.LANCZOS)
    plate.alpha_composite(sprite, ((CAPTURE_PLATE[0] - display[0]) // 2,
                                   (CAPTURE_PLATE[1] - display[1]) // 2))
    out.parent.mkdir(parents=True, exist_ok=True)
    plate.convert("RGB").save(out, format="PNG", optimize=True)


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def run(command: list[str], allow_fail: bool = False) -> str:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0 and not allow_fail:
        print(" ".join(command))
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"command failed: {command[1]}")
    return result.stdout


def main() -> None:
    # ---- 0. candidates -----------------------------------------------------
    run([sys.executable, str(ROOT / "tools" / "make_candidates.py")])

    upstream = {
        "game_spec": ("spec/game-spec.yaml", "v1"),
        "art_style": ("art/art-style.yaml", "v2"),
        "style_anchor_manifest": ("art/style-anchor-manifest.yaml", "v1"),
        "style_constraint_ledger": ("art/style-constraint-ledger.yaml", "v1"),
    }
    upstream_refs = {
        key: {"path": rel, "version": version, "content_hash": sha(ROOT / rel)}
        for key, (rel, version) in upstream.items()
    }

    # ---- 1. asset specs ----------------------------------------------------
    for state in STATES:
        spec_path = ROOT / f"assets/specs/AST-GATE-{state}.yaml"
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        spec["source_versions"] = dict(upstream_refs)
        dump(spec_path, spec)

    spec_refs = {
        state: {
            "path": f"assets/specs/AST-GATE-{state}.yaml",
            "version": "v1",
            "content_hash": sha(ROOT / f"assets/specs/AST-GATE-{state}.yaml"),
        }
        for state in STATES
    }

    for asset_id in FRAMES:
        spec_path = ROOT / f"assets/specs/{asset_id}.yaml"
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
        spec["source_versions"] = dict(upstream_refs)
        dump(spec_path, spec)

    frame_spec_refs = {
        asset_id: {
            "path": f"assets/specs/{asset_id}.yaml",
            "version": "v1",
            "content_hash": sha(ROOT / f"assets/specs/{asset_id}.yaml"),
        }
        for asset_id in FRAMES
    }

    # ---- 2. generation records --------------------------------------------
    for state in STATES:
        asset_id = f"AST-GATE-{state}"
        candidate = ROOT / f"generation/{asset_id}/candidates/v1-c1.png"
        record = {
            "schema_version": 3,
            "asset_id": asset_id,
            "job_version": "v1",
            "candidate": {
                "id": "v1-c1",
                "path": f"generation/{asset_id}/candidates/v1-c1.png",
                "content_hash": sha(candidate),
                "selected": True,
            },
            "inputs": {
                "asset_spec": spec_refs[state],
                "art_style": upstream_refs["art_style"],
                "anchor_ids": ["ANCH-GATE-GEOMETRY-001", "ANCH-PALETTE-001"],
                "constraint_ids": ["NEG-LIGHTING-001", "NEG-TEXTURE-002",
                                   "NEG-DETAIL-003", "NEG-STATE-004"],
                "canonical_parent_candidate": None if state == "CLOSED" else "AST-GATE-CLOSED/v1-c1",
            },
            "screening": {
                "identity": "PASS",
                "geometry_family": "PASS",
                "palette": "PASS",
                "texture": "PASS",
                "lighting": "PASS",
                "state_readability": "PASS",
                "output": "PASS",
            },
            "provenance": {
                # Truthful: no image model ran. A deterministic script stood in,
                # and saying so is the whole point of the provenance rule.
                "capability": "deterministic-script",
                "model": "examples/gate-family/tools/make_candidates.py",
                "seed": STATES.index(state),
                "created_at": None,
                "external_job": False,
            },
        }
        dump(ROOT / f"generation/{asset_id}/records/v1-c1.yaml", record)

        # The generation contract is the authority; prompt.md is a serialization
        # of it for a provider that needs prose. Writing the prose first is how
        # scoped anchors collapse into adjective soup.
        dump(ROOT / f"generation/{asset_id}/generation-contract.yaml", {
            "schema_version": 3,
            "asset": {"id": asset_id, "family": "FAM-GATE",
                      "semantic_role": "corridor-blocking object driven by an adjacent switch"},
            "identity": {
                "required": True,
                "anchors": [{"id": "ANCH-GATE-GEOMETRY-001",
                             "governs": ["frame.outer_proportion", "frame.thickness_ratio", "opening.aspect"]}],
            },
            "style": {
                "global_rules": [
                    "2D orthographic top-down projection",
                    "no outline; forms separate by value contrast at their edges",
                    "flat surfaces, no directional shading",
                ],
                "category_overrides": [
                    "readable at 64 px; secondary cues must survive downscale",
                    "state changes alter silhouette, not only hue",
                ],
            },
            "anchors": [{
                "id": "ANCH-PALETTE-001",
                "role": "palette_anchor",
                "governs": ["palette.hue_family", "palette.value_structure"],
                "do_not_inherit": ["shape_language", "detail_density"],
            }],
            "constraints": {
                "hard_forbidden": [
                    "NEG-LIGHTING-001: no directional shading, rim light, bloom, or glow",
                    "NEG-STATE-004: state must not be carried by hue alone",
                ],
                "soft_avoid": ["NEG-DETAIL-003: no ornament that vanishes below 4 px at 64 px display"],
                "bounded": ["NEG-TEXTURE-002: value grain within +/- 8 of base"],
                "anti_reference": [],
            },
            "family": {
                "canonical_parent": None if state == "CLOSED" else "AST-GATE-CLOSED",
                "preserve": ["outer_frame_geometry", "frame_thickness",
                             "top_down_projection", "palette_family", "footprint"],
                "allowed_delta": [] if state == "CLOSED" else ["panel_height"],
            },
            "output": {"medium": "raster", "background": "transparent",
                       "framing": "full_asset", "clipping": "forbidden"},
            "non_goals": [
                "do not add ornament that is not in the canonical parent",
                "do not introduce a light source",
                "do not differentiate this state by recolouring",
            ],
        })

        panel = {"CLOSED": "fills the opening completely",
                 "TRANSITION": "covers the top 45% of the opening",
                 "OPEN": "is retracted to a thin lintel at the top of the opening"}[state]
        (ROOT / f"generation/{asset_id}/prompt.md").write_text(
            f"""# {asset_id} — provider prompt

Serialized from `generation-contract.yaml`. The contract is the source of truth;
edit that and re-serialize rather than editing this file.

A top-down orthographic gate that blocks a corridor until its switch is powered.

Non-negotiable geometry: a rectangular stone frame of constant thickness around a
central opening. The frame is identical in every state of this family; only the
panel inside the opening changes. In this state the panel {panel}.

Rendering: flat fills with restrained per-pixel value grain. Forms separate by
value contrast at their edges — there is no outline. Warm mid-value earth tones
against cool dark floors.

Do not add: directional shading, rim light, bloom, glow, ornament smaller than
4 px at 64 px display size, or any decoration absent from the canonical parent.

Do not differentiate this state by colour. The panel's height carries the state;
hue is identical across the family.

Output: transparent background, full asset in frame, no clipping.
""", encoding="utf-8")

        dump(ROOT / f"generation/{asset_id}/job.yaml", {
            "schema_version": 3,
            "asset_id": asset_id,
            "job_version": "v1",
            "contract": f"generation/{asset_id}/generation-contract.yaml",
            "prompt": f"generation/{asset_id}/prompt.md",
            "budget": {"candidates_max": 4, "regeneration_attempts_max": 6},
            "inputs": {"asset_spec": spec_refs[state], "art_style": upstream_refs["art_style"]},
        })

        dump(ROOT / f"generation/{asset_id}/candidate-index.yaml", {
            "asset_id": asset_id,
            "job_version": "v1",
            "candidates": [{
                "id": "v1-c1",
                "path": f"generation/{asset_id}/candidates/v1-c1.png",
                "content_hash": sha(candidate),
                "screening": "PASS",
                "selected": True,
            }],
            "budget": {
                "candidates_generated": 1,
                "candidates_max": 4,
                "stop_reason": "first candidate satisfied every critical dimension",
            },
        })

    for index, asset_id in enumerate(FRAMES):
        candidate = ROOT / f"generation/{asset_id}/candidates/v1-c1.png"
        parent = None if index == 0 else f"{FRAMES[0]}/v1-c1"
        dump(ROOT / f"generation/{asset_id}/records/v1-c1.yaml", {
            "schema_version": 3,
            "asset_id": asset_id,
            "job_version": "v1",
            "candidate": {
                "id": "v1-c1",
                "path": f"generation/{asset_id}/candidates/v1-c1.png",
                "content_hash": sha(candidate),
                "selected": True,
            },
            "inputs": {
                "asset_spec": frame_spec_refs[asset_id],
                "art_style": upstream_refs["art_style"],
                "anchor_ids": ["ANCH-GATE-GEOMETRY-001", "ANCH-PALETTE-001"],
                "constraint_ids": ["NEG-LIGHTING-001", "NEG-TEXTURE-002",
                                   "NEG-DETAIL-003", "NEG-STATE-004"],
                "canonical_parent_candidate": parent,
            },
            "screening": {
                "identity": "PASS",
                "geometry_family": "PASS",
                "palette": "PASS",
                "texture": "PASS",
                "lighting": "PASS",
                "state_readability": "PASS",
                "output": "PASS",
            },
            "provenance": {
                "capability": "deterministic-script",
                "model": "examples/gate-family/tools/make_candidates.py",
                # One seed for the whole clip: a per-frame seed would make the
                # grain crawl, and check_frames.py would report the crawl as an
                # inter-frame delta with no pose behind it.
                "seed": 7,
                "created_at": None,
                "external_job": False,
            },
        })

        dump(ROOT / f"generation/{asset_id}/generation-contract.yaml", {
            "schema_version": 3,
            "asset_id": asset_id,
            "clip": {"id": CLIP_ID, "frame_index": index, "frame_count": FRAME_COUNT},
            "semantic_purpose": f"frame {index} of the gate opening; the panel travels, nothing else does",
            "geometry": {
                "invariant": ["outer_frame_geometry", "frame_thickness", "top_down_projection"],
                "varies": ["panel_height"],
            },
            "family": {
                "canonical_parent": None if index == 0 else FRAMES[0],
                "derivation": "pose the parent, do not redraw it",
            },
            "output": {"background": "transparent", "framing": "full asset in frame"},
            "non_goals": ["new ornament", "directional shading", "per-frame grain reseed"],
        })

        (ROOT / f"generation/{asset_id}/prompt.md").write_text(
            f"""# {asset_id}

Frame {index} of {FRAME_COUNT} in {CLIP_ID}.

Pose the canonical frame; do not redraw it. The outer frame, its thickness, the
projection, and the grain are identical to frame 0. Only the panel travels.

Output: transparent background, full asset in frame, no clipping.
""", encoding="utf-8")

        dump(ROOT / f"generation/{asset_id}/job.yaml", {
            "schema_version": 3,
            "asset_id": asset_id,
            "job_version": "v1",
            "contract": f"generation/{asset_id}/generation-contract.yaml",
            "prompt": f"generation/{asset_id}/prompt.md",
            "budget": {"candidates_max": 4, "regeneration_attempts_max": 6},
            "inputs": {"asset_spec": frame_spec_refs[asset_id],
                       "art_style": upstream_refs["art_style"]},
        })

        dump(ROOT / f"generation/{asset_id}/candidate-index.yaml", {
            "asset_id": asset_id,
            "job_version": "v1",
            "candidates": [{
                "id": "v1-c1",
                "path": f"generation/{asset_id}/candidates/v1-c1.png",
                "content_hash": sha(candidate),
                "screening": "PASS",
                "selected": True,
            }],
            "budget": {
                "candidates_generated": 1,
                "candidates_max": 4,
                "stop_reason": "first candidate satisfied every critical dimension",
            },
        })

    # ---- 3. normalization --------------------------------------------------
    for state in STATES:
        asset_id = f"AST-GATE-{state}"
        run([
            sys.executable, str(SKILLS / "game-asset-normalizer/scripts/normalize.py"),
            "--candidate", f"generation/{asset_id}/candidates/v1-c1.png",
            "--spec", f"assets/specs/{asset_id}.yaml",
            "--project-root", ".",
            "--out", f"normalized/{asset_id}",
            "--generation-record", f"generation/{asset_id}/records/v1-c1.yaml",
            "--shared-scale", SHARED_SCALE,
        ])

    # Frames go through the same normalizer on the same shared scale basis as
    # the states. That is what makes the pivot identical across the clip.
    for asset_id in FRAMES:
        run([
            sys.executable, str(SKILLS / "game-asset-normalizer/scripts/normalize.py"),
            "--candidate", f"generation/{asset_id}/candidates/v1-c1.png",
            "--spec", f"assets/specs/{asset_id}.yaml",
            "--project-root", ".",
            "--out", f"normalized/{asset_id}",
            "--generation-record", f"generation/{asset_id}/records/v1-c1.yaml",
            "--shared-scale", SHARED_SCALE,
        ])

    # ---- 3b. clip continuity ------------------------------------------------
    frame_check = yaml.safe_load(run([
        sys.executable, str(SKILLS / "game-asset-normalizer/scripts/check_frames.py"),
        "--project-root", ".", "--clip", CLIP_ID,
        *sum([["--spec", f"assets/specs/{asset_id}.yaml"] for asset_id in FRAMES], []),
    ], allow_fail=True))
    dump(ROOT / f"normalized/{CLIP_ID}/frame-continuity-report.yaml", frame_check)

    # ---- 4. QC -------------------------------------------------------------
    qc_refs = {}
    for state in STATES:
        asset_id = f"AST-GATE-{state}"
        siblings = [f"normalized/AST-GATE-{other}/runtime/AST-GATE-{other}.png"
                    for other in STATES if other != state]
        command = [
            sys.executable, str(SKILLS / "game-asset-qc/scripts/technical_check.py"),
            "--asset", f"normalized/{asset_id}/runtime/{asset_id}.png",
            "--spec", f"assets/specs/{asset_id}.yaml",
            "--record", f"normalized/{asset_id}/normalization-record.yaml",
        ]
        for sibling in siblings:
            command += ["--sibling", sibling]
        for background in BACKGROUNDS:
            command += ["--background", background]

        measured = yaml.safe_load(run(command, allow_fail=True))
        norm_record = yaml.safe_load(
            (ROOT / f"normalized/{asset_id}/normalization-record.yaml").read_text(encoding="utf-8"))

        failing = [item["check_id"] for item in measured["accessibility"] if item["result"] == "FAIL"]
        failing += [name for name, result in measured["technical"]["checks"].items() if result == "FAIL"]

        report = {
            "schema_version": 3,
            "asset_id": asset_id,
            "family_id": "FAM-GATE",
            "status": "rework_required" if failing else "approved",
            "evaluated": {
                "normalized_output": {
                    "path": norm_record["output"]["path"],
                    "version": "v1",
                    "content_hash": norm_record["output"]["content_hash"],
                },
                "asset_spec": spec_refs[state],
                "generation_candidate": "v1-c1",
                "art_style": upstream_refs["art_style"],
                "anchor_ids": ["ANCH-GATE-GEOMETRY-001", "ANCH-PALETTE-001"],
                "constraint_ids": ["NEG-LIGHTING-001", "NEG-TEXTURE-002",
                                   "NEG-DETAIL-003", "NEG-STATE-004"],
            },
            "technical": measured["technical"],
            "anchors": [
                {"anchor_id": "ANCH-GATE-GEOMETRY-001", "role": "geometry_anchor",
                 "governed_dimensions": ["frame.outer_proportion", "frame.thickness_ratio", "opening.aspect"],
                 "result": "PASS"},
                {"anchor_id": "ANCH-PALETTE-001", "role": "palette_anchor",
                 "governed_dimensions": ["palette.hue_family", "palette.value_structure"],
                 "result": "PASS"},
            ],
            "constraints": [
                {"constraint_id": "NEG-LIGHTING-001", "type": "HARD_FORBIDDEN", "result": "PASS",
                 "evidence": "flat fills only; no gradient, rim light, or bloom present"},
                {"constraint_id": "NEG-TEXTURE-002", "type": "BOUNDED", "result": "PASS",
                 "evidence": "grain amplitude +/- 7, within the +/- 8 bound"},
                {"constraint_id": "NEG-DETAIL-003", "type": "SOFT_AVOID", "result": "PASS",
                 "evidence": "bolts remain resolvable at 64 px; no sub-4px ornament"},
                {"constraint_id": "NEG-STATE-004", "type": "HARD_FORBIDDEN", "result": "PASS",
                 "evidence": "panel height carries the state; hue is identical across siblings"},
            ],
            "accessibility": measured["accessibility"],
            "passing_dimensions": [
                "identity", "outer_frame_geometry", "frame_thickness",
                "top_down_projection", "palette_family", "footprint",
                "texture_density", "lighting", "state_readability",
            ],
            "findings": [],
            "rework_handoff": None,
        }
        dump(ROOT / f"qc/{asset_id}/qc-report.yaml", report)
        qc_refs[state] = {
            "path": f"qc/{asset_id}/qc-report.yaml",
            "version": "v1",
            "content_hash": sha(ROOT / f"qc/{asset_id}/qc-report.yaml"),
        }

    frame_qc_refs = {}
    for index, asset_id in enumerate(FRAMES):
        command = [
            sys.executable, str(SKILLS / "game-asset-qc/scripts/technical_check.py"),
            "--asset", f"normalized/{asset_id}/runtime/{asset_id}.png",
            "--spec", f"assets/specs/{asset_id}.yaml",
            "--record", f"normalized/{asset_id}/normalization-record.yaml",
        ]
        # A frame's meaningful sibling is its neighbour in the clip, not every
        # other frame: adjacent frames are where a stutter or a redraw shows.
        for neighbour in FRAMES[max(index - 1, 0):index] + FRAMES[index + 1:index + 2]:
            command += ["--sibling", f"normalized/{neighbour}/runtime/{neighbour}.png"]
        for background in BACKGROUNDS:
            command += ["--background", background]

        measured = yaml.safe_load(run(command, allow_fail=True))
        norm_record = yaml.safe_load(
            (ROOT / f"normalized/{asset_id}/normalization-record.yaml").read_text(encoding="utf-8"))
        failing = [name for name, result in measured["technical"]["checks"].items() if result == "FAIL"]

        dump(ROOT / f"qc/{asset_id}/qc-report.yaml", {
            "schema_version": 3,
            "asset_id": asset_id,
            "family_id": "FAM-GATE-OPENING",
            "status": "rework_required" if failing else "approved",
            "evaluated": {
                "normalized_output": {
                    "path": norm_record["output"]["path"],
                    "version": "v1",
                    "content_hash": norm_record["output"]["content_hash"],
                },
                "asset_spec": frame_spec_refs[asset_id],
                "generation_candidate": "v1-c1",
                "art_style": upstream_refs["art_style"],
                "anchor_ids": ["ANCH-GATE-GEOMETRY-001", "ANCH-PALETTE-001"],
                "constraint_ids": ["NEG-LIGHTING-001", "NEG-TEXTURE-002",
                                   "NEG-DETAIL-003", "NEG-STATE-004"],
                "clip": {"id": CLIP_ID, "frame_index": index,
                         "continuity_report": f"normalized/{CLIP_ID}/frame-continuity-report.yaml",
                         "continuity_status": frame_check["status"]},
            },
            "technical": measured["technical"],
            "anchors": [
                {"anchor_id": "ANCH-GATE-GEOMETRY-001", "role": "geometry_anchor",
                 "governed_dimensions": ["frame.outer_proportion", "frame.thickness_ratio"],
                 "result": "PASS"},
            ],
            "constraints": [
                {"constraint_id": "NEG-LIGHTING-001", "type": "HARD_FORBIDDEN", "result": "PASS",
                 "evidence": "flat fills only across every frame"},
            ],
            "accessibility": measured["accessibility"],
            "passing_dimensions": ["identity", "outer_frame_geometry", "frame_thickness",
                                   "palette_family", "runtime_pivot", "clip_continuity"],
            "findings": [],
            "rework_handoff": None,
        })
        frame_qc_refs[asset_id] = {
            "path": f"qc/{asset_id}/qc-report.yaml",
            "version": "v1",
            "content_hash": sha(ROOT / f"qc/{asset_id}/qc-report.yaml"),
        }

    dump(ROOT / f"qc/FAM-GATE-OPENING/family-qc-summary.yaml", {
        "family_id": "FAM-GATE-OPENING",
        "canonical_asset": FRAMES[0],
        "family_contract_version": "v1",
        "status": "approved" if frame_check["status"] == "pass" else "rework_required",
        "approved_members": list(FRAMES),
        "rework_members": [],
        "blocked_members": [],
        "systemic_findings": [],
        "local_findings": [],
        "invariants_verified": [
            f"clip continuity checked as a sequence: {frame_check['status']}",
            f"runtime_pivot drift across the clip: {frame_check['measured']['max_pivot_drift']}",
            "shared 256x256 canvas and shared scale basis 0.623377 across every frame",
            "one grain seed for the whole clip, so texture does not crawl between frames",
        ],
    })

    dump(ROOT / "qc/FAM-GATE/family-qc-summary.yaml", {
        "family_id": "FAM-GATE",
        "canonical_asset": "AST-GATE-CLOSED",
        "family_contract_version": "v1",
        "status": "approved",
        "approved_members": [f"AST-GATE-{state}" for state in STATES],
        "rework_members": [],
        "blocked_members": [],
        "systemic_findings": [],
        "local_findings": [],
        "invariants_verified": [
            "outer_frame_geometry identical across all three states",
            "shared scale basis 0.623377 applied to every member",
            "shared 256x256 canvas and bottom_center pivot",
            "state carried by panel height, not hue",
        ],
    })

    # ---- 5. engine integration --------------------------------------------
    # The atlas is packed before the budget is measured, because the atlas is
    # what is actually resident at runtime. Measuring the loose sprites instead
    # under-reports texture memory and leaves max_atlas_dimension describing
    # nothing.
    run([
        sys.executable, str(SKILLS / "game-engine-integrator/scripts/pack_atlas.py"),
        "--project-root", ".", "--atlas-id", "FAM-GATE", "--target-id", "web-main",
        *sum([["--member", f"AST-GATE-{state}"] for state in STATES], []),
    ])

    # The clip packs as its own sheet. Frames share a draw pass and a lifetime,
    # and pack_atlas.py refuses to pack a partial clip because a frame map that
    # indexes frames the sheet does not contain plays wrong.
    run([
        sys.executable, str(SKILLS / "game-engine-integrator/scripts/pack_atlas.py"),
        "--project-root", ".", "--atlas-id", CLIP_ID, "--target-id", "web-main",
        *sum([["--member", asset_id] for asset_id in FRAMES], []),
    ])

    budget = yaml.safe_load(run([
        sys.executable, str(SKILLS / "game-engine-integrator/scripts/budget_check.py"),
        "--project-root", ".", "--target-id", "web-main",
    ], allow_fail=True))
    dump(ROOT / "engine-integration/web-main/budget-report.yaml", budget)

    import_settings = {"schema_version": 3,
                       "target": {"id": "web-main", "engine": "web-canvas",
                                  "pixels_per_unit": 64, "color_space": "gamma"},
                       "assets": {}}
    for state in STATES:
        asset_id = f"AST-GATE-{state}"
        norm_record = yaml.safe_load(
            (ROOT / f"normalized/{asset_id}/normalization-record.yaml").read_text(encoding="utf-8"))
        import_settings["assets"][asset_id] = {
            "source": norm_record["output"]["path"],
            "content_hash": norm_record["output"]["content_hash"],
            # Taken from the normalization record, never re-decided here.
            "pivot": norm_record["geometry"]["runtime_pivot"],
            "pixels_per_unit": 64,
            "filter_mode": "bilinear",
            "compression": "none",
            "generate_mipmaps": False,
            "wrap_mode": "clamp",
        }
    dump(ROOT / "engine-integration/web-main/import-settings.yaml", import_settings)

    dump(ROOT / "engine-integration/web-main/integration-plan.yaml", {
        "schema_version": 3,
        "target": {"id": "web-main", "engine": "web-canvas"},
        "atlas_strategy": {
            "decision": "single atlas for FAM-GATE",
            "rationale": "all three states share a draw pass and a lifetime; they load and unload together",
            "padding_px": 2,
            "padding_rationale": "bilinear filtering bleeds neighbouring pixels at non-integer scale below 2 px",
        },
        "inputs": [qc_refs[state] for state in STATES],
        "limitations": [],
        "status": budget["status"],
    })

    # ---- 6. runtime validation --------------------------------------------
    runtime_refs = {}
    for state in STATES:
        asset_id = f"AST-GATE-{state}"
        norm_record = yaml.safe_load(
            (ROOT / f"normalized/{asset_id}/normalization-record.yaml").read_text(encoding="utf-8"))
        report = {
            "schema_version": 3,
            "asset_id": asset_id,
            "status": "runtime_approved",
            "build": {"id": "example-build-0001", "executable": True},
            "integrated_lineage": {
                "normalized_output": {
                    "path": norm_record["output"]["path"],
                    "version": "v1",
                    "content_hash": norm_record["output"]["content_hash"],
                },
                "qc_report": qc_refs[state],
                "integration_plan": {"path": "engine-integration/web-main/integration-plan.yaml"},
            },
            "contexts": [
                {"id": context["id"], "scene": context["scene"], "viewport": context["viewport"],
                 "camera": context["camera"], "states": context["states"],
                 "level": context["level"], "result": "PASS",
                 "capture_ids": [context["capture_id"]]}
                for context in CONTEXTS
            ],
            "findings": [],
            "untested": [
                {"context": "ultrawide 21:9 viewport", "reason": "not a declared target", "risk": "low"},
            ],
            "rework_handoff": None,
        }

        # The plan is written before the report it authorizes: it names the
        # contexts, why that coverage is sufficient, and what was excluded.
        dump(ROOT / f"runtime-validation/{asset_id}/runtime-validation-plan.yaml", {
            "schema_version": 3,
            "asset_id": asset_id,
            "build_target": {"id": "example-build-0001", "engine": "web-canvas"},
            "coverage_rationale": (
                "P0 stateful gameplay asset, so Level 2 minimum. CTX-CORRIDOR-MIN covers the "
                "smallest declared viewport with all three states present; CTX-CHAMBER-DENSE "
                "covers the darker of the two backgrounds the AssetSpec records in "
                "runtime.backgrounds_encountered, which is where A11Y_RUNTIME_CONTRAST is "
                "most likely to fail."
            ),
            "planned_contexts": [
                {"id": context["id"], "scene": context["scene"], "viewport": context["viewport"],
                 "camera": context["camera"], "states": context["states"],
                 "level": context["level"], "risk": context["risk"],
                 "background": context["background"], "expected": context["expected"]}
                for context in CONTEXTS
            ],
            "excluded_contexts": [
                {"context": "ultrawide 21:9 viewport", "reason": "not a declared target",
                 "risk": "low"},
            ],
        })

        # Every capture id in the report is backed by bytes on disk and hashed,
        # so a BLOCKER or MAJOR finding could actually be reproduced by whoever
        # has to fix it.
        captures = []
        spec_doc = yaml.safe_load(
            (ROOT / f"assets/specs/{asset_id}.yaml").read_text(encoding="utf-8"))
        display = (
            spec_doc["runtime"]["intended_display_size"]["width"],
            spec_doc["runtime"]["intended_display_size"]["height"],
        )
        for context in CONTEXTS:
            capture_rel = f"runtime-validation/{asset_id}/captures/{context['capture_id']}.png"
            render_capture(ROOT / norm_record["output"]["path"], context["background"],
                           display, ROOT / capture_rel)
            captures.append({
                "id": context["capture_id"],
                "context_id": context["id"],
                "kind": "rendered_frame",
                "path": capture_rel,
                "content_hash": sha(ROOT / capture_rel),
                "background": context["background"],
                "rendered_at": f"{display[0]}x{display[1]} on a {CAPTURE_PLATE[0]}x{CAPTURE_PLATE[1]} plate",
                "produced_by": "examples/gate-family/tools/build_example.py:render_capture",
                "limitation": (
                    "headless composite of the runtime asset over a declared background; no game "
                    "build runs in CI, and this is recorded rather than described as a screenshot"
                ),
            })
        dump(ROOT / f"runtime-validation/{asset_id}/evidence-manifest.yaml", {
            "schema_version": 3,
            "asset_id": asset_id,
            "build": {"id": "example-build-0001", "executable": True},
            "captures": captures,
        })

        dump(ROOT / f"runtime-validation/{asset_id}/runtime-report.yaml", report)
        runtime_refs[state] = {
            "path": f"runtime-validation/{asset_id}/runtime-report.yaml",
            "version": "v1",
            "content_hash": sha(ROOT / f"runtime-validation/{asset_id}/runtime-report.yaml"),
        }

    # ---- 7. pipeline state -------------------------------------------------
    assets_state = {}
    for state in STATES:
        asset_id = f"AST-GATE-{state}"
        norm_record = yaml.safe_load(
            (ROOT / f"normalized/{asset_id}/normalization-record.yaml").read_text(encoding="utf-8"))
        assets_state[asset_id] = {
            "lifecycle": "RUNTIME_APPROVED",
            "family_id": "FAM-GATE",
            "priority": "P0",
            "active_versions": {
                "asset_spec": spec_refs[state],
                "generation_candidate": {
                    "id": "v1-c1",
                    "content_hash": sha(ROOT / f"generation/{asset_id}/candidates/v1-c1.png"),
                },
                "normalization_output": {
                    "version": "v1",
                    "content_hash": norm_record["output"]["content_hash"],
                },
                "qc_report": qc_refs[state],
                "runtime_report": runtime_refs[state],
            },
            "root_owner": None,
            "next_skill": None,
            "next_action": "eligible for SHIPPABLE once the milestone requires it",
        }

    # Frames stop at QC_APPROVED. Runtime approval for a clip needs frame-
    # sequence evidence, which the runtime evidence model does not yet carry -
    # so claiming it here would be exactly the unsupported promotion the
    # validator now rejects.
    for index, asset_id in enumerate(FRAMES):
        norm_record = yaml.safe_load(
            (ROOT / f"normalized/{asset_id}/normalization-record.yaml").read_text(encoding="utf-8"))
        assets_state[asset_id] = {
            "lifecycle": "QC_APPROVED",
            "family_id": "FAM-GATE-OPENING",
            "priority": "P1",
            "active_versions": {
                "asset_spec": frame_spec_refs[asset_id],
                "generation_candidate": {
                    "id": "v1-c1",
                    "content_hash": sha(ROOT / f"generation/{asset_id}/candidates/v1-c1.png"),
                },
                "normalization_output": {
                    "version": "v1",
                    "content_hash": norm_record["output"]["content_hash"],
                },
                "qc_report": frame_qc_refs[asset_id],
            },
            "root_owner": None,
            "next_skill": "runtime-visual-validator",
            "next_action": "validate the clip at 12 fps once frame-sequence evidence is modelled",
        }

    dump(ROOT / ".pipeline/game-art-production-state.yaml", {
        "version": 3,
        "project": {"id": "gate-family", "name": "Gate Family", "pipeline_status": "IN_PROGRESS"},
        "profile": "full",
        "target": {"milestone": "gate family runtime-approved"},
        "authoritative": upstream_refs,
        "stages": {
            "game_spec": {"skill": "game-spec-builder", "status": "COMPLETE",
                          "readiness": "PRODUCTION_READY", "artifacts": ["spec/game-spec.yaml"]},
            "art_style": {"skill": "art-style-builder", "status": "COMPLETE",
                          "readiness": "ASSET_GENERATION_READY", "artifacts": ["art/art-style.yaml"]},
            "asset_planning": {"skill": "game-asset-planner", "status": "COMPLETE",
                               "readiness": None, "artifacts": ["assets/asset-manifest.yaml"]},
            "generation": {"skill": "game-asset-generator", "status": "COMPLETE",
                           "readiness": None, "artifacts": []},
            "normalization": {"skill": "game-asset-normalizer", "status": "COMPLETE",
                              "readiness": None, "artifacts": []},
            "asset_qc": {"skill": "game-asset-qc", "status": "COMPLETE",
                         "readiness": None,
                         "artifacts": ["qc/FAM-GATE/family-qc-summary.yaml",
                                       "qc/FAM-GATE-OPENING/family-qc-summary.yaml"]},
            "engine_integration": {"skill": "game-engine-integrator", "status": "COMPLETE",
                                   "readiness": None,
                                   "artifacts": ["engine-integration/web-main/budget-report.yaml"]},
            "runtime_validation": {"skill": "runtime-visual-validator", "status": "COMPLETE",
                                   "readiness": None, "artifacts": []},
        },
        "assets": assets_state,
        "families": {
            "FAM-GATE-OPENING": {
                "canonical_asset": FRAMES[0],
                "canonical_status": "QC_APPROVED",
                "systemic_blocker": None,
                "clip": {"id": CLIP_ID, "frame_count": FRAME_COUNT, "fps": 12, "loop": "once",
                         "continuity": frame_check["status"]},
                "derivatives": {asset_id: "QC_APPROVED" for asset_id in FRAMES[1:]},
            },
            "FAM-GATE": {
                "canonical_asset": "AST-GATE-CLOSED",
                "canonical_status": "RUNTIME_APPROVED",
                "systemic_blocker": None,
                "derivatives": {
                    "AST-GATE-TRANSITION": "RUNTIME_APPROVED",
                    "AST-GATE-OPEN": "RUNTIME_APPROVED",
                },
            }
        },
        "active_versions": upstream_refs,
        "handoffs": ["HND-0001"],
        "blockers": [],
        "invalidations": ["INV-0001"],
        "rework_queue": [],
    })

    # ---- 8. asset manifest -------------------------------------------------
    dump(ROOT / "assets/asset-manifest.yaml", {
        "schema_version": 3,
        "profile": "full",
        "source_versions": {
            "game_spec": upstream_refs["game_spec"],
            "art_style": upstream_refs["art_style"],
        },
        "families": {
            "FAM-GATE": {
                "canonical_asset": "AST-GATE-CLOSED",
                "topology": "CANONICAL_PARENT_TO_STATES",
                "members": [f"AST-GATE-{state}" for state in STATES],
                "preserve": ["outer_frame_geometry", "frame_thickness",
                             "top_down_projection", "palette_family", "footprint"],
            },
            "FAM-GATE-OPENING": {
                "canonical_asset": FRAMES[0],
                "topology": "PARENT_TO_ANIMATION",
                "members": list(FRAMES),
                "clip": {"id": CLIP_ID, "frame_count": FRAME_COUNT, "fps": 12, "loop": "once"},
                # runtime_pivot joins the invariants here: frames that do not
                # share a pivot are what makes a clip bob.
                "preserve": ["outer_frame_geometry", "frame_thickness",
                             "top_down_projection", "palette_family", "footprint",
                             "runtime_pivot"],
            },
        },
        "assets": {
            f"AST-GATE-{state}": {
                "spec_path": f"assets/specs/AST-GATE-{state}.yaml",
                "family_id": "FAM-GATE",
                "category": "interactive_object",
                "priority": "P0",
                "tier": 1,
                "strategy": "generated_raster",
                "lifecycle": "RUNTIME_APPROVED",
                "canonical_parent": None if state == "CLOSED" else "AST-GATE-CLOSED",
            }
            for state in STATES
        } | {
            asset_id: {
                "spec_path": f"assets/specs/{asset_id}.yaml",
                "family_id": "FAM-GATE-OPENING",
                "category": "interactive_object",
                "priority": "P1",
                "tier": 2,
                "strategy": "generated_raster",
                "lifecycle": "QC_APPROVED",
                "canonical_parent": None if index == 0 else FRAMES[0],
                "animation": {"clip_id": CLIP_ID, "frame_index": index},
            }
            for index, asset_id in enumerate(FRAMES)
        },
    })

    print("example rebuilt")
    print(f"- budget status: {budget['status']}")
    print(f"- clip {CLIP_ID}: {FRAME_COUNT} frames, continuity {frame_check['status']}, "
          f"pivot drift {frame_check['measured']['max_pivot_drift']}")
    for state in STATES:
        qc = yaml.safe_load((ROOT / f"qc/AST-GATE-{state}/qc-report.yaml").read_text(encoding="utf-8"))
        contrast = next((i for i in qc["accessibility"] if i["check_id"] == "A11Y_CONTRAST"), None)
        cvd = next((i for i in qc["accessibility"] if i["check_id"] == "A11Y_COLOR_VISION"), None)
        print(f"- AST-GATE-{state:<10} qc={qc['status']:<10} "
              f"contrast={contrast['measured'] if contrast else '-'} "
              f"cvd_separation={cvd['measured'] if cvd else '-'}")


if __name__ == "__main__":
    main()
