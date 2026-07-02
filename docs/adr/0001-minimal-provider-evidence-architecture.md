# ADR 0001: Minimal Provider And Evidence Architecture

## Status

Accepted for Protocol 2.x near-term work.

## Context

Agents-Team already has two small runtime concepts:

- provider selection chooses a built-in or compatible external skill for a workflow phase.
- evidence validation checks gate records and independent QA records before a goal can be considered healthy.

The next issues need stronger evidence sources and lifecycle checks, but a broad Provider Registry or Evidence Bus would be too large for a reviewable Protocol 2.x change.

## Decision

Use a minimal provider/capability registry concept:

- A provider is a named source of a capability for one workflow phase: `plan`, `build`, `debug`, `review`, or `ship`.
- A capability record has `provider`, `skill`, `phase`, and optional compatibility notes.
- Built-in providers remain the fallback and cannot be disabled by unrelated external skills.
- External providers are selected only when their skill is explicitly available and phase-compatible.

Use one shared evidence object shape for current gates:

```yaml
gate: test:unit | package:verify | github-actions | qa
command: exact command or source query
exitCode: integer
passed: integer
failed: integer
skipped: integer
skipReason: required when skipped > 0
timestamp: ISO 8601 UTC timestamp
commitSha: exact current PR head SHA
artifact: inspectable local path or HTTPS URL
```

Independent QA evidence adds:

```yaml
independent: true
verifier: actor or system that performed QA
implementationContext: implementation session, run, or actor context
qaContext: separate QA session, run, or actor context
verdict: PASS | FAIL | BLOCKED
commitSha: exact current PR head SHA verified by QA
artifact: inspectable evidence URL or path
```

GitHub Actions is a valid evidence source when its run is bound to the current PR head SHA. PR body evidence is an index and human-readable summary; it must not become the only source of truth for future GitHub Checks work.

## Deferred

- Full Provider Registry implementation.
- Evidence Bus or event store.
- External identity provider integration.
- Protocol 3.0 rewrite.
- Automatic GitHub Checks source-of-truth enforcement.

## Follow-Up Issues

- #19: read GitHub Checks / workflow runs as the source of truth for test evidence.
- #20: require an explicit verify lifecycle before PASS.
- #21: require a verifiable L3 approval event.
- #22: enforce worker diff boundaries.
- #23: require risk-path classification before L2/L3 gates.
- #24: unify contract validation semantics after #14 clarified QA evidence boundaries.

## Consequences

Near-term implementation should extend the current small validators and generated gates instead of introducing a new bus. Any future provider or evidence feature must preserve current-head SHA binding, separate QA context, and inspectable artifacts.
