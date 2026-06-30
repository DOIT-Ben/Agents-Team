---
name: manage-team-collaboration
description: Use when an initialized project mechanism needs checking, upgrading, repairing, removing, or its local runtime logs need viewing or deletion
---

# Manage Team Collaboration

## Operations

- 检查: `python3 ../../scripts/manage_project.py check <repo>`; read-only.
- 升级: preview first with `upgrade`; apply only after conflicts and version impact are approved.
- 修复: regenerate missing or damaged managed files without changing business rules.
- 移除: preview every deletion and AGENTS block change; require explicit confirmation before apply.
- 日志: `logs` is read-only; `delete-logs` previews first and requires `--apply` before deleting local runtime records.

## Rules

1. Start with `check` and read `.codex/team-collaboration.json`.
2. Never overwrite locally modified managed files. Present drift and ask whether to preserve, restore, or convert it into project configuration.
3. Patch and minor updates still use a Draft PR. Major protocol updates require a migration plan and user approval.
4. Updates may touch only managed files and the managed `AGENTS.md` block.
5. Removal preserves ADRs, Git history, Issues, PRs, and all non-managed project guidance.

Use `python3 ../../scripts/manage_project.py <check|repair|upgrade|remove|logs|delete-logs> <repo> [--apply]`. Read `../../references/migration-rules.md` before upgrades or legacy adoption and `../../references/runtime-feedback.md` before handling local records.
