---
name: initialize-team-collaboration
description: Use when a Git repository needs the reusable team collaboration mechanism initialized, adopted, or repaired
---

# Initialize Team Collaboration

## Rule

Never write project files before showing a dry-run preview and receiving 用户确认. Do not overwrite existing project guidance, GitHub templates, or CI.

硬规则：不得覆盖既有项目规则、非受控模板或业务 CI。

## Workflow

1. Read existing `AGENTS.md`, Git status, manifests, test commands, `.github`, risky paths, and remote metadata. Never read secret file contents.
2. Run:
   `python3 ../../scripts/initialize_project.py <repo>`
3. Report detected stack, commands, create/update lists, conflicts, and unknowns. Ask only for facts that cannot be detected reliably.
4. Stop on dirty worktrees, unmanaged target conflicts, missing Git, unknown required commands, or project-rule conflicts.
5. After explicit approval, run:
   `python3 ../../scripts/initialize_project.py <repo> --apply`
6. Validate with `python3 ../../scripts/validate_project.py <repo>`.
7. Deliver changes on a new branch and Draft PR. Never push the default branch directly.
8. Run the bootstrap gate before merge. Create the 开放 PR, then push one reviewed commit so the `synchronize` event validates the Issue and current-head evidence. Correct PR evidence through an `edited` event without changing the head SHA. Missing token or Issue access is blocking.

Initialization supports new projects and existing-project adoption. Existing `AGENTS.md` content outside the managed block must remain byte-for-byte intact. A repeated apply must be idempotent.

Read `../../references/core-protocol.md` and `../../references/migration-rules.md` when conflicts or legacy mechanisms are present.
