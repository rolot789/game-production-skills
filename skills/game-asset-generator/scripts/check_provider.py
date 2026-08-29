#!/usr/bin/env python3
"""Check the planned asset set against what the declared provider can do.

Run this after planning and before generating anything. It answers one question
with no image budget spent: **can the provider you have actually execute the
plan you made?**

The question is not rhetorical. `derivation_mode: parent_derived` means "make
this, posed differently, preserving identity" - an image-conditioned edit. A
text-to-image provider cannot do it, and what you get instead is a new drawing
per family member, which is precisely the IDENTITY_DRIFT the anti-drift
machinery exists to prevent. Discovering that after forty images is the most
expensive way to learn it.

    python3 check_provider.py --project-root .
    python3 check_provider.py --project-root . --provider text_to_image_only

The provider comes from project.yaml `generation.provider`, naming a profile in
contracts/providers.yaml or a `generation.capabilities` block the project
declares itself.

Exit 0 when the plan is executable, 1 on any BLOCKER. A shortfall is never a
generator defect - the generator compiled the contract correctly and the
provider cannot execute it.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

try:
    import yaml
except ImportError:  # pragma: no cover - environment guard
    print("check_provider.py requires pyyaml: python3 -m pip install pyyaml", file=sys.stderr)
    raise SystemExit(2)


def contracts_path(name: str) -> Path:
    """Resolve a contract from an installed skill or from the repository."""
    here = Path(__file__).resolve().parent
    for candidate in (here.parent / "references" / name,
                      here.parents[2] / "contracts" / name):
        if candidate.exists():
            return candidate
    raise SystemExit(f"cannot locate {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--provider", default=None,
                        help="override project.yaml generation.provider")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    project_file = root / "project.yaml"
    if not project_file.exists():
        raise SystemExit(f"no project.yaml in {root}")
    project = yaml.safe_load(project_file.read_text(encoding="utf-8"))
    providers = yaml.safe_load(contracts_path("providers.yaml").read_text(encoding="utf-8"))

    generation = project.get("generation") or {}
    name = args.provider or generation.get("provider")
    if not name:
        print("PROVIDER CHECK: BLOCKED")
        print("- project.yaml declares no generation.provider")
        print("- an undeclared provider is not a capable provider; name a profile from")
        print("  contracts/providers.yaml, or declare generation.capabilities yourself")
        raise SystemExit(1)

    # A project may name a shipped profile or declare its own capabilities. The
    # second is how you record a provider this repository has never measured,
    # which is most of them.
    #
    # An explicit --provider always resolves against the shipped profiles: it is
    # asking "what if we used this instead", and the project's own capability
    # block describes the project's provider, not that one. Reusing it would
    # answer the question with the wrong capabilities and report `executable`
    # for a provider that cannot execute anything.
    profiles = providers.get("profiles") or {}
    if args.provider:
        declared = profiles.get(args.provider)
        if declared is None:
            raise SystemExit(f"unknown provider profile {args.provider!r}; "
                             f"contracts/providers.yaml has {sorted(profiles)}")
    else:
        declared = generation.get("capabilities")
        if declared is None:
            declared = profiles.get(name)
            if declared is None:
                raise SystemExit(f"project.yaml names provider {name!r}, which is not a profile in "
                                 f"contracts/providers.yaml {sorted(profiles)} and declares no "
                                 f"generation.capabilities block of its own")
    known = set(providers["capabilities"])
    capabilities = {key: bool(value) for key, value in declared.items() if key in known}

    specs_dir = root / (project.get("paths") or {}).get("asset_specs", "assets/specs/")
    specs = sorted(specs_dir.glob("*.yaml")) if specs_dir.exists() else []
    if not specs:
        raise SystemExit(f"no AssetSpecs under {specs_dir}")

    requirements = providers["derivation_requirements"]
    strategies = yaml.safe_load(contracts_path("toolkit-contract.yaml").read_text(encoding="utf-8"))
    planning_only = set(((strategies.get("representation_strategies") or {})
                         .get("planning_only") or {}).get("strategies") or [])

    findings: list[dict] = []
    modes: dict[str, list[str]] = {}
    wants_transparency: list[str] = []

    for spec_path in specs:
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        asset_id = spec.get("asset_id", spec_path.stem)
        production = spec.get("production") or {}
        strategy = production.get("strategy")
        mode = production.get("derivation_mode")

        if strategy in planning_only:
            findings.append({
                "asset_id": asset_id,
                "severity": "NOTE",
                "detail": f"strategy {strategy!r} has no production path in this toolkit; "
                          f"no provider capability applies",
            })
            continue
        if strategy not in (None, "generated_raster"):
            continue  # authors no file; nothing for a provider to do

        modes.setdefault(mode, []).append(asset_id)
        if ((spec.get("runtime") or {}).get("background_policy") or "transparent") == "transparent":
            wants_transparency.append(asset_id)

        for capability in (requirements.get(mode) or {}).get("requires", []):
            if not capabilities.get(capability):
                findings.append({
                    "asset_id": asset_id,
                    "severity": "BLOCKER",
                    "detail": f"derivation_mode {mode!r} requires {capability!r}, "
                              f"which {name!r} does not have",
                })

    handling = providers.get("shortfall_handling") or {}
    if wants_transparency and not capabilities.get("native_transparency"):
        findings.append({
            "asset_id": f"{len(wants_transparency)} asset(s)",
            "severity": "MAJOR",
            "detail": f"{name!r} has no native_transparency and these specs want a transparent "
                      f"background; check_alpha.py will fail every candidate",
            "action": (handling.get("missing_native_transparency") or {}).get("action", ""),
        })
    if not capabilities.get("mask_inpaint"):
        findings.append({
            "asset_id": "*",
            "severity": "NOTE",
            "detail": f"{name!r} has no mask_inpaint; a G1_LOCAL_DIMENSION_DELTA cannot be "
                      f"scoped to a region and is really a full re-roll",
        })
    if not capabilities.get("seed_exposed"):
        findings.append({
            "asset_id": "*",
            "severity": "NOTE",
            "detail": f"{name!r} does not expose a seed; provenance records `not_exposed` and "
                      f"candidates are not exactly reproducible",
        })

    blockers = [item for item in findings if item["severity"] == "BLOCKER"]
    report = {
        "provider": {"id": name, "capabilities": capabilities},
        "status": "blocked" if blockers else "executable",
        "planned": {
            "assets_needing_generation": sum(len(ids) for ids in modes.values()),
            "derivation_modes": {mode: len(ids) for mode, ids in sorted(modes.items(), key=lambda i: str(i[0]))},
        },
        "findings": findings,
    }
    print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True).rstrip())

    if blockers:
        affected = sorted({item["asset_id"] for item in blockers})
        print(
            f"\n# PROVIDER SHORTFALL - {len(affected)} asset(s) cannot be produced as planned.\n"
            f"# This is not a generator defect: the contract is correct and the provider cannot\n"
            f"# execute it. Either declare a provider with the missing capability, or revise\n"
            f"# derivation_mode - and accept the family coherence that decision costs.",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
