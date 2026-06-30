#!/usr/bin/env python3
"""Build a deterministic marketplace ZIP for agents-team."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", "dist", "__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
INCLUDED_ROOTS = [
    ".agents", ".github", "plugins", "docs", "release", "tools",
    "README.md", "CHANGELOG.md", "NOTICE.md", "SECURITY.md", "LICENSE",
]


def iter_files():
    for item in INCLUDED_ROOTS:
        path = ROOT / item
        if path.is_file():
            yield path
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                relative = child.relative_to(ROOT)
                if child.is_file() and not (set(relative.parts) & EXCLUDED_PARTS) and child.suffix not in EXCLUDED_SUFFIXES:
                    yield child


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha1(path: Path) -> str:
    digest = hashlib.sha1(usedforsecurity=False)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest() -> dict:
    return json.loads((ROOT / "plugins/agents-team/.codex-plugin/plugin.json").read_text(encoding="utf-8"))


def source_commit() -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def write_sidecars(
    output: Path, version: str, channel: str, files: list[Path], test_evidence: dict
) -> None:
    checksum = sha256(output)
    Path(str(output) + ".sha256").write_text(f"{checksum}  {output.name}\n", encoding="utf-8")
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    commit = source_commit()
    try:
        archive_reference = output.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        archive_reference = output.name
    verification_code = hashlib.sha1(
        "".join(sorted(sha1(path) for path in files)).encode("ascii"), usedforsecurity=False
    ).hexdigest()
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"Agents-Team-{version}",
        "documentNamespace": f"https://github.com/DOIT-Ben/Agents-Team/spdx/{version}/{commit}",
        "creationInfo": {"created": created, "creators": ["Tool: Agents-Team build_distribution.py"]},
        "packages": [{
            "name": "agents-team",
            "SPDXID": "SPDXRef-Package-agents-team",
            "versionInfo": version,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": True,
            "packageVerificationCode": {"packageVerificationCodeValue": verification_code},
            "licenseConcluded": "NOASSERTION",
            "licenseDeclared": "NOASSERTION",
            "copyrightText": "NOASSERTION",
        }],
        "files": [
            {
                "fileName": path.relative_to(ROOT).as_posix(),
                "SPDXID": f"SPDXRef-File-{index}",
                "checksums": [{"algorithm": "SHA256", "checksumValue": sha256(path)}],
                "licenseConcluded": "NOASSERTION",
                "copyrightText": "NOASSERTION",
            }
            for index, path in enumerate(files, start=1)
        ],
        "relationships": [
            {
                "spdxElementId": "SPDXRef-DOCUMENT",
                "relationshipType": "DESCRIBES",
                "relatedSpdxElement": "SPDXRef-Package-agents-team",
            },
            *[
            {
                "spdxElementId": "SPDXRef-Package-agents-team",
                "relationshipType": "CONTAINS",
                "relatedSpdxElement": f"SPDXRef-File-{index}",
            }
            for index in range(1, len(files) + 1)
            ],
        ],
    }
    output.with_suffix(".spdx.json").write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    report = {
        "buildSchemaVersion": 1,
        "name": "agents-team",
        "version": version,
        "channel": channel,
        "sourceCommit": commit,
        "builtAt": created,
        "archive": output.name,
        "sha256": checksum,
        "protocolVersion": "2.0.0",
        "feedbackSchemaVersion": 1,
        "testEvidence": test_evidence,
        "verificationCommands": [
            "python -m unittest discover -s plugins/agents-team/tests -v",
            f"python tools/verify_distribution.py {archive_reference}",
        ],
    }
    output.with_suffix(".build.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Codex plugin marketplace archive.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--channel", choices=["internal", "beta", "stable"])
    parser.add_argument("--tag")
    parser.add_argument("--test-evidence", type=Path)
    args = parser.parse_args()
    plugin = manifest()
    version = plugin["version"]
    inferred = "beta" if "-beta." in version else "internal" if "-internal." in version else "stable"
    channel = args.channel or inferred
    if channel != inferred:
        raise SystemExit(f"release channel {channel} does not match plugin version {version}")
    if args.tag and args.tag != f"v{version}":
        raise SystemExit(f"release tag {args.tag} does not match plugin version {version}")
    if args.test_evidence is None or not args.test_evidence.is_file():
        raise SystemExit("a machine-readable --test-evidence file is required")
    try:
        test_evidence = json.loads(args.test_evidence.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"cannot read test evidence: {exc}") from exc
    if (
        test_evidence.get("status") != "passed"
        or test_evidence.get("failed") != 0
        or test_evidence.get("errors", 0) != 0
        or not test_evidence.get("command")
    ):
        raise SystemExit("test evidence must record a successful command with zero failures and errors")
    output = args.output or ROOT / f"dist/agents-team-{version}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    files = list(iter_files())
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(2026, 6, 29, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())
    write_sidecars(output, version, channel, files, test_evidence)
    print(json.dumps({
        "archive": str(output),
        "checksum": str(Path(str(output) + ".sha256")),
        "sbom": str(output.with_suffix(".spdx.json")),
        "buildReport": str(output.with_suffix(".build.json")),
        "version": version,
        "channel": channel,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
