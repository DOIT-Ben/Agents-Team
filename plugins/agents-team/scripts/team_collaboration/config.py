"""Load and validate the project adapter configuration."""

from __future__ import annotations

import json
import re
from pathlib import Path, PureWindowsPath
from typing import Any


SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")


class ConfigError(ValueError):
    """Raised when a project adapter configuration is invalid."""


def _unsafe_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    return (
        not value
        or value.startswith(("/", "\\"))
        or bool(PureWindowsPath(value).drive)
        or ".." in parts
        or "\x00" in value
    )


def validate_config(config: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return ["configuration must be an object"]

    required_sections = ["mechanism", "project", "commands", "paths", "risk", "overrides", "enforcement", "managedFiles"]
    for section in required_sections:
        if section not in config:
            errors.append(f"{section} is required")

    mechanism = config.get("mechanism")
    if isinstance(mechanism, dict):
        if not mechanism.get("id"):
            errors.append("mechanism.id is required")
        for field in ("pluginVersion", "protocolVersion"):
            value = mechanism.get(field)
            if not isinstance(value, str) or not SEMVER.fullmatch(value):
                errors.append(f"mechanism.{field} must be semantic version")
        if not isinstance(mechanism.get("configSchemaVersion"), int):
            errors.append("mechanism.configSchemaVersion must be integer")

    project = config.get("project")
    if isinstance(project, dict):
        for field in ("name", "type", "defaultBranch"):
            if not isinstance(project.get(field), str) or not project[field].strip():
                errors.append(f"project.{field} is required")

    for section_name in ("paths", "risk"):
        section = config.get(section_name)
        if not isinstance(section, dict):
            if section_name in config:
                errors.append(f"{section_name} must be an object")
            continue
        for key, values in section.items():
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                errors.append(f"{section_name}.{key} must be a list of strings")
                continue
            for value in values:
                if _unsafe_path(value):
                    errors.append(f"{section_name}.{key} contains unsafe path: {value}")

    if "managedFiles" in config and not isinstance(config["managedFiles"], dict):
        errors.append("managedFiles must be an object")

    enforcement = config.get("enforcement")
    if isinstance(enforcement, dict):
        if enforcement.get("mode") not in {"strict", "advisory"}:
            errors.append("enforcement.mode must be strict or advisory")
        fail_closed = enforcement.get("failClosedRisks")
        if (
            not isinstance(fail_closed, list)
            or any(value not in {"L1", "L2", "L3"} for value in fail_closed)
        ):
            errors.append("enforcement.failClosedRisks must contain only L1, L2, L3")

        for field in ("requireLinkedIssue", "requireIndependentQA"):
            values = enforcement.get(field)
            if (
                not isinstance(values, dict)
                or set(values) != {"L1", "L2", "L3"}
                or any(not isinstance(value, bool) for value in values.values())
            ):
                errors.append(f"enforcement.{field} must map L1, L2 and L3 to booleans")

        if not isinstance(enforcement.get("requireFailureRecord"), bool):
            errors.append("enforcement.requireFailureRecord must be boolean")

        required_check_names = enforcement.get("requiredCheckNames", [])
        if (
            not isinstance(required_check_names, list)
            or any(not isinstance(value, str) or not value.strip() for value in required_check_names)
        ):
            errors.append("enforcement.requiredCheckNames must be a list of non-empty strings")

    return errors


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot load configuration: {exc}") from exc
    errors = validate_config(data)
    if errors:
        raise ConfigError("; ".join(errors))
    return data
