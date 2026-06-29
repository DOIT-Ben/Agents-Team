# Release Contract

Before production release record commit SHA, linked Issues/PRs, config/data changes, backup, rollback command, downtime, paid-provider cost, and production acceptance path.

Use exact states: local verified, CI passed, QA passed, staging passed, production deployed, production accepted, release complete. “Release complete” requires real production-path acceptance and a viable rollback.

Production core-path failure or P0 requires rollback. Never hot-edit production without committing the same change back to the repository.
