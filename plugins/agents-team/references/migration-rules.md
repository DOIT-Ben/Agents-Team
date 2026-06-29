# Migration Rules

- Project protocol versions are pinned independently from the installed Plugin version.
- Patch changes do not alter semantics; minor changes are additive; major changes need an approved migration plan.
- Always preview. Update only managed files and managed blocks.
- Managed hash drift blocks overwrite.
- Preserve custom project guidance and unsupported existing CI/templates.
- Repeated migration must be idempotent.
- Roll back by reverting the upgrade PR and restoring repository settings listed in the rollback plan.
- Legacy dynamic ledgers should be migrated to GitHub Issues/PRs, then removed from active guidance; Git history remains the archive.
