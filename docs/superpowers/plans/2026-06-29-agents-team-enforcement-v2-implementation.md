# Agents-Team Enforcement Protocol 2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Agents-Team from drift-aware templates to a fail-closed, diagnosable Goal/PR enforcement system.

**Architecture:** Add pure Python contract, lifecycle, evidence, diagnostics, and doctor modules; render self-contained project validators and a GitHub Actions gate; keep dynamic status in GitHub while repository files contain only protocol and validators.

**Tech Stack:** Python 3 standard library, unittest, Markdown/YAML templates, GitHub Actions, Codex Plugin and Skill manifests.

---

### Task 1: Define diagnostics and contract parser

**Files:**
- Create: `plugins/agents-team/scripts/team_collaboration/diagnostics.py`
- Create: `plugins/agents-team/scripts/team_collaboration/contracts.py`
- Create: `plugins/agents-team/tests/test_diagnostics.py`
- Create: `plugins/agents-team/tests/test_contracts.py`

- [ ] Write failing tests for stable diagnostic JSON and required Issue/PR sections.
- [ ] Run `python3 -m unittest plugins/agents-team/tests/test_diagnostics.py plugins/agents-team/tests/test_contracts.py -v` and confirm missing-module failures.
- [ ] Implement `Finding`, Markdown section parsing, linked-Issue extraction, checklist validation, command evidence parsing, and L3 confirmation checks.
- [ ] Re-run focused tests and confirm all pass.

### Task 2: Implement lifecycle and evidence gates

**Files:**
- Create: `plugins/agents-team/scripts/team_collaboration/lifecycle.py`
- Create: `plugins/agents-team/scripts/team_collaboration/evidence.py`
- Create: `plugins/agents-team/tests/test_lifecycle.py`
- Create: `plugins/agents-team/tests/test_evidence.py`

- [ ] Write failing tests for legal transitions, skipped states, conflicting labels, failing exit codes, missing counts, unexpected skips and QA independence.
- [ ] Run focused tests and confirm RED failures.
- [ ] Implement explicit transition tables and fail-closed evidence validation.
- [ ] Re-run focused tests and confirm GREEN.

### Task 3: Add project Doctor

**Files:**
- Create: `plugins/agents-team/scripts/team_collaboration/doctor.py`
- Create: `plugins/agents-team/scripts/doctor_project.py`
- Create: `plugins/agents-team/tests/test_doctor.py`

- [ ] Write failing tests for healthy, warning and blocked repositories.
- [ ] Implement read-only checks and JSON output with exit codes 0, 2 and 1.
- [ ] Verify Doctor never modifies the repository.

### Task 4: Upgrade generated validators and CI

**Files:**
- Create: `plugins/agents-team/templates/project/validate_goal_contract.py`
- Create: `plugins/agents-team/templates/project/validate_pr_contract.py`
- Modify: `plugins/agents-team/templates/project/collaboration-gate.yml`
- Test: `plugins/agents-team/tests/test_generated_gates.py`

- [ ] Write fixture-driven failing tests for valid and invalid GitHub event payloads.
- [ ] Implement self-contained validators using only the Python standard library.
- [ ] Make GitHub API failure fail closed for L2/L3 with `AT-SYSTEM-*`.
- [ ] Emit JSON diagnostics and append a readable GitHub Job Summary.

### Task 5: Strengthen templates and runbook

**Files:**
- Modify: `plugins/agents-team/templates/project/team-goal.yml`
- Modify: `plugins/agents-team/templates/project/critical-goal.yml`
- Modify: `plugins/agents-team/templates/project/pull_request_template.md`
- Create: `plugins/agents-team/templates/project/team-failure.yml`
- Create: `plugins/agents-team/templates/project/team-runbook.md`
- Test: `plugins/agents-team/tests/test_templates.py`

- [ ] Write failing contract tests for rollback, failure evidence, exact test results, QA independence and root-cause fields.
- [ ] Update templates with unambiguous required fields and examples.
- [ ] Document failure codes, state recovery and escalation in the runbook.

### Task 6: Upgrade config and migration

**Files:**
- Modify: `plugins/agents-team/scripts/team_collaboration/__init__.py`
- Modify: `plugins/agents-team/scripts/team_collaboration/config.py`
- Modify: `plugins/agents-team/scripts/team_collaboration/initialize.py`
- Modify: `plugins/agents-team/templates/project/team-collaboration.schema.json`
- Modify: `plugins/agents-team/tests/test_config.py`
- Modify: `plugins/agents-team/tests/test_versioning.py`

- [ ] Write failing tests for enforcement configuration and 1.x migration.
- [ ] Bump Plugin to `0.2.0`, Protocol to `2.0.0`, schema to `2`.
- [ ] Add strict defaults, preserve timestamps and block upgrades on drift.
- [ ] Verify repeated upgrade is idempotent.

### Task 7: Align Skills and Hook behavior

**Files:**
- Modify: all four `plugins/agents-team/skills/*/SKILL.md`
- Modify: `plugins/agents-team/hooks/session_start.py`
- Modify: `plugins/agents-team/references/*.md`
- Modify: `plugins/agents-team/tests/test_skills.py`
- Modify: `plugins/agents-team/tests/test_hook.py`

- [ ] Add failing assertions for Doctor, diagnostic codes, lifecycle and fail-closed execution.
- [ ] Require execution and QA Skills to run deterministic contract gates before claims.
- [ ] Make SessionStart report healthy, warning, blocked or outdated without writing.

### Task 8: Add repository CI and release metadata

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `plugins/agents-team/.codex-plugin/plugin.json`
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Modify: `tools/build_distribution.py`
- Modify: `tools/verify_distribution.py`

- [ ] Add CI for unit tests, Plugin/Skill validation, compile and distribution E2E.
- [ ] Add homepage, repository and license metadata.
- [ ] Build `agents-team-0.2.0.zip` and document upgrade/install checks.

### Task 9: Full failure-injection and release verification

**Files:**
- Modify: fixtures and tests under `plugins/agents-team/tests/`

- [ ] Run the entire unit suite and record the exact test count.
- [ ] Run official Plugin and Skill validators.
- [ ] Compile all Python files.
- [ ] Build and unpack the distribution ZIP.
- [ ] Initialize disposable repositories, run Doctor, validate adapters, and exercise valid/invalid PR gates.
- [ ] Confirm the working tree contains only intended changes, then commit and publish to GitHub.

