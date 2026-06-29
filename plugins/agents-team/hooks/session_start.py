#!/usr/bin/env python3
"""Read-only project mechanism detection for SessionStart."""

from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.validate import validate_project  # noqa: E402


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    config = root / ".codex" / "team-collaboration.json"
    if not config.is_file():
        print("当前项目尚未初始化团队协作机制。需要时可说：初始化团队协作机制。")
        return 0
    errors = validate_project(root)
    if errors:
        print("当前项目团队协作机制需要检查：" + "; ".join(errors))
    else:
        print("当前项目已启用团队协作机制。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
