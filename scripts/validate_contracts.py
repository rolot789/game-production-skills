#!/usr/bin/env python3
"""Verify that the toolkit is internally consistent.

The previous version of this script checked that specific English sentences
appeared in specific SKILL.md files. That coupled prose to CI (rewording broke
the build) while proving almost nothing (the sentence being present said nothing
about the meaning being right), and it silently excluded the two skills that
actually had the defect it was nominally guarding against.

This version compares sets and resolves references instead. Every check below
answers "do two places that must agree actually agree?" rather than "does this
string still exist?".

    python3 scripts/validate_contracts.py
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.minischema import SchemaStore  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Owners in routing.yaml that are roles rather than skills.
NON_SKILL_OWNERS = {"runtime_integration"}

TOKEN_PATTERNS = {
    "generation_rework_levels": re.compile(r"\bG[0-4]_[A-Z][A-Z_]*"),
    "art_style_loop_levels": re.compile(r"\bL[0-4]_[A-Z][A-Z_]*"),
    "invalidation_scope_classes": re.compile(
        r"\b(?:LOCAL_ASSET|LOCAL_DERIVATIVE|FAMILY_SYSTEMIC|CATEGORY_SYSTEMIC"
        r"|GLOBAL_SYSTEMIC|SCENE_LOCAL|RUNTIME_SYSTEMIC)\b"),
}


def load(rel: str):
    path = ROOT / rel
    if not path.exists():
        raise FileNotFoundError(rel)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def skill_documents():
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        for document in [skill_dir / "SKILL.md", *sorted(skill_dir.glob("references/*.md"))]:
            if document.exists():
                yield skill_dir.name, document


def main() -> None:
    errors: list[str] = []

    try:
        contract = load("contracts/toolkit-contract.yaml")
        rework = load("contracts/rework-handoff-contract.yaml")
        routing = load("contracts/routing.yaml")
        mirrors = load("contracts/mirror-manifest.yaml")
        project = load("templates/project/project.yaml")
        state = load("templates/project/.pipeline/game-art-production-state.yaml")
        example_project = load("examples/gate-family/project.yaml")
        example_state = load("examples/gate-family/.pipeline/game-art-production-state.yaml")
        profiles = {name: load(f"contracts/profiles/{name}.yaml") for name in ("lite", "full")}
    except Exception as exc:
        print(f"CONTRACT VALIDATOR: FAIL\n- unable to load required YAML: {exc}")
        raise SystemExit(1)

    version = contract.get("version")

    # ---- 1. version alignment ---------------------------------------------
    for label, value in {
        "orchestrator.state_version": contract.get("orchestrator", {}).get("state_version"),
        "rework contract": rework.get("version"),
        "routing contract": routing.get("version"),
        "mirror manifest": mirrors.get("version"),
        "template project": project.get("version"),
        "template pipeline state": state.get("version"),
        "example project": example_project.get("version"),
        "example pipeline state": example_state.get("version"),
        "profile lite": profiles["lite"].get("version"),
        "profile full": profiles["full"].get("version"),
    }.items():
        if value != version:
            errors.append(f"version mismatch: {label}={value!r}, contract={version!r}")

    # ---- 2. stage order ----------------------------------------------------
    stage_order = contract.get("stage_order", [])
    stages = contract.get("stages", {})
    if list(stages.keys()) != stage_order:
        errors.append("toolkit-contract.yaml stages must be declared in stage_order")

    for label, doc in [("template", state), ("example", example_state)]:
        declared = list((doc.get("stages") or {}).keys())
        if declared != stage_order:
            errors.append(f"{label} pipeline state stage order differs from the contract: {declared}")

    for label, doc in [("template", state), ("example", example_state)]:
        missing = {"assets", "families", "active_versions", "handoffs",
                   "blockers", "invalidations", "rework_queue"} - set(doc.keys())
        if missing:
            errors.append(f"{label} pipeline state is missing keys: {sorted(missing)}")

    # ---- 3. path registry --------------------------------------------------
    required_paths = set(contract.get("path_resolution", {}).get("required_project_path_keys", []))
    for label, doc in [("template", project), ("example", example_project)]:
        declared = set((doc.get("paths") or {}).keys())
        missing = required_paths - declared
        if missing:
            errors.append(f"{label} project.yaml is missing canonical path keys: {sorted(missing)}")
        if doc.get("path_resolution", {}).get("mode") != "canonical_registry":
            errors.append(f"{label} project.yaml path_resolution.mode must be canonical_registry")

    # ---- 4. handoff field agreement ---------------------------------------
    contract_fields = set(contract.get("orchestrator", {}).get("handoff_fields", []))
    rework_fields = set(rework.get("required_fields", []))
    if contract_fields != rework_fields:
        errors.append(
            "orchestrator.handoff_fields and rework required_fields differ: "
            f"only_contract={sorted(contract_fields - rework_fields)}, "
            f"only_rework={sorted(rework_fields - contract_fields)}"
        )

    store = SchemaStore(ROOT / "contracts" / "schemas")
    handoff_schema = store.get("rework-handoff.schema.json")
    schema_required = set(handoff_schema.get("required", []))
    if schema_required != rework_fields:
        errors.append(
            "rework-handoff.schema.json required fields differ from the rework contract: "
            f"only_schema={sorted(schema_required - rework_fields)}, "
            f"only_contract={sorted(rework_fields - schema_required)}"
        )
    if handoff_schema.get("additionalProperties") is not False:
        errors.append("rework-handoff.schema.json must set additionalProperties: false "
                      "so specialist-local aliases are rejected")
    for alias in rework.get("forbidden_external_aliases", []):
        if alias in handoff_schema.get("properties", {}):
            errors.append(f"rework-handoff.schema.json declares the forbidden alias {alias!r}")

    # ---- 5. status enums ---------------------------------------------------
    all_statuses: set[str] = set()
    for name, stage in stages.items():
        allowed = set(stage.get("allowed_exit_status", []))
        promotion = set(stage.get("promotion_status", []))
        all_statuses |= allowed
        if not promotion.issubset(allowed):
            errors.append(f"{name}: promotion_status must be a subset of allowed_exit_status")
    if "partial_validation_only" in set(stages.get("runtime_validation", {}).get("promotion_status", [])):
        errors.append("partial_validation_only must never be a runtime promotion status")

    # ---- 6. deterministic tools exist --------------------------------------
    for name, stage in stages.items():
        tool = stage.get("deterministic_tool")
        if tool and not (ROOT / tool).exists():
            errors.append(f"{name}.deterministic_tool does not exist: {tool}")

    # ---- 7. lifecycle transitions are a well-formed graph ------------------
    lifecycle = set(contract.get("asset_lifecycle", []))
    transitions = contract.get("lifecycle_transitions", {})
    if not transitions:
        errors.append("toolkit-contract.yaml declares no lifecycle_transitions; "
                      "an orchestrator cannot reject an illegal transition without them")
    missing_states = lifecycle - set(transitions.keys())
    if missing_states:
        errors.append(f"lifecycle states with no declared transitions: {sorted(missing_states)}")
    unknown_states = set(transitions.keys()) - lifecycle
    if unknown_states:
        errors.append(f"lifecycle_transitions declares unknown states: {sorted(unknown_states)}")

    reachable = {"PLANNED"}
    for source, moves in transitions.items():
        for move in moves:
            target = move.get("to")
            if target not in lifecycle:
                errors.append(f"lifecycle_transitions[{source}] moves to unknown state {target!r}")
            if not move.get("condition"):
                errors.append(f"lifecycle_transitions[{source}] -> {target} has no condition; "
                              f"a transition without required evidence is not enforceable")
            reachable.add(target)
    unreachable = lifecycle - reachable
    if unreachable:
        errors.append(f"lifecycle states no transition can reach: {sorted(unreachable)}")

    # ---- 8. routing table is well formed and resolvable --------------------
    skill_names = {p.name for p in (ROOT / "skills").iterdir()
                   if p.is_dir() and (p / "SKILL.md").exists()}
    scope_classes = set(contract.get("orchestrator", {}).get("invalidation_scope_classes", []))
    stage_names = set(stage_order) | {"affected_runtime_contexts"}
    reason_codes = set()

    for entry in routing.get("symptom_classes", []):
        code = entry["id"]
        reason_codes.add(code)
        owner = entry.get("root_owner")
        candidates = entry.get("root_owner_candidates", [])
        if owner is None and not candidates:
            errors.append(f"routing {code}: root_owner is null with no root_owner_candidates")
        for name in [owner, *candidates]:
            if name and name not in skill_names and name not in NON_SKILL_OWNERS:
                errors.append(f"routing {code}: unknown owner {name!r}")
        scope = entry.get("invalidation_scope")
        if scope and scope not in scope_classes:
            errors.append(f"routing {code}: invalidation_scope {scope!r} is not in the contract enum")
        for target in entry.get("revalidation_scope", []):
            if target not in stage_names:
                errors.append(f"routing {code}: revalidation_scope names unknown stage {target!r}")
        status = entry.get("default_status")
        if status and status not in all_statuses:
            errors.append(f"routing {code}: default_status {status!r} is not any stage's exit status")

    for source, target in (routing.get("systemic_escalation", {}).get("escalation_map") or {}).items():
        for value in (source, target):
            if value not in scope_classes:
                errors.append(f"routing escalation_map references unknown scope {value!r}")

    # ---- 9. enum tokens in prose resolve to the contract -------------------
    # This replaces the old string-grep markers. Any G-level, L-level, or
    # invalidation-scope token written anywhere in the skills must exist in the
    # contract - which is exactly the check that would have caught the two
    # competing G-level vocabularies.
    for field, pattern in TOKEN_PATTERNS.items():
        declared = set(contract.get(field, []) or contract.get("orchestrator", {}).get(field, []))
        for skill, document in skill_documents():
            for token in set(pattern.findall(document.read_text(encoding="utf-8"))):
                if token not in declared:
                    errors.append(
                        f"{document.relative_to(ROOT)} uses {token!r}, which is not in "
                        f"toolkit-contract.yaml {field}"
                    )

    # ---- 10. reason codes named in skill docs resolve ---------------------
    code_pattern = re.compile(r"`([A-Z][A-Z_]{4,})`")
    known_uppercase = (reason_codes | lifecycle | scope_classes | all_statuses
                       | set(contract.get("requirement_states", []))
                       | set(contract.get("pipeline_stage_states", []))
                       | set(contract.get("severity", []))
                       | set(contract.get("verification_results", []))
                       | set(contract.get("generation_rework_levels", []))
                       | set(contract.get("art_style_loop_levels", []))
                       | {check["id"] for check in contract.get("accessibility", {}).get("required_checks", [])})
    # Vocabularies a specialist legitimately defines for its own internal use.
    local_vocabularies = {
        "REFERENCE_ANCHORED", "EXPLORATORY", "PREVIEWABLE", "DOWNLOADABLE", "LINK_ONLY",
        "BLOCKED", "UNAVAILABLE", "CANDIDATE", "ACTIVE", "REJECTED", "SUPERSEDED",
        "HARD_FORBIDDEN", "SOFT_AVOID", "BOUNDED", "ANTI_REFERENCE",
        "PREFERENCE_DELTA", "ANCHOR_MISMATCH", "GENERATION_FAILURE",
        "NEGATIVE_PATTERN_VIOLATION", "REFERENCE_GAP", "CATEGORY_DRIFT", "DIRECTION_REJECTION",
        "CONTENT_ERROR", "IDENTITY_DRIFT", "STYLE_DIMENSION_DRIFT", "CONSTRAINT_VIOLATION",
        "FAMILY_DRIFT", "STATE_READABILITY_FAILURE", "OUTPUT_TECHNICAL_FAILURE",
        "UPSTREAM_SPEC_AMBIGUITY", "USER_EXPLICIT", "USER_CALIBRATION_FEEDBACK",
        "REFERENCE_REJECTION", "GAME_SPEC_DERIVED", "RUNTIME_READABILITY_FINDING",
        "QC_RECURRING_FAILURE", "CANONICAL_PARENT_TO_STATES", "CANONICAL_PARENT_TO_DIRECTIONS",
        "PARENT_TO_ANIMATION", "STATE_TO_TRANSITION", "INDEPENDENT_BUT_SHARED_STYLE",
        "INTEGRATION_LOCAL", "INTEGRATION_SYSTEMIC", "NORMALIZATION_RUNTIME_MECHANICAL",
        "CONTENT_QC_ESCAPE", "CONTEXT_SENSITIVE_ASSET_FAILURE", "SEMANTIC_UNDEFINED",
        "INTENTIONAL_CHANGE", "SEMANTIC_REGRESSION", "COSMETIC_DELTA", "BASELINE_STALE",
        "PROPOSED", "CONFIRMED", "PRIMARY", "SECONDARY", "DISCOVERY_ONLY",
        "ASK", "PROPOSE", "INFER", "REJECT", "RESET",
        "BG-LIGHT", "BG-MID", "BG-DARK",
        "VISION_READY", "PROTOTYPE_READY", "ART_HANDOFF_READY", "ASSET_PLANNING_READY",
        "PRODUCTION_READY", "STYLE_DIRECTION_READY", "REFERENCE_GROUNDED",
        "CALIBRATION_READY", "ASSET_GENERATION_READY", "STYLE_PRODUCTION_READY",
    }
    for skill, document in skill_documents():
        for token in set(code_pattern.findall(document.read_text(encoding="utf-8"))):
            if token in known_uppercase or token in local_vocabularies:
                continue
            if token.startswith(("NEG-", "REF-", "ANCH-", "AST-", "CTX-", "CAP-", "HND-",
                                 "RWK-", "INV-", "FAM-", "BASE-", "RTV-", "OQ-", "REQ-",
                                 "D-", "GEO-", "A11Y_")):
                continue
            errors.append(
                f"{document.relative_to(ROOT)} uses `{token}`, which is not defined in "
                f"toolkit-contract.yaml, routing.yaml, or a known specialist vocabulary"
            )

    # ---- 11. mirrors --------------------------------------------------------
    for entry in mirrors.get("mirrors", []):
        source = ROOT / entry["source"]
        if not source.exists():
            errors.append(f"mirror source missing: {entry['source']}")
            continue
        for target_skill in entry["targets"]:
            if target_skill not in skill_names:
                errors.append(f"mirror manifest targets unknown skill: {target_skill}")
                continue
            mirrored = ROOT / "skills" / target_skill / "references" / source.name
            if not mirrored.exists():
                errors.append(f"missing mirror {mirrored.relative_to(ROOT)}; run scripts/sync_contracts.py")
            elif source.read_text(encoding="utf-8") not in mirrored.read_text(encoding="utf-8"):
                errors.append(f"stale mirror {mirrored.relative_to(ROOT)}; run scripts/sync_contracts.py")

    # ---- 12. skills are well formed ---------------------------------------
    for skill_dir in sorted((ROOT / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill_dir.name}: missing SKILL.md")
            continue
        text = skill_md.read_text(encoding="utf-8")
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
        if not match:
            errors.append(f"{skill_dir.name}: SKILL.md has no YAML frontmatter")
            continue
        frontmatter = yaml.safe_load(match.group(1))
        if frontmatter.get("name") != skill_dir.name:
            errors.append(f"{skill_dir.name}: frontmatter name is {frontmatter.get('name')!r}")
        description = frontmatter.get("description", "")
        if not description:
            errors.append(f"{skill_dir.name}: missing description")
        elif not re.search(r"\bUse when\b", description):
            errors.append(
                f"{skill_dir.name}: description does not state a trigger condition. "
                f"Descriptions are how a skill gets selected; a capability statement "
                f"without 'Use when ...' competes with its neighbours for every request."
            )
        elif len(description) > 1024:
            errors.append(f"{skill_dir.name}: description is {len(description)} chars, over the 1024 limit")

        # Every relative path a skill document names must resolve inside it.
        for document in [skill_md, *sorted(skill_dir.glob("references/*.md"))]:
            body = document.read_text(encoding="utf-8")
            for candidate in set(re.findall(r"`((?:references|scripts)/[A-Za-z0-9_.-]+)`", body)):
                if not (skill_dir / candidate).exists():
                    errors.append(
                        f"{document.relative_to(ROOT)} references {candidate!r}, "
                        f"which does not exist in the skill directory"
                    )

    # ---- 13. schemas -------------------------------------------------------
    unsupported = store.unsupported_keywords()
    if unsupported:
        errors.append(
            f"contracts/schemas uses keywords the bundled validator does not implement: "
            f"{unsupported}. Either avoid them or extend scripts/lib/minischema.py."
        )
    for schema_path in sorted((ROOT / "contracts" / "schemas").glob("*.json")):
        try:
            json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{schema_path.name} is not valid JSON: {exc}")

    # ---- 14. profiles ------------------------------------------------------
    for name, profile in profiles.items():
        for stage in profile.get("required_stages", []) + profile.get("optional_stages", []):
            if stage not in stage_order:
                errors.append(f"profile {name} names unknown stage {stage!r}")
        ceiling = profile.get("promotion_ceiling")
        if ceiling and ceiling not in lifecycle:
            errors.append(f"profile {name} promotion_ceiling {ceiling!r} is not a lifecycle state")

    # ---- 15. packaging -----------------------------------------------------
    package_path = ROOT / "package.json"
    if package_path.exists():
        package = json.loads(package_path.read_text(encoding="utf-8"))
        canonical = "rolot789/game-production-skills"
        urls = [(package.get("repository") or {}).get("url", ""),
                (package.get("bugs") or {}).get("url", ""),
                package.get("homepage", "")]
        if not all(canonical in value for value in urls if value):
            errors.append("package.json repository/bugs/homepage must point to rolot789/game-production-skills")
        shipped = set(package.get("files", []))
        for needed in ("skills/", "contracts/", "scripts/"):
            if needed not in shipped:
                errors.append(
                    f"package.json files is missing {needed!r}; consumers would install a "
                    f"toolkit whose own documents point at files that were never shipped"
                )

    # ---- output ------------------------------------------------------------
    if errors:
        print("CONTRACT VALIDATOR: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("CONTRACT VALIDATOR: PASS")
    print(f"- contract version: {version}")
    print(f"- stages: {len(stage_order)}  skills: {len(skill_names)}")
    print(f"- lifecycle states: {len(lifecycle)}  transitions declared for all, all reachable")
    print(f"- routing symptom classes: {len(reason_codes)}  all owners and scopes resolve")
    print(f"- schemas: {len(store.schemas)}  all parse, no unsupported keywords")
    print(f"- mirrors: in sync  canonical path keys: {len(required_paths)}")
    print("- enum tokens in skill prose: all resolve against the contract")


if __name__ == "__main__":
    main()
