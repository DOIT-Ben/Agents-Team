#!/usr/bin/env python3
"""Print installed and available mechanism versions."""

import argparse
import json
from pathlib import Path

from team_collaboration import PLUGIN_VERSION, PROTOCOL_VERSION
from team_collaboration.config import ConfigError, load_config
from team_collaboration.versioning import compare_versions


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect team collaboration mechanism versions.")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    try:
        config = load_config(args.project / ".codex" / "team-collaboration.json")
    except ConfigError as exc:
        print(json.dumps({"status": "missing-or-invalid", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    installed = config["mechanism"]["protocolVersion"]
    print(json.dumps({
        "status": "current" if compare_versions(installed, PROTOCOL_VERSION) == 0 else "upgrade-available",
        "installedProtocolVersion": installed,
        "availableProtocolVersion": PROTOCOL_VERSION,
        "pluginVersion": PLUGIN_VERSION,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
