#!/usr/bin/env python3
"""Archive superseded artifacts and prune candidate images nothing references.

The toolkit says provenance is append-only even when artifacts are superseded,
and its file layout said otherwise: normalization records, QC reports, and
runtime reports live at fixed per-asset paths and were simply overwritten, so
what a rework rejected - and why - was gone. Meanwhile generation candidates
accumulated with no policy at all.

    python3 scripts/retain.py archive <project-dir> <artifact-path> [...]
    python3 scripts/retain.py prune <project-dir> [--apply]

`archive` snapshots artifacts into `.pipeline/history/` and appends to the
ledger. It is content-triggered: an artifact whose bytes already match the most
recent archived copy supersedes nothing, so nothing is written.

`prune` deletes candidate images that no active record depends on, and marks
their generation records `pruned: true`. The record is never deleted - it is
the provenance. A pruned candidate keeps its id, hash, screening result, and
rejection reason after the pixels are gone.

Prune is dry-run by default. Pass --apply to actually delete.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import shutil
import sys
import yaml

def _contract_path() -> Path:
    """Resolve the contract from an installed skill or from the repository.

    An installed skill is a self-contained directory and cannot reach a
    repository-root contracts/, so the mirrored copy under references/ is the
    one that exists in a real install.
    """
    here = Path(__file__).resolve().parent
    for candidate in (here.parent / "references" / "toolkit-contract.yaml",
                      here.parents[2] / "contracts" / "toolkit-contract.yaml"):
        if candidate.exists():
            return candidate
    raise SystemExit("cannot locate toolkit-contract.yaml")


CONTRACT = _contract_path()
DEFAULT_HISTORY = ".pipeline/history/"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_project(project_dir: Path) -> dict:
    project_file = project_dir / "project.yaml"
    if not project_file.exists():
        raise SystemExit(f"no project.yaml in {project_dir}")
    return yaml.safe_load(project_file.read_text(encoding="utf-8"))


def history_root(project_dir: Path, project: dict) -> Path:
    return project_dir / (project.get("paths") or {}).get("history", DEFAULT_HISTORY)


def read_ledger(root: Path) -> dict:
    path = root / "ledger.yaml"
    if not path.exists():
        return {"version": 3, "entries": []}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {"version": 3, "entries": []}


def write_ledger(root: Path, ledger: dict) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "ledger.yaml").write_text(
        yaml.safe_dump(ledger, sort_keys=False, allow_unicode=True), encoding="utf-8")


def cmd_archive(args) -> int:
    project_dir = Path(args.project).resolve()
    project = load_project(project_dir)
    root = history_root(project_dir, project)
    ledger = read_ledger(root)
    archived_hashes = {entry["superseded_hash"] for entry in ledger["entries"]}

    written = 0
    for raw in args.artifact:
        source = (project_dir / raw).resolve()
        if not source.exists():
            print(f"! {raw}: does not exist, nothing to archive", file=sys.stderr)
            continue
        rel = source.relative_to(project_dir)
        digest = sha256_file(source)

        # Content-triggered, not write-triggered. Rewriting an artifact with the
        # same bytes supersedes nothing, and an archive full of identical copies
        # makes the real supersessions harder to find.
        if digest in archived_hashes:
            print(f"= {rel}: already archived at this content hash")
            continue

        target = root / rel.parent / f"{rel.stem}.{digest[:12]}{rel.suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        ledger["entries"].append({
            "archived_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "artifact": str(rel),
            "superseded_hash": digest,
            "archive_path": str(target.relative_to(project_dir)),
            "reason": args.reason,
        })
        archived_hashes.add(digest)
        written += 1
        print(f"+ {rel} -> {target.relative_to(project_dir)}")

    if written:
        write_ledger(root, ledger)
    print(f"archived {written} artifact(s); ledger has {len(ledger['entries'])} entries")
    return 0


def cmd_prune(args) -> int:
    project_dir = Path(args.project).resolve()
    project = load_project(project_dir)
    paths = project.get("paths") or {}
    contract = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    keep_recent = args.keep or (
        ((contract.get("retention") or {}).get("generation_candidates") or {})
        .get("keep_recent_per_job", 2))

    generation_root = project_dir / paths.get("generation", "generation/")
    normalized_root = project_dir / paths.get("normalized", "normalized/")
    if not generation_root.exists():
        raise SystemExit(f"no generation directory at {generation_root}")

    # Anything a normalization record consumed stays, whatever the index says
    # about selection: that record's lineage claim points at these bytes.
    consumed: set[str] = set()
    if normalized_root.exists():
        for record_path in normalized_root.rglob("normalization-record.yaml"):
            record = yaml.safe_load(record_path.read_text(encoding="utf-8")) or {}
            candidate = record.get("input_candidate") or {}
            if candidate.get("content_hash"):
                consumed.add(candidate["content_hash"])

    pruned, kept = [], 0
    for asset_dir in sorted(p for p in generation_root.iterdir() if p.is_dir()):
        records_dir = asset_dir / "records"
        if not records_dir.exists():
            continue

        records = {}
        for record_path in sorted(records_dir.glob("*.yaml")):
            record = yaml.safe_load(record_path.read_text(encoding="utf-8")) or {}
            if record.get("candidate"):
                records[record["candidate"]["id"]] = (record_path, record)

        # Newest-first within each job version, so "keep the last N" means the
        # N most recent attempts rather than N arbitrary ones.
        def sort_key(candidate_id: str):
            job, _, ordinal = candidate_id.partition("-c")
            return (job, -int(ordinal) if ordinal.isdigit() else 0)

        seen_per_job: dict[str, int] = {}
        for candidate_id in sorted(records, key=sort_key):
            record_path, record = records[candidate_id]
            candidate = record["candidate"]
            job = candidate_id.partition("-c")[0]
            seen_per_job[job] = seen_per_job.get(job, 0) + 1

            image = project_dir / candidate["path"]
            if candidate.get("pruned") or not image.exists():
                continue
            if candidate.get("selected"):
                kept += 1
                continue
            if candidate["content_hash"] in consumed:
                kept += 1
                continue
            if seen_per_job[job] <= keep_recent:
                kept += 1
                continue

            pruned.append((image, record_path, record))

    for image, record_path, record in pruned:
        rel = image.relative_to(project_dir)
        if not args.apply:
            print(f"would prune {rel}  ({image.stat().st_size} bytes)")
            continue
        image.unlink()
        record["candidate"]["pruned"] = True
        record["candidate"]["pruned_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        record_path.write_text(
            yaml.safe_dump(record, sort_keys=False, allow_unicode=True), encoding="utf-8")
        print(f"pruned {rel}")

    freed = sum(image.stat().st_size for image, _, _ in pruned) if not args.apply else 0
    print(f"\n{len(pruned)} prunable, {kept} retained (selected, consumed, or within the "
          f"last {keep_recent} per job)")
    if pruned and not args.apply:
        print(f"would free {freed} bytes; re-run with --apply to delete")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    archive = sub.add_parser("archive", help="snapshot artifacts before they are overwritten")
    archive.add_argument("project")
    archive.add_argument("artifact", nargs="+", help="project-relative paths")
    archive.add_argument("--reason", default=None)
    archive.set_defaults(func=cmd_archive)

    prune = sub.add_parser("prune", help="delete candidate images nothing references")
    prune.add_argument("project")
    prune.add_argument("--apply", action="store_true", help="actually delete; default is a dry run")
    prune.add_argument("--keep", type=int, default=None,
                       help="candidates to retain per job version (default from the contract)")
    prune.set_defaults(func=cmd_prune)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
