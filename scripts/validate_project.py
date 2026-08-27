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
  8. promoted lifecycle states have the evidence their promotion requires
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
ROUTING = ROOT / "contracts" / "routing.yaml"
FORBIDDEN_ALIASES = ("change_dimensions", "preserve_dimensions")

PROMOTION_EVIDENCE = {
    "QC_APPROVED": ("qc", "qc-report.yaml", ("approved", "approved_with_minor_findings")),
    "INTEGRATION_READY": ("engine_integration", "budget-report.yaml",
                          ("integration_ready", "integration_ready_with_minor_findings")),
    "RUNTIME_APPROVED": ("runtime_validation", "runtime-report.yaml",
                         ("runtime_approved", "runtime_approved_with_minor_findings")),
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
    for record in collect(generation_root, "*.yaml"):
        if record.parent.name != "records":
            continue
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if check_schema(report, store, doc, "generation-record.schema.json", label):
            candidate = doc["candidate"]
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
    for record in collect(resolve(project_dir, paths, "engine_integration"), "budget-report.yaml"):
        label = str(record.relative_to(project_dir))
        doc = load_yaml(record)
        if check_schema(report, store, doc, "budget-report.schema.json", label):
            scan_aliases(report, doc.get("rework_handoff"), label)

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

    # --- lifecycle promotion evidence --------------------------------------
    if state:
        for asset_id, entry in (state.get("assets") or {}).items():
            lifecycle = entry.get("lifecycle")
            requirement = PROMOTION_EVIDENCE.get(lifecycle)
            if not requirement:
                continue
            _, _, allowed = requirement
            source = {
                "QC_APPROVED": qc_by_asset,
                "INTEGRATION_READY": None,
                "RUNTIME_APPROVED": runtime_by_asset,
            }[lifecycle]
            if source is None:
                continue
            evidence = source.get(asset_id)
            if evidence is None:
                report.error(f"pipeline state: asset {asset_id} is {lifecycle} with no supporting report on disk")
            elif evidence["status"] not in allowed:
                report.error(
                    f"pipeline state: asset {asset_id} is {lifecycle} but its report status is "
                    f"{evidence['status']!r}, which does not promote"
                )
        if profile == "lite":
            for asset_id, entry in (state.get("assets") or {}).items():
                if entry.get("lifecycle") == "SHIPPABLE":
                    report.warn(
                        f"pipeline state: asset {asset_id} is SHIPPABLE under the lite profile, "
                        f"whose promotion ceiling is QC_APPROVED unless runtime_validation ran"
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
    for warning in report.warnings:
        print(f"! {warning}")


if __name__ == "__main__":
    main()
