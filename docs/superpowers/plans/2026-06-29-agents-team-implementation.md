# Agents-Team Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and package a reusable Codex plugin that safely initializes, executes, verifies, and maintains a GitHub-first team collaboration mechanism in arbitrary software repositories.

**Architecture:** A marketplace-backed plugin contains four concise Skills, deterministic Python standard-library scripts, immutable templates, a read-only SessionStart hook, and fixture-driven tests. Project initialization renders a self-contained adapter layer into a staged directory, validates it, and only then applies managed files and managed `AGENTS.md` blocks.

**Tech Stack:** Python 3 standard library, JSON/JSON Schema subset validation, unittest, Markdown/YAML templates, Codex plugin and Skill manifests.

---

### Task 1: Scaffold repository and plugin package

**Files:**
- Create: `.agents/plugins/marketplace.json`
- Create: `plugins/agents-team/.codex-plugin/plugin.json`
- Create: plugin `skills/`, `scripts/`, `references/`, `templates/`, `hooks/`, `tests/`

- [ ] Run the official plugin creator to scaffold a repo marketplace plugin.
- [ ] Run the official skill initializer for all four Skill folders.
- [ ] Validate the initial plugin structure and record the expected placeholder failures.
- [ ] Initialize a local Git repository on `feat/initial-plugin`.

### Task 2: Define failing configuration and rendering tests

**Files:**
- Create: `plugins/agents-team/tests/test_config.py`
- Create: `plugins/agents-team/tests/test_rendering.py`
- Create: `plugins/agents-team/tests/fixtures/`

- [ ] Write tests for valid/invalid config, required keys, semantic versions, and path containment.
- [ ] Write tests proving an existing `AGENTS.md` keeps all text outside the managed block.
- [ ] Write tests for idempotent repeated rendering and template required fields.
- [ ] Run tests and verify RED failures because implementation modules do not exist.

### Task 3: Implement configuration, inspection, and rendering core

**Files:**
- Create: `scripts/team_collaboration/config.py`
- Create: `scripts/team_collaboration/inspect.py`
- Create: `scripts/team_collaboration/render.py`
- Create: `scripts/team_collaboration/managed_block.py`

- [ ] Implement the minimum config loader and validator to pass config tests.
- [ ] Implement repository inspection without reading secret file contents.
- [ ] Implement managed-block replacement and staged rendering.
- [ ] Run focused tests to GREEN, then refactor without behavior changes.

### Task 4: Define and implement project templates

**Files:**
- Create: `templates/project/agents-managed-block.md`
- Create: `templates/project/team-collaboration.json`
- Create: `templates/project/team-collaboration.schema.json`
- Create: `templates/project/validate_team_collaboration.py`
- Create: `templates/project/team-goal.yml`
- Create: `templates/project/critical-goal.yml`
- Create: `templates/project/pull_request_template.md`
- Create: `templates/project/collaboration-gate.yml`
- Create: `templates/project/adr-readme.md`

- [ ] Write contract tests for Goal-first Issue forms, mandatory completion/gates/boundaries, PR QA/risk/rollback, and AGENTS markers.
- [ ] Run contract tests to verify RED against absent templates.
- [ ] Add minimal complete templates.
- [ ] Run contract tests to GREEN.

### Task 5: Build initialization CLI with safe apply

**Files:**
- Create: `scripts/initialize_project.py`
- Create: `tests/test_initialize.py`

- [ ] Write failing tests for dry-run, apply, dirty worktree stop, path traversal rejection, and idempotency.
- [ ] Implement CLI modes `initialize`, `adopt`, `repair`, and `upgrade` with dry-run default.
- [ ] Render to a temporary staged tree, validate, then atomically replace each managed target.
- [ ] Verify existing files and non-managed AGENTS content remain unchanged.

### Task 6: Build mechanism validation and version management

**Files:**
- Create: `scripts/validate_project.py`
- Create: `scripts/detect_version.py`
- Create: `scripts/manage_project.py`
- Create: `tests/test_validation.py`
- Create: `tests/test_versioning.py`

- [ ] Write failing tests for missing files, block drift, template drift, version mismatch, check/repair/upgrade/remove previews, and rollback metadata.
- [ ] Implement deterministic validators and version comparison.
- [ ] Implement managed-file hashes and non-destructive management previews.
- [ ] Run focused and full tests to GREEN.

### Task 7: Author four Skills and protocol references

**Files:**
- Modify: four `SKILL.md` files
- Create: `references/core-protocol.md`
- Create: `references/risk-classification.md`
- Create: `references/issue-contract.md`
- Create: `references/qa-contract.md`
- Create: `references/release-contract.md`
- Create: `references/migration-rules.md`

- [ ] Write baseline pressure scenarios that expose behavior without the Skill instructions.
- [ ] Author concise trigger-only frontmatter and workflow bodies for initialization, execution, verification, and management.
- [ ] Ensure the verification Skill is read-only and requires a fresh context.
- [ ] Run `quick_validate.py` for every Skill.

### Task 8: Add read-only SessionStart hook

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/session_start.py`
- Create: `tests/test_hook.py`

- [ ] Write failing tests proving the hook never writes files and only reports initialized, missing, damaged, or outdated state.
- [ ] Implement read-only detection.
- [ ] Run hook tests to GREEN.

### Task 9: Add cross-project fixture and security tests

**Files:**
- Create: fixture projects for Python, Next.js, .NET, monorepo, existing AGENTS/CI, legacy and dirty states.
- Create: `tests/test_fixtures.py`
- Create: `tests/test_security.py`

- [ ] Add fixture matrix assertions for scan, dry-run, apply, repeat apply, validate, and repair.
- [ ] Add negative tests for symlinks, traversal, secrets, conflicting blocks, and unsupported repository state.
- [ ] Run the complete unittest suite.

### Task 10: Package, validate, and document

**Files:**
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `LICENSE`
- Create: `docs/usage.md`
- Create: distribution ZIP

- [ ] Document installation, four Chinese trigger phrases, generated project files, risk levels, and limitations.
- [ ] Validate all Skills and the Plugin with official validators.
- [ ] Run full tests from a clean checkout.
- [ ] Run an end-to-end initialization into disposable fixture repositories and validate generated projects without Plugin access.
- [ ] Build the ZIP and verify its contents and checksum.
- [ ] Record the only external blocker: a new GitHub repository cannot be created because `gh` is unavailable in the environment.
