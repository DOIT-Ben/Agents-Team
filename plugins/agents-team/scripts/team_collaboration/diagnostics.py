"""Stable diagnostics shared by local, CI, and generated project gates."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable


CODE_PATTERN = re.compile(r"^AT-(?:CONTRACT|STATE|GATE|BOUNDARY|QA|DRIFT|SYSTEM)-\d{3}$")
SEVERITIES = {"info", "warning", "error"}


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    location: str
    message: str
    remediation: str
    evidence: str = ""

    def __post_init__(self) -> None:
        if not CODE_PATTERN.fullmatch(self.code):
            raise ValueError(f"invalid finding code: {self.code}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"invalid severity: {self.severity}")
        for field_name in ("location", "message", "remediation"):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} is required")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def summarize_findings(findings: Iterable[Finding]) -> dict[str, object]:
    items = list(findings)
    if any(item.severity == "error" for item in items):
        status = "blocked"
    elif items:
        status = "warning"
    else:
        status = "healthy"
    return {"status": status, "findings": [item.to_dict() for item in items]}
