# Orchestration Rules

## Authority

The main Codex is the only orchestrator and integrator. Workers return bounded results; they do not own the Goal, lifecycle, final evidence, or merge decision.

## Flat Dispatch

- 角色不得调用其他角色。
- Workers cannot create nested teams or delegate their assigned responsibility.
- The main Codex may dispatch multiple workers only when tasks, files, contracts, and tests are independent.
- The main Codex must inspect every result and the integrated diff instead of trusting a completion claim.

## Role Injection

Codex plugins do not auto-discover a root `agents/` directory. Before dispatch, load one contract from `references/roles/` and include it with the Goal, allowed files, forbidden files, dependencies, verification, and expected output.

## Independence

An implementation participant cannot issue independent QA. L2/L3 verification uses a fresh context that receives the Goal, final artifact, and evidence without the implementation reasoning narrative.

## Failure

Any ambiguity, boundary conflict, missing authority, unavailable required environment, or failing gate returns FAIL or BLOCKED to the main Codex. It must not be silently converted into success.
