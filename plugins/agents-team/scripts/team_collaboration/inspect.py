"""Conservative repository inspection without reading secret contents."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EMPTY_COMMANDS = {"test": "", "build": "", "lint": "", "typecheck": "", "e2e": ""}


def _package_manager(root: Path) -> str:
    if (root / "bun.lock").exists() or (root / "bun.lockb").exists():
        return "bun"
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    return "npm"


def _js_profile(root: Path) -> dict[str, Any] | None:
    package = root / "package.json"
    if not package.is_file():
        return None
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    dependencies = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
    project_type = "nextjs" if "next" in dependencies else "node"
    manager = _package_manager(root)
    scripts = data.get("scripts", {}) if isinstance(data.get("scripts", {}), dict) else {}
    commands = dict(EMPTY_COMMANDS)
    for key in commands:
        if key in scripts:
            commands[key] = f"{manager} run {key}"
    if "typecheck" not in scripts and (root / "tsconfig.json").exists():
        commands["typecheck"] = f"{manager} exec tsc --noEmit" if manager != "npm" else "npx tsc --noEmit"
    return {"projectType": project_type, "commands": commands}


def inspect_repository(root: Path) -> dict[str, Any]:
    root = root.resolve()
    profile = _js_profile(root)
    app_manifests = list((root / "apps").glob("*/package.json")) + list((root / "apps").glob("*/pyproject.toml")) if (root / "apps").is_dir() else []
    if len(app_manifests) >= 2:
        profile = {"projectType": "monorepo", "commands": dict(EMPTY_COMMANDS)}
    if profile is None and (list(root.glob("*.sln")) or list(root.glob("*.csproj"))):
        profile = {"projectType": "dotnet", "commands": {**EMPTY_COMMANDS, "test": "dotnet test", "build": "dotnet build"}}
    if profile is None and ((root / "pyproject.toml").exists() or (root / "requirements.txt").exists()):
        profile = {"projectType": "python", "commands": {**EMPTY_COMMANDS, "test": "python -m pytest" if (root / "tests").exists() else ""}}
    if profile is None:
        profile = {"projectType": "generic", "commands": dict(EMPTY_COMMANDS)}

    paths = {
        "frontend": [name for name in ("frontend", "web", "apps/web") if (root / name).exists()],
        "backend": [name for name in ("backend", "api", "src", "apps/api") if (root / name).exists()],
        "database": [name for name in ("migrations", "prisma", "database", "db") if (root / name).exists()],
        "deployment": [name for name in ("deploy", "deployment", "infra", "docker-compose.yml") if (root / name).exists()],
        "tests": [name for name in ("tests", "test", "e2e") if (root / name).exists()],
    }
    return {**profile, "paths": paths}
