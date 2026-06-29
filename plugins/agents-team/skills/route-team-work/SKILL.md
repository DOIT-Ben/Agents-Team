---
name: route-team-work
description: Use when an initialized Agents-Team Goal needs a deterministic engineering phase, role, provider, and parallelism decision
---

# Route Team Work

## Entry Gate

Read `AGENTS.md`, `.codex/team-collaboration.json`, the linked Goal Issue, current lifecycle labels, and the requested intent. Stop when the Goal contract is invalid or L2/L3 prerequisites cannot be read.

## Workflow

1. Validate the Goal contract using Protocol 2.0.
2. Reclassify the risk as L1, L2, or L3 and escalate when the repository paths or requested action require it.
3. Use `scripts/team_collaboration/routing.py` to select plan, build, debug, review, or ship.
4. Use `scripts/team_collaboration/providers.py` to prefer a compatible installed external Skill only when it is actually available; otherwise select the built-in Skill.
5. Load the selected contract from `references/roles/` and record allowed files, forbidden files, dependencies, and exit gates.
6. Allow parallel work only when tasks, files, contracts, and tests are all independent.

## Forbidden

- Do not implement business code while routing.
- Do not invent lifecycle state, available Skills, permissions, or evidence.
- Do not let an external Skill override the Goal, risk, boundary, approval, QA, or CI contract.
- Do not create nested role dispatch.

## Exit Gate

Return one phase, one Skill, one role, one provider, the risk with rationale, boundaries, prerequisites, exit gates, and an explicit parallelism decision.

## Evidence

Record the Issue number, lifecycle status, risk source, selected Skill and provider, role-contract path, allowed and forbidden files, and the four parallelism facts.
