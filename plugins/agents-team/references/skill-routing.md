# Skill Routing Contract

Protocol 2.0 is always authoritative. Routing selects how to execute a valid Goal; it cannot repair or bypass an invalid contract.

## Phase Mapping

| Lifecycle or intent | Phase | Builtin Skill | Role |
| --- | --- | --- | --- |
| `draft`, `ready`, planning intent | plan | `plan-team-goal` | `goal-planner` |
| `in-progress` | build | `build-team-goal` | `implementation-worker` |
| failure, error, bug, timeout | debug | `debug-team-goal` | `test-engineer` |
| `implemented`, `qa-pending` | review | `review-team-goal` | `code-reviewer` |
| `pass`, `mergeable` | ship | `ship-team-goal` | `independent-verifier` |

## Provider Selection

The `builtin` provider is the guaranteed fallback. A compatible `external` Skill may be selected only when it is installed and visible in the current session. External results must be converted into Protocol 2.0 evidence and remain subject to Goal, risk, boundary, QA, and CI gates.

## Decision Record

Every route records phase, Skill, provider, role, risk, status, allowed files, forbidden files, prerequisites, exit gates, and the four parallelism facts.
