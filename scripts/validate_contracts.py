#!/usr/bin/env python3
from pathlib import Path
import json
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(rel):
    path = ROOT / rel
    if not path.exists():
        raise FileNotFoundError(rel)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read(rel):
    path = ROOT / rel
    if not path.exists():
        raise FileNotFoundError(rel)
    return path.read_text(encoding="utf-8")


def main():
    errors = []

    try:
        contract = load_yaml("contracts/toolkit-contract.yaml")
        rework = load_yaml("contracts/rework-handoff-contract.yaml")
        project = load_yaml("templates/project/project.yaml")
        state = load_yaml("templates/project/.pipeline/game-art-production-state.yaml")
        example_project = load_yaml("examples/minimal-project/project.yaml")
        example_state = load_yaml("examples/minimal-project/.pipeline/game-art-production-state.yaml")
    except Exception as exc:
        print(f"CONTRACT VALIDATOR: FAIL\n- unable to load required YAML: {exc}")
        raise SystemExit(1)

    version = contract.get("version")
    version_checks = {
        "contract": version,
        "orchestrator.state_version": contract.get("orchestrator", {}).get("state_version"),
        "template project": project.get("version"),
        "template pipeline state": state.get("version"),
        "example project": example_project.get("version"),
        "example pipeline state": example_state.get("version"),
    }
    for label, value in version_checks.items():
        if value != version:
            errors.append(f"version mismatch: {label}={value!r}, contract={version!r}")

    stage_order = contract.get("stage_order", [])
    contract_stages = contract.get("stages", {})
    if list(contract_stages.keys()) != stage_order:
        errors.append("contracts/toolkit-contract.yaml stages must follow stage_order")

    for label, doc in [("template", state), ("example", example_state)]:
        stages = list((doc.get("stages") or {}).keys())
        if stages != stage_order:
            errors.append(f"{label} pipeline stage order differs from toolkit contract: {stages}")

    required_state_keys = {
        "assets", "families", "active_versions", "handoffs", "blockers", "invalidations", "rework_queue"
    }
    for label, doc in [("template", state), ("example", example_state)]:
        missing = required_state_keys - set(doc.keys())
        if missing:
            errors.append(f"{label} pipeline state missing v2 keys: {sorted(missing)}")

    required_path_keys = set(contract.get("path_resolution", {}).get("required_project_path_keys", []))
    for label, doc in [("template", project), ("example", example_project)]:
        paths = set((doc.get("paths") or {}).keys())
        missing = required_path_keys - paths
        if missing:
            errors.append(f"{label} project.yaml missing canonical path keys: {sorted(missing)}")
        if doc.get("path_resolution", {}).get("mode") != "canonical_registry":
            errors.append(f"{label} project.yaml path_resolution.mode must be canonical_registry")

    contract_handoff = set(contract.get("orchestrator", {}).get("handoff_fields", []))
    rework_required = set(rework.get("required_fields", []))
    if contract_handoff != rework_required:
        errors.append(
            "toolkit orchestrator handoff_fields and rework-handoff required_fields differ: "
            f"only_contract={sorted(contract_handoff - rework_required)}, "
            f"only_rework={sorted(rework_required - contract_handoff)}"
        )

    scope_schema = rework.get("scope_schema", {})
    for field in ("change_scope", "preserve_scope"):
        if field not in scope_schema:
            errors.append(f"rework handoff missing scope schema: {field}")

    for stage_name in ("asset_qc", "runtime_validation"):
        stage = contract_stages.get(stage_name, {})
        allowed = set(stage.get("allowed_exit_status", []))
        promotion = set(stage.get("promotion_status", []))
        if not promotion.issubset(allowed):
            errors.append(f"{stage_name} promotion_status must be subset of allowed_exit_status")

    runtime_promotion = set(contract_stages.get("runtime_validation", {}).get("promotion_status", []))
    if "partial_validation_only" in runtime_promotion:
        errors.append("partial_validation_only must never be a runtime promotion status")

    semantic_expectations = {
        "skills/game-asset-planner/SKILL.md": [
            "project.yaml", "style-constraint-ledger.yaml", "source_versions", "canonical parent"
        ],
        "skills/game-asset-generator/SKILL.md": [
            "project.yaml", "change_scope", "preserve_scope", "generation-contract.yaml"
        ],
        "skills/game-asset-normalizer/SKILL.md": [
            "project.yaml", "change_scope", "preserve_scope", "input_candidate", "hash"
        ],
        "skills/game-asset-qc/SKILL.md": [
            "project.yaml", "change_scope", "preserve_scope", "contracts/rework-handoff-contract.yaml"
        ],
        "skills/runtime-visual-validator/SKILL.md": [
            "project.yaml", "change_scope", "preserve_scope", "partial_validation_only"
        ],
        "skills/game-art-production-orchestrator/SKILL.md": [
            "project.yaml", "change_scope", "preserve_scope", "new generation candidate",
            "old normalization output/record becomes non-authoritative"
        ],
    }
    for rel, needles in semantic_expectations.items():
        try:
            text = read(rel)
        except Exception as exc:
            errors.append(f"missing semantic contract document {rel}: {exc}")
            continue
        for needle in needles:
            if needle not in text:
                errors.append(f"{rel} missing required v2 semantic marker: {needle!r}")

    policy_files = [
        "skills/art-style-builder/references/reference-search-policy.md",
        "skills/art-style-builder/references/style-loop-policy.md",
        "skills/art-style-builder/references/negative-constraint-policy.md",
        "skills/game-asset-generator/references/generation-compilation-policy.md",
        "skills/game-asset-generator/references/anti-drift-regeneration-policy.md",
        "skills/game-asset-generator/references/family-coherence-policy.md",
        "skills/game-asset-qc/references/contract-verification-policy.md",
        "skills/game-asset-qc/references/failure-routing-policy.md",
        "skills/game-asset-qc/references/family-batch-qc-policy.md",
        "skills/runtime-visual-validator/references/runtime-evidence-policy.md",
        "skills/runtime-visual-validator/references/scene-context-validation-policy.md",
        "skills/runtime-visual-validator/references/runtime-regression-routing-policy.md",
        "skills/game-art-production-orchestrator/references/orchestration-state-policy.md",
        "skills/game-art-production-orchestrator/references/invalidation-routing-policy.md",
        "skills/game-art-production-orchestrator/references/handoff-promotion-policy.md",
    ]
    for rel in policy_files:
        if not (ROOT / rel).exists():
            errors.append(f"missing referenced policy file: {rel}")

    package_path = ROOT / "package.json"
    if package_path.exists():
        package = json.loads(package_path.read_text(encoding="utf-8"))
        canonical = "rolot789/game-production-skills"
        urls = [
            (package.get("repository") or {}).get("url", ""),
            (package.get("bugs") or {}).get("url", ""),
            package.get("homepage", ""),
        ]
        if any("tokencat" in value for value in urls):
            errors.append("package.json still contains stale tokencat repository URLs")
        if not all(canonical in value for value in urls if value):
            errors.append("package.json repository/bugs/homepage must point to rolot789/game-production-skills")

    if errors:
        print("CONTRACT VALIDATOR: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("CONTRACT VALIDATOR: PASS")
    print(f"- contract version: {version}")
    print(f"- stages: {len(stage_order)}")
    print(f"- canonical path keys: {len(required_path_keys)}")
    print(f"- handoff fields: {len(contract_handoff)}")
    print("- template/example schemas: aligned")
    print("- v2 semantic markers: aligned")


if __name__ == "__main__":
    main()
