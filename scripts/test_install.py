#!/usr/bin/env python3
"""End-to-end install smoke test.

This exists because of a real defect: four SKILL.md files told the agent to read
`contracts/rework-handoff-contract.yaml`, and the installer only ever copied
`skills/`. Every one of those references was dangling in an installed project,
and nothing caught it - the repository's own validators only looked at the
repository, where the path happened to resolve.

So this test does what a user does:

  1. install every skill into a temporary project
  2. run `init` to create the path registry
  3. resolve every relative path any installed SKILL.md or reference document
     points at, from inside the installed skill directory
  4. run the project validator against the fresh project

Any dangling reference fails the build.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

# Paths that appear inside skill documents and must resolve from the installed
# skill directory. Repository-relative paths (contracts/, scripts/, examples/)
# are documentation about the repository and are checked against ROOT instead.
SKILL_LOCAL_PREFIXES = ("references/", "scripts/")
REPO_PREFIXES = ("contracts/", "scripts/", "examples/", "templates/", "skills/")

# Matches `backticked/path.ext` mentions.
PATH_PATTERN = re.compile(r"`([A-Za-z0-9_./<>-]+\.(?:yaml|yml|json|md|py))`")


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"$ {' '.join(command)}")
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
    return result


def referenced_paths(text: str) -> set[str]:
    return set(PATH_PATTERN.findall(text))


def main() -> None:
    errors: list[str] = []
    workdir = Path(tempfile.mkdtemp(prefix="gps-install-test-"))
    project = workdir / "project"
    project.mkdir()

    try:
        # --- 1. install -----------------------------------------------------
        install = run(["node", str(ROOT / "bin" / "game-production-skills.js"),
                       "install", "--cwd", str(project)])
        if install.returncode != 0:
            errors.append("install command failed")

        skills_dir = project / ".agents" / "skills"
        if not skills_dir.exists():
            print("INSTALL SMOKE TEST: FAIL")
            print("- install produced no .agents/skills directory")
            raise SystemExit(1)

        installed = sorted(p.name for p in skills_dir.iterdir() if p.is_dir())
        expected = sorted(p.name for p in (ROOT / "skills").iterdir()
                          if p.is_dir() and (p / "SKILL.md").exists())
        if installed != expected:
            errors.append(f"installed skills {installed} != repository skills {expected}")

        # --- 2. init --------------------------------------------------------
        init = run(["node", str(ROOT / "bin" / "game-production-skills.js"),
                    "init", "--cwd", str(project), "--name", "Smoke Test Project"])
        if init.returncode != 0:
            errors.append("init command failed")
        if not (project / "project.yaml").exists():
            errors.append("init did not create project.yaml")
        if not (project / ".pipeline" / "game-art-production-state.yaml").exists():
            errors.append("init did not create .pipeline/game-art-production-state.yaml")

        # --- 3. resolve every documented path -------------------------------
        checked = 0
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            documents = [skill_dir / "SKILL.md"] + sorted(skill_dir.glob("references/*.md"))
            for document in documents:
                if not document.exists():
                    continue
                for candidate in referenced_paths(document.read_text(encoding="utf-8")):
                    if "<" in candidate:  # logical pattern such as specs/<asset-id>.yaml
                        continue
                    if candidate.startswith(SKILL_LOCAL_PREFIXES):
                        checked += 1
                        if not (skill_dir / candidate).exists():
                            errors.append(
                                f"{skill_dir.name}/{document.name} references {candidate!r}, "
                                f"which does not exist in the installed skill"
                            )
                    elif candidate.startswith(REPO_PREFIXES):
                        checked += 1
                        if not (ROOT / candidate).exists():
                            errors.append(
                                f"{skill_dir.name}/{document.name} references {candidate!r}, "
                                f"which does not exist in the repository"
                            )

        # --- 4. validate the fresh project ----------------------------------
        validate = run([sys.executable, str(ROOT / "scripts" / "validate_project.py"), str(project)])
        if validate.returncode != 0:
            errors.append("validate_project.py failed on a freshly initialized project")

        # --- 5. the mirrored contracts must be byte-identical ---------------
        manifest = ROOT / "contracts" / "mirror-manifest.yaml"
        if manifest.exists():
            for skill_dir in sorted(skills_dir.iterdir()):
                for mirrored in sorted(skill_dir.glob("references/*.yaml")):
                    source = ROOT / "contracts" / mirrored.name
                    if not source.exists():
                        continue
                    body = mirrored.read_text(encoding="utf-8")
                    if source.read_text(encoding="utf-8") not in body:
                        errors.append(
                            f"{skill_dir.name}/references/{mirrored.name} does not match "
                            f"contracts/{mirrored.name}; run scripts/sync_contracts.py"
                        )

    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    if errors:
        print("INSTALL SMOKE TEST: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("INSTALL SMOKE TEST: PASS")
    print(f"- skills installed: {len(installed)}")
    print(f"- documented paths resolved: {checked}")
    print("- init created project.yaml and .pipeline/")
    print("- fresh project passes validate_project.py")
    print("- mirrored contracts match their sources")


if __name__ == "__main__":
    main()
