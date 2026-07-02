#!/usr/bin/env python3
"""Verify an archive can initialize and self-validate a disposable project."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def run(command: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an Agents-Team distribution ZIP.")
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        package = root / "package"
        project = root / "project"
        with zipfile.ZipFile(args.archive) as source:
            source.extractall(package)
        project.mkdir()
        (project / "pyproject.toml").write_text('[project]\nname="e2e"\nversion="0.0.0"\n', encoding="utf-8")
        (project / "tests").mkdir()
        run(["git", "init", "-q", "-b", "main"], project)
        run(["git", "config", "user.email", "verify@example.com"], project)
        run(["git", "config", "user.name", "Distribution Verify"], project)
        run(["git", "add", "."], project)
        run(["git", "commit", "-q", "-m", "fixture"], project)
        plugin = package / "plugins" / "agents-team"
        package_tests = run(
            [sys.executable, "-m", "unittest", "discover", "-s", "plugins/agents-team/tests", "-v"],
            package,
        )
        init_result = run([sys.executable, str(plugin / "scripts/initialize_project.py"), str(project), "--apply"])
        validation = run([sys.executable, str(project / ".codex/scripts/validate_team_collaboration.py"), str(project)])
        manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        print(json.dumps({
            "status": "valid",
            "plugin": manifest["name"],
            "version": manifest["version"],
            "packageTests": "passed" if package_tests.returncode == 0 else "failed",
            "initialization": json.loads(init_result.stdout)["status"],
            "projectValidation": validation.stdout.strip(),
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
