#!/usr/bin/env python3
"""Validate a real game project against the toolkit contracts.

`validate_contracts.py` checks that this repository is internally consistent.
This script checks the thing that actually matters to a user: that the
artifacts a pipeline run produced are well formed, mutually consistent, and
carry lineage strong enough for dependency-aware invalidation.

    python3 scripts/validate_project.py <project-dir> [--profile lite|full]

Checks performed:
  1. project.yaml conforms to its schema and registers every required path key
  2. every discovered artifact conforms to its schema
  3. recorded content hashes match the bytes actually on disk
  4. QC verdicts are bound to the normalized output they claim to evaluate
  5. runtime approval is bound to the QC report it claims to follow
  6. every reason_code resolves against contracts/routing.yaml
  7. rework handoffs use canonical scope fields, never specialist-local aliases
  8. promoted lifecycle states have the evidence their promotion requires,
     including INTEGRATION_READY and the whole-chain coherence SHIPPABLE claims
  9. the active profile's required stages and artifacts are actually present
 10. no asset has exceeded the rework_budget for one route
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.minischema import SchemaStore, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "contracts" / "schemas"
CONTRACT = ROOT / "contracts" / "toolkit-contract.yaml"
ROUTING = ROOT / "contracts" / "routing.yaml"
PROFILE_DIR = ROOT / "contracts" / "profiles"
FORBIDDEN_ALIASES = ("change_dimensions", "preserve_dimensions")

QC_PROMOTES = ("approved", "approved_with_minor_findings")
INTEGRATION_PROMOTES = ("integration_ready", "integration_ready_with_minor_findings")
RUNTIME_PROMOTES = ("runtime_approved", "runtime_approved_with_minor_findings")

# Which report authorizes each promoted lifecycle state. SHIPPABLE is absent on
# purpose: no single report authorizes it. It requires the whole chain to agree,
# which is checked separately by `check_shippable`.
PROMOTION_EVIDENCE = {
    "QC_APPROVED": QC_PROMOTES,
    "INTEGRATION_READY": INTEGRATION_PROMOTES,
    "RUNTIME_APPROVED": RUNTIME_PROMOTES,
}

# Profiles name required artifacts by logical filename; project.yaml registers
# them by path key. This is the map between the two vocabularies.
#
# A key that project.schema.json marks required is always enforced. The rest are
# enforced only when the project registers them, because the registry is how a
# project declares which optional artifacts it keeps - an unregistered
# calibration-plan.yaml means "this project does not use one", not "it is lost".
ARTIFACT_PATH_KEYS = {
    "game-spec.yaml": "game_spec",
    "GameSpec.md": "game_spec_human",
    "requirement-state.yaml": "requirement_state",
    "decision-log.md": "game_spec_decision_log",
    "art-style.yaml": "art_style",
    "ArtStyle.md": "art_style_human",
    "style-requirement-state.yaml": "style_requirement_state",
    "style-decision-log.md": "style_decision_log",
    "style-anchor-manifest.yaml": "style_anchors",
    "calibration-plan.yaml": "calibration_plan",
    "reference-corpus.yaml": "reference_corpus",
    "reference-search-history.yaml": "reference_search_history",
    "style-constraint-ledger.yaml": "style_constraint_ledger",
    "style-loop-state.yaml": "style_loop_state",
    "asset-manifest.yaml": "asset_manifest",
    "specs/<asset-id>.yaml": "asset_specs",
    "generation/<asset-id>/job.yaml": "generation",
    "generation/<asset-id>/generation-contract.yaml": "generation",
    "generation/<asset-id>/prompt.md": "generation",
    "generation/<asset-id>/candidate-index.yaml": "generation",
    "generation/<asset-id>/records/*.yaml": "generation",
    "normalized/<asset-id>/runtime/*": "normalized",
    "normalized/<asset-id>/normalization-record.yaml": "normalized",
    "normalized/<asset-id>/geometry-report.yaml": "normalized",
    "qc/<asset-id>/qc-report.yaml": "qc",
    "engine-integration/<target-id>/integration-plan.yaml": "engine_integration",
    "engine-integration/<target-id>/import-settings.yaml": "engine_integration",
    "engine-integration/<target-id>/budget-report.yaml": "engine_integration",
    "runtime-validation/<asset-id>/runtime-validation-plan.yaml": "runtime_validation",
    "runtime-validation/<asset-id>/runtime-report.yaml": "runtime_validation",
    "runtime-validation/<asset-id>/evidence-manifest.yaml": "runtime_validation",
}

# Keys project.schema.json requires; always enforced when the profile asks.
ALWAYS_REGISTERED = {
    "game_spec", "art_style", "style_anchors", "style_constraint_ledger",
    "asset_manifest", "asset_specs", "generation", "normalized", "qc",
    "engine_integration", "runtime_validation", "pipeline_state", "handoffs",
    "invalidation_ledger", "rework_queue",
}


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checked = 0

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def check_schema(report: Report, store: SchemaStore, doc, schema: str, label: str) -> bool:
    report.checked += 1
    errors = validate(doc, schema, store)
    for error in errors:
        report.error(f"{label} [{schema}] {error}")
    return not errors


def resolve(project_dir: Path, paths: dict, key: str) -> Path | None:
    value = paths.get(key)
    return None if value is None else project_dir / value


def collect(base: Path | None, filename: str) -> list[Path]:
    if base is None or not base.exists():
        return []
    return sorted(base.rglob(filename))


def verify_hash(report: Report, project_dir: Path, recorded_path: str, recorded_hash: str, label: str) -> None:
    target = project_dir / recorded_path
    if not target.exists():
        report.error(f"{label}: recorded path does not exist: {recorded_path}")
        return
    actual = sha256_file(target)
    if actual != recorded_hash:
        report.error(
            f"{label}: content_hash mismatch for {recorded_path}\n"
            f"    recorded {recorded_hash}\n"
            f"    on disk  {actual}"
        )


def scan_aliases(report: Report, node, label: str, path: str = "$") -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key in FORBIDDEN_ALIASES:
                report.error(
                    f"{label}: {path}.{key} is a specialist-local alias and must not appear "
                    f"in a routed handoff; serialize to change_scope / preserve_scope"
                )
            scan_aliases(report, value, label, f"{path}.{key}")
    elif isinstance(node, list):
        for index, item in enumerate(node):
            scan_aliases(report, item, label, f"{path}[{index}]")


# Happy-path ordering, used to decide which stages an asset has actually
# reached. Rework and INVALIDATED states are deliberately absent: an asset in
# rework has not reached the next stage, so its artifacts are not yet required.
LIFECYCLE_ORDER = [
    "PLANNED", "READY_FOR_GENERATION", "GENERATED", "NORMALIZED",
    "QC_APPROVED", "INTEGRATION_READY", "RUNTIME_APPROVED", "SHIPPABLE",
]
STAGE_PRODUCES = {
    "asset_planning": "PLANNED",
    "generation": "GENERATED",
    "normalization": "NORMALIZED",
    "asset_qc": "QC_APPROVED",
    "engine_integration": "INTEGRATION_READY",
    "runtime_validation": "RUNTIME_APPROVED",
}


def reached(lifecycle: str, stage: str) -> bool:
    """True when an asset in `lifecycle` has passed through `stage`."""
    minimum = STAGE_PRODUCES.get(stage)
    if minimum is None or lifecycle not in LIFECYCLE_ORDER:
        return False
    return LIFECYCLE_ORDER.index(lifecycle) >= LIFECYCLE_ORDER.index(minimum)


def load_profile(name: str) -> dict:
    path = PROFILE_DIR / f"{name}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in PROFILE_DIR.glob("*.yaml"))
        raise SystemExit(f"unknown profile {name!r}; contracts/profiles/ has {available}")
    return load_yaml(path)


def profile_artifacts(profile: dict) -> dict[str, list[str]]:
    """Normalize the two shapes `required_artifacts` takes across the profiles.

    `full` keys it by stage. `lite` is a flat list, because the three artifacts
    it names exist regardless of which stage is running. Both mean the same
    thing, so both are normalized to stage -> artifacts with `*` for "any stage".
    """
    declared = profile.get("required_artifacts") or {}
    if isinstance(declared, list):
        return {"*": list(declared)}
    return {stage: list(items or []) for stage, items in declared.items()}


def missing_for(project_dir: Path, base_rel: str, logical: str, identifiers) -> list[str]:
    """Which concrete paths a logical artifact pattern expects but does not find.

    The path key already names the pattern's first segment (`qc` registers
    `qc/`, and the pattern is `qc/<asset-id>/qc-report.yaml`), so the segment is
    dropped rather than joined twice.
    """
    base = project_dir / base_rel
    if "<asset-id>" not in logical and "<target-id>" not in logical:
        return [] if base.exists() else [base_rel]

    tail = logical.split("/", 1)[1]
    missing = []
    for identifier in identifiers:
        rel = tail.replace("<asset-id>", identifier).replace("<target-id>", identifier)
        found = list(base.glob(rel)) if "*" in rel else ([base / rel] if (base / rel).exists() else [])
        if not found:
            missing.append(str(Path(base_rel) / rel))
    return missing


def integration_evidence(asset_id: str, plans: list, budgets: list) -> str | None:
    """None when engine integration promotes this asset, else why it does not."""
    if not any(doc.get("status") in INTEGRATION_PROMOTES for doc in budgets):
        return "no budget-report.yaml on disk has a promoting status"
    if not plans:
        # budget_check.py measures every normalized asset, so a promoting budget
        # report covers them all when no plan narrows the set.
        return None
    covering = [
        doc for doc in plans
        if doc.get("status") in INTEGRATION_PROMOTES
        and any(f"/{asset_id}/" in (item.get("path") or "") for item in (doc.get("inputs") or []))
    ]
    return None if covering else "no promoting integration-plan.yaml lists this asset in its inputs"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", help="path to the project directory containing project.yaml")
    parser.add_argument("--profile", choices=["lite", "full"], default=None)
    args = parser.parse_args()

    project_dir = Path(args.project).resolve()
    report = Report()
    store = SchemaStore(SCHEMA_DIR)

    project_file = project_dir / "project.yaml"
    if not project_file.exists():
        print("PROJECT VALIDATOR: FAIL")
        print(f"- no project.yaml in {project_dir}")
        print("- run: npx game-production-skills init --name \"<project>\"")
        raise SystemExit(1)

    project = load_yaml(project_file)
    check_schema(report, store, project, "project.schema.json", "project.yaml")

    paths = project.get("paths") or {}
    profile = args.profile or project.get("profile") or "full"

    routing = load_yaml(ROUTING)
    contract = load_yaml(CONTRACT)
    known_reason_codes = {entry["id"] for entry in routing.get("symptom_classes", [])}

    # --- pipeline state -----------------------------------------------------
    state_path = resolve(project_dir, paths, "pipeline_state")
    state = None
    if state_path and state_path.exists():
        state = load_yaml(state_path)
        check_schema(report, store, state, "pipeline-state.schema.json", "pipeline state")

    # --- asset manifest -----------------------------------------------------
    manifest_path = resolve(project_dir, paths, "asset_manifest")
    if manifest_path and manifest_path.exists():
        manifest = load_yaml(manifest_path)
        check_schema(report, store, manifest, "asset-manifest.schema.json", "asset-manifest.yaml")

    # --- asset specs --------------------------------------------------------
    for spec_file in collect(resolve(project_dir, paths, "asset_specs"), "*.yaml"):
        label = str(spec_file.relative_to(project_dir))
        check_schema(report, store, load_yaml(spec_file), "asset-spec.schema.json", label)

    # --- generation records -------------------------------------------------
    generation_root = resolve(project_dir, paths, "generation")
    pruned_candidates: dict[str, tuple[str, str]] = {}
    for record in collect(generation_root, "*.yaml"):
        if record.parent.name != "records":
            continue
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if check_schema(report, store, doc, "generation-record.schema.json", label):
            candidate = doc["candidate"]
            if candidate.get("pruned"):
                # The record outlives the pixels on purpose, so the bytes are not
                # required - but pruning something still in use would silently
                # break the lineage the record claims.
                if candidate.get("selected"):
                    report.error(
                        f"{label}: candidate {candidate['id']} is marked pruned and selected; "
                        f"the selected candidate's bytes must be retained"
                    )
                pruned_candidates[candidate["content_hash"]] = (label, candidate["id"])
            else:
                verify_hash(report, project_dir, candidate["path"], candidate["content_hash"], label)

    # --- normalization records ---------------------------------------------
    normalized_root = resolve(project_dir, paths, "normalized")
    normalized_by_asset: dict[str, dict] = {}
    for record in collect(normalized_root, "normalization-record.yaml"):
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if check_schema(report, store, doc, "normalization-record.schema.json", label):
            normalized_by_asset[doc["asset_id"]] = doc
            verify_hash(report, project_dir, doc["output"]["path"], doc["output"]["content_hash"], label)
            candidate_hash = doc["input_candidate"]["content_hash"]
            if candidate_hash in pruned_candidates:
                origin, candidate_id = pruned_candidates[candidate_hash]
                report.error(
                    f"{label}: consumes candidate {candidate_id}, which {origin} marks as pruned. "
                    f"A candidate a normalization record depends on must be retained"
                )
            else:
                verify_hash(
                    report, project_dir,
                    doc["input_candidate"]["path"], doc["input_candidate"]["content_hash"],
                    f"{label} (input candidate)",
                )
            if doc["validation"]["status"] != "pass":
                report.warn(f"{label}: normalization validation status is {doc['validation']['status']}")

    # --- QC reports ---------------------------------------------------------
    qc_by_asset: dict[str, dict] = {}
    for record in collect(resolve(project_dir, paths, "qc"), "qc-report.yaml"):
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if not check_schema(report, store, doc, "qc-report.schema.json", label):
            continue
        qc_by_asset[doc["asset_id"]] = doc
        scan_aliases(report, doc.get("rework_handoff"), label)
        for finding in doc.get("findings", []):
            code = finding.get("reason_code")
            if code and code not in known_reason_codes:
                report.error(f"{label}: finding {finding['id']} has unknown reason_code {code!r}")
        handoff = doc.get("rework_handoff")
        if handoff:
            check_schema(report, store, handoff, "rework-handoff.schema.json", f"{label} rework_handoff")
            for code in handoff.get("reason_codes", []):
                if code not in known_reason_codes:
                    report.error(f"{label}: rework_handoff reason_code {code!r} is not in contracts/routing.yaml")

        # Lineage binding: the verdict must name the exact output it judged.
        claimed = doc["evaluated"]["normalized_output"]
        norm = normalized_by_asset.get(doc["asset_id"])
        if norm and claimed["content_hash"] != norm["output"]["content_hash"]:
            report.error(
                f"{label}: QC verdict is bound to a normalized output that is no longer active\n"
                f"    qc evaluated  {claimed['content_hash']}\n"
                f"    active output {norm['output']['content_hash']}\n"
                f"    → this QC approval does not apply to the current asset"
            )

    # --- engine integration -------------------------------------------------
    integration_root = resolve(project_dir, paths, "engine_integration")
    budget_reports: list[dict] = []
    for record in collect(integration_root, "budget-report.yaml"):
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if check_schema(report, store, doc, "budget-report.schema.json", label):
            scan_aliases(report, doc.get("rework_handoff"), label)
            budget_reports.append(doc)

    # An atlas is a derived artifact whose inputs are the normalized outputs it
    # packed. A member whose bytes have changed since packing means the atlas
    # ships pixels that no longer exist upstream.
    for record in collect(integration_root, "atlas-manifest.yaml"):
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if not check_schema(report, store, doc, "atlas-manifest.schema.json", label):
            continue
        verify_hash(report, project_dir, doc["atlas"]["path"], doc["atlas"]["content_hash"], label)
        for member in doc["members"]:
            verify_hash(report, project_dir, member["source"], member["content_hash"],
                        f"{label} (member {member['asset_id']})")
            norm = normalized_by_asset.get(member["asset_id"])
            if norm and member["content_hash"] != norm["output"]["content_hash"]:
                report.error(
                    f"{label}: member {member['asset_id']} was packed from a normalized output "
                    f"that is no longer active\n"
                    f"    packed {member['content_hash']}\n"
                    f"    active {norm['output']['content_hash']}"
                )
        if doc["padding_px"] < 2:
            report.warn(
                f"{label}: padding is {doc['padding_px']} px; below 2 px neighbouring members "
                f"bleed under bilinear filtering at non-integer scale"
            )

    integration_plans: list[dict] = []
    for record in collect(integration_root, "integration-plan.yaml"):
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        integration_plans.append(doc)
        # An integration plan pins the QC reports it consumed. If one of those
        # has since changed, the plan describes assets that no longer exist in
        # that form, so the pin is checked like any other lineage claim.
        for item in doc.get("inputs") or []:
            if item.get("path") and item.get("content_hash"):
                verify_hash(report, project_dir, item["path"], item["content_hash"], label)

    # --- runtime reports ----------------------------------------------------
    runtime_by_asset: dict[str, dict] = {}
    for record in collect(resolve(project_dir, paths, "runtime_validation"), "runtime-report.yaml"):
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if not check_schema(report, store, doc, "runtime-report.schema.json", label):
            continue
        runtime_by_asset[doc["asset_id"]] = doc
        scan_aliases(report, doc.get("rework_handoff"), label)

        for finding in doc.get("findings", []):
            code = finding.get("reason_code")
            if code and code not in known_reason_codes:
                report.error(f"{label}: finding {finding['id']} has unknown reason_code {code!r}")
            if finding["severity"] in ("BLOCKER", "MAJOR") and not finding.get("capture_ids"):
                report.error(
                    f"{label}: finding {finding['id']} is {finding['severity']} with no capture_ids; "
                    f"a visual claim without rendered evidence is not a finding"
                )

        if doc["status"] in ("runtime_approved", "runtime_approved_with_minor_findings"):
            if doc.get("build", {}).get("executable") is False:
                report.error(
                    f"{label}: status {doc['status']} with build.executable false; "
                    f"supplied captures never produce runtime approval"
                )
            for untested in doc.get("untested", []):
                if untested.get("risk") == "high":
                    report.error(
                        f"{label}: status {doc['status']} while a high-risk context is untested "
                        f"({untested['context']}); expected partial_validation_only"
                    )

        qc = qc_by_asset.get(doc["asset_id"])
        claimed_qc = doc["integrated_lineage"]["qc_report"]
        if qc is not None and "content_hash" in claimed_qc:
            qc_path = project_dir / claimed_qc["path"]
            if qc_path.exists():
                actual = sha256_file(qc_path)
                if actual != claimed_qc["content_hash"]:
                    report.error(
                        f"{label}: runtime approval cites a QC report whose content has changed\n"
                        f"    cited  {claimed_qc['content_hash']}\n"
                        f"    actual {actual}"
                    )

        # The mixed-version case: a runtime report that approves an asset built
        # from a normalized output that is no longer the active one. The QC
        # binding above cannot catch it, because QC and runtime can each be
        # internally consistent while describing different generations.
        norm = normalized_by_asset.get(doc["asset_id"])
        claimed_output = doc["integrated_lineage"].get("normalized_output") or {}
        if (
            norm is not None
            and doc["status"] in RUNTIME_PROMOTES
            and claimed_output.get("content_hash")
            and claimed_output["content_hash"] != norm["output"]["content_hash"]
        ):
            report.error(
                f"{label}: runtime approval is bound to a normalized output that is no longer active\n"
                f"    runtime validated {claimed_output['content_hash']}\n"
                f"    active output     {norm['output']['content_hash']}\n"
                f"    → this runtime approval does not apply to the current asset"
            )

    # --- history ledger -----------------------------------------------------
    # Append-only provenance is only provenance if the archived bytes are still
    # the bytes that were archived.
    history = project_dir / paths.get("history", ".pipeline/history/")
    ledger_path = history / "ledger.yaml"
    archived = 0
    if ledger_path.exists():
        ledger = load_yaml(ledger_path) or {}
        for entry in ledger.get("entries") or []:
            archived += 1
            verify_hash(report, project_dir, entry["archive_path"], entry["superseded_hash"],
                        f"history ledger entry for {entry['artifact']}")

    # --- lifecycle promotion evidence --------------------------------------
    profile_doc = load_profile(profile)
    required_stages = set(profile_doc.get("required_stages") or [])
    rework_cap = ((contract.get("rework_budget") or {})
                  .get("same_route_repeats", {}).get("default_max", 2))

    if state:
        assets = state.get("assets") or {}
        for asset_id, entry in assets.items():
            lifecycle = entry.get("lifecycle")

            # Single-report promotions.
            allowed = PROMOTION_EVIDENCE.get(lifecycle)
            if allowed is not None:
                if lifecycle == "INTEGRATION_READY":
                    problem = integration_evidence(asset_id, integration_plans, budget_reports)
                    if problem:
                        report.error(
                            f"pipeline state: asset {asset_id} is INTEGRATION_READY but {problem}"
                        )
                else:
                    source = qc_by_asset if lifecycle == "QC_APPROVED" else runtime_by_asset
                    evidence = source.get(asset_id)
                    if evidence is None:
                        report.error(
                            f"pipeline state: asset {asset_id} is {lifecycle} with no supporting report on disk"
                        )
                    elif evidence["status"] not in allowed:
                        report.error(
                            f"pipeline state: asset {asset_id} is {lifecycle} but its report status is "
                            f"{evidence['status']!r}, which does not promote"
                        )

            # SHIPPABLE is not authorized by any single report. It claims that
            # every stage the active profile requires agrees about one lineage,
            # so it is the one promotion that has to be checked as a chain.
            if lifecycle == "SHIPPABLE":
                problems: list[str] = []
                norm = normalized_by_asset.get(asset_id)
                if norm is None:
                    problems.append("no normalization record on disk")

                qc = qc_by_asset.get(asset_id)
                if qc is None:
                    problems.append("no QC report on disk")
                elif qc["status"] not in QC_PROMOTES:
                    problems.append(f"QC status {qc['status']!r} does not promote")

                if "engine_integration" in required_stages:
                    problem = integration_evidence(asset_id, integration_plans, budget_reports)
                    if problem:
                        problems.append(problem)

                if "runtime_validation" in required_stages:
                    runtime = runtime_by_asset.get(asset_id)
                    if runtime is None:
                        problems.append("no runtime report on disk")
                    elif runtime["status"] not in RUNTIME_PROMOTES:
                        problems.append(f"runtime status {runtime['status']!r} does not promote")
                elif profile_doc.get("promotion_ceiling") != "SHIPPABLE":
                    # lite: RUNTIME_APPROVED and SHIPPABLE need executable runtime
                    # evidence regardless of profile, so the optional stage must
                    # actually have run.
                    runtime = runtime_by_asset.get(asset_id)
                    if runtime is None or runtime["status"] not in RUNTIME_PROMOTES:
                        problems.append(
                            f"the {profile} profile's promotion ceiling is "
                            f"{profile_doc.get('promotion_ceiling')!r}; SHIPPABLE additionally "
                            f"requires the optional runtime_validation stage to have promoted"
                        )

                if problems:
                    detail = "\n".join(f"    - {p}" for p in problems)
                    report.error(
                        f"pipeline state: asset {asset_id} is SHIPPABLE without coherent lineage "
                        f"across the stages the {profile} profile requires\n{detail}"
                    )

            # RUNTIME_APPROVED under a profile whose ceiling stops earlier.
            if (
                lifecycle == "RUNTIME_APPROVED"
                and "runtime_validation" not in required_stages
                and asset_id not in runtime_by_asset
            ):
                report.error(
                    f"pipeline state: asset {asset_id} is RUNTIME_APPROVED under the {profile} "
                    f"profile, where runtime_validation is optional and did not run; runtime "
                    f"approval requires executable runtime evidence regardless of profile"
                )

            # Rework budget: a route repeated past the cap is two stages
            # disagreeing, not a fix applied badly.
            for attempt in entry.get("rework_attempts") or []:
                if attempt.get("count", 0) > rework_cap:
                    report.error(
                        f"pipeline state: asset {asset_id} has been routed to "
                        f"{attempt['to']} for {attempt['reason_code']} {attempt['count']} times, "
                        f"exceeding rework_budget.same_route_repeats ({rework_cap}); "
                        f"escalate to a BLOCKER naming both stages instead of routing again"
                    )

    # --- profile required stages and artifacts ------------------------------
    stage_status = {name: (entry or {}).get("status")
                    for name, entry in ((state or {}).get("stages") or {}).items()}
    asset_lifecycles = {aid: (entry or {}).get("lifecycle")
                        for aid, entry in ((state or {}).get("assets") or {}).items()}
    # `lite` lists its required artifacts without stage keys, so they have no
    # per-stage status to gate on. They become required once the project has
    # actually begun: any planned asset, or any stage reported finished.
    started = bool(asset_lifecycles) or "COMPLETE" in stage_status.values()
    # Engine targets come from project.yaml, not from listing the integration
    # directory: atlases live there too, under their own ids, and a directory
    # listing cannot tell an atlas apart from a target.
    declared_target = (project.get("engine") or {}).get("id")
    target_ids = [declared_target] if declared_target else []

    for stage, artifacts in profile_artifacts(profile_doc).items():
        if stage != "*" and stage not in required_stages:
            continue
        for logical in artifacts:
            key = ARTIFACT_PATH_KEYS.get(logical)
            if key is None:
                report.error(
                    f"profile {profile}: required artifact {logical!r} has no entry in "
                    f"ARTIFACT_PATH_KEYS; validate_project.py cannot resolve it"
                )
                continue
            registered = paths.get(key)
            if registered is None:
                # The registry is how a project declares which optional
                # artifacts it keeps. Only the keys project.schema.json makes
                # mandatory are errors when absent.
                if key in ALWAYS_REGISTERED:
                    report.error(
                        f"project.yaml: paths.{key} is not registered, but the {profile} "
                        f"profile requires {logical!r}"
                    )
                continue

            if "<asset-id>" in logical:
                identifiers = [aid for aid, life in asset_lifecycles.items() if reached(life, stage)]
            elif "<target-id>" in logical:
                integrating = any(reached(life, "engine_integration") for life in asset_lifecycles.values())
                identifiers = target_ids if integrating else []
            else:
                # A stage-level artifact is required once the stage claims to be
                # finished. A project mid-run is not failed for work it has not
                # reached yet, and a project that has not started is not failed
                # at all - `init` writes project.yaml before anything exists.
                identifiers = []
                if stage == "*":
                    if not started:
                        continue
                elif stage_status.get(stage) != "COMPLETE":
                    continue

            if ("<asset-id>" in logical or "<target-id>" in logical) and not identifiers:
                continue
            for missing in missing_for(project_dir, registered, logical, identifiers):
                report.error(
                    f"profile {profile} requires {missing} for stage {stage}; it does not exist"
                )

    # --- output -------------------------------------------------------------
    if report.errors:
        print("PROJECT VALIDATOR: FAIL")
        print(f"- project: {project_dir}")
        print(f"- profile: {profile}")
        for error in report.errors:
            print(f"- {error}")
        for warning in report.warnings:
            print(f"! {warning}")
        raise SystemExit(1)

    print("PROJECT VALIDATOR: PASS")
    print(f"- project: {project_dir}")
    print(f"- profile: {profile}")
    print(f"- documents validated: {report.checked}")
    print(f"- normalized assets: {len(normalized_by_asset)}")
    print(f"- qc reports: {len(qc_by_asset)}")
    print(f"- runtime reports: {len(runtime_by_asset)}")
    if pruned_candidates:
        print(f"- pruned candidates: {len(pruned_candidates)} (records retained)")
    if archived:
        print(f"- archived supersessions: {archived}")
    for warning in report.warnings:
        print(f"! {warning}")


if __name__ == "__main__":
    main()
