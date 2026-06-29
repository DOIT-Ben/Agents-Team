"""Semantic version comparison for mechanism compatibility checks."""

from __future__ import annotations

import re


SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:-[0-9A-Za-z.-]+)?$")


def _parts(version: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid semantic version: {version}")
    return tuple(int(value) for value in match.groups())  # type: ignore[return-value]


def compare_versions(left: str, right: str) -> int:
    left_parts = _parts(left)
    right_parts = _parts(right)
    return (left_parts > right_parts) - (left_parts < right_parts)
