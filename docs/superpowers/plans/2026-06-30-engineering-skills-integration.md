# Engineering Skills Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a self-contained engineering lifecycle, deterministic routing, explicit worker-role contracts, and optional external-skill compatibility without weakening Agents-Team Protocol 2.0 governance.

**Architecture:** Protocol 2.0 remains the only contract, evidence, lifecycle, diagnostics, and fail-closed layer. A deterministic router selects one of six engineering workflow skills and a role contract; `execute-team-goal` remains the main orchestrator. Codex plugins do not auto-discover an `agents/` directory, so role definitions live under `references/roles/` and are explicitly injected into worker tasks.

**Tech Stack:** Python 3 standard library, `unittest`, Markdown Agent Skills, Codex plugin manifest, GitHub Actions, deterministic ZIP packaging.

---

### Task 1: Stabilize the Existing Protocol 2.0 Baseline

**Files:**
- Modify: `plugins/agents-team/scripts/team_collaboration/__init__.py`
- Modify: `plugins/agents-team/scripts/team_collaboration/config.py`
- Modify: `plugins/agents-team/scripts/team_collaboration/initialize.py`
- Modify: `plugins/agents-team/templates/project/team-collaboration.schema.json`
- Verify existing: `plugins/agents-team/scripts/team_collaboration/contracts.py`
- Verify existing: `plugins/agents-team/scripts/team_collaboration/evidence.py`
- Verify existing: `plugins/agents-team/scripts/team_collaboration/lifecycle.py`
- Verify existing: `plugins/agents-team/scripts/team_collaboration/diagnostics.py`
- Verify existing: `plugins/agents-team/scripts/team_collaboration/doctor.py`
- Test: `plugins/agents-team/tests/test_config.py`
- Test: `plugins/agents-team/tests/test_versioning.py`
- Test: `plugins/agents-team/tests/test_contracts.py`
- Test: `plugins/agents-team/tests/test_evidence.py`
- Test: `plugins/agents-team/tests/test_lifecycle.py`
- Test: `plugins/agents-team/tests/test_diagnostics.py`
- Test: `plugins/agents-team/tests/test_doctor.py`

- [ ] **Step 1: Run the existing Protocol 2.0 tests and capture the RED baseline**

Run:

```bash
python3 -m unittest \
  tests.test_config tests.test_versioning tests.test_contracts \
  tests.test_evidence tests.test_lifecycle tests.test_diagnostics tests.test_doctor -v
```

Expected: FAIL because constants, generated configuration, schema, or migration still use Protocol 1.0 fields.

- [ ] **Step 2: Update protocol constants**

Use:

```python
PLUGIN_ID = "agents-team"
PLUGIN_VERSION = "0.2.0"
PROTOCOL_VERSION = "2.0.0"
CONFIG_SCHEMA_VERSION = 2
```

- [ ] **Step 3: Make enforcement configuration mandatory and validated**

Add `enforcement` to `required_sections` and validate this exact contract:

```python
mode = enforcement.get("mode")
if mode not in {"strict", "advisory"}:
    errors.append("enforcement.mode must be strict or advisory")

fail_closed = enforcement.get("failClosedRisks")
if not isinstance(fail_closed, list) or any(value not in {"L1", "L2", "L3"} for value in fail_closed):
    errors.append("enforcement.failClosedRisks must contain only L1, L2, L3")
```

- [ ] **Step 4: Generate strict Protocol 2.0 defaults**

Add to `_build_config`:

```python
"enforcement": {
    "mode": "strict",
    "failClosedRisks": ["L2", "L3"],
    "requireLinkedIssue": {"L1": False, "L2": True, "L3": True},
    "requireIndependentQA": {"L1": False, "L2": True, "L3": True},
    "requireFailureRecord": True,
},
```

Update the JSON Schema required list to include `enforcement`.

- [ ] **Step 5: Run the focused tests until GREEN**

Run the Step 1 command again.

Expected: all focused Protocol 2.0 tests PASS.

- [ ] **Step 6: Run the complete plugin suite**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: all tests PASS with zero failures.

- [ ] **Step 7: Commit only the Protocol 2.0 baseline files**

```bash
git add plugins/agents-team/scripts plugins/agents-team/templates/project/team-collaboration.schema.json plugins/agents-team/tests
git commit -m "feat: enforce collaboration protocol 2"
```

### Task 2: Add Deterministic Engineering Work Routing

**Files:**
- Create: `plugins/agents-team/scripts/team_collaboration/routing.py`
- Create: `plugins/agents-team/tests/test_routing.py`

- [ ] **Step 1: Write failing routing tests**

```python
import unittest

from team_collaboration.routing import ParallelFacts, route_work


class RoutingTests(unittest.TestCase):
    def test_ready_goal_routes_to_planning(self):
        decision = route_work(intent="implement upload", status="ready", risk="L2")
        self.assertEqual(decision.skill, "plan-team-goal")
        self.assertEqual(decision.role, "goal-planner")

    def test_failure_intent_routes_to_debugging(self):
        decision = route_work(intent="tests fail with timeout", status="in-progress", risk="L2")
        self.assertEqual(decision.skill, "debug-team-goal")
        self.assertEqual(decision.role, "test-engineer")

    def test_parallelism_requires_every_fact(self):
        facts = ParallelFacts(True, True, True, False)
        decision = route_work(intent="implement", status="in-progress", risk="L2", parallel=facts)
        self.assertFalse(decision.can_parallel)
```

- [ ] **Step 2: Run tests to verify RED**

```bash
python3 -m unittest tests.test_routing -v
```

Expected: ERROR because `team_collaboration.routing` does not exist.

- [ ] **Step 3: Implement the minimal router**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ParallelFacts:
    independent_tasks: bool
    disjoint_files: bool
    stable_contracts: bool
    independent_tests: bool

    def allowed(self) -> bool:
        return all((self.independent_tasks, self.disjoint_files, self.stable_contracts, self.independent_tests))


@dataclass(frozen=True)
class RouteDecision:
    phase: str
    skill: str
    role: str
    risk: str
    can_parallel: bool


ROUTES = {
    "plan": ("plan-team-goal", "goal-planner"),
    "build": ("build-team-goal", "implementation-worker"),
    "debug": ("debug-team-goal", "test-engineer"),
    "review": ("review-team-goal", "code-reviewer"),
    "ship": ("ship-team-goal", "independent-verifier"),
}
```

`route_work` must reject unknown risks, prefer explicit failure/debug intent, and otherwise map lifecycle states as follows:

```python
STATE_PHASE = {
    "draft": "plan",
    "ready": "plan",
    "in-progress": "build",
    "implemented": "review",
    "qa-pending": "review",
    "pass": "ship",
    "mergeable": "ship",
}
```

- [ ] **Step 4: Run focused and full tests**

```bash
python3 -m unittest tests.test_routing -v
python3 -m unittest discover -s tests -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/agents-team/scripts/team_collaboration/routing.py plugins/agents-team/tests/test_routing.py
git commit -m "feat: add deterministic work routing"
```

### Task 3: Add Optional External Skill Provider Selection

**Files:**
- Create: `plugins/agents-team/scripts/team_collaboration/providers.py`
- Create: `plugins/agents-team/tests/test_providers.py`

- [ ] **Step 1: Write failing provider tests**

```python
import unittest

from team_collaboration.providers import select_provider


class ProviderTests(unittest.TestCase):
    def test_builtin_provider_is_default(self):
        result = select_provider("plan", available_skills=set())
        self.assertEqual(result.provider, "builtin")
        self.assertEqual(result.skill, "plan-team-goal")

    def test_compatible_external_skill_can_be_selected(self):
        result = select_provider("plan", available_skills={"planning-and-task-breakdown"})
        self.assertEqual(result.provider, "external")
        self.assertEqual(result.skill, "planning-and-task-breakdown")
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_providers -v
```

Expected: ERROR because the provider module does not exist.

- [ ] **Step 3: Implement the provider mapping**

```python
BUILTIN = {
    "plan": "plan-team-goal",
    "build": "build-team-goal",
    "debug": "debug-team-goal",
    "review": "review-team-goal",
    "ship": "ship-team-goal",
}

EXTERNAL = {
    "plan": "planning-and-task-breakdown",
    "build": "incremental-implementation",
    "debug": "debugging-and-error-recovery",
    "review": "code-review-and-quality",
    "ship": "shipping-and-launch",
}
```

Return a frozen `ProviderDecision(provider, skill, phase)`. Unknown phases must raise `ValueError`. External skills are optional and never downloaded by this module.

- [ ] **Step 4: Run focused and full tests, then commit**

```bash
python3 -m unittest tests.test_providers -v
python3 -m unittest discover -s tests -v
git add plugins/agents-team/scripts/team_collaboration/providers.py plugins/agents-team/tests/test_providers.py
git commit -m "feat: add optional skill provider selection"
```

### Task 4: Add Executable Role Contracts

**Files:**
- Create: `plugins/agents-team/references/roles/goal-planner.md`
- Create: `plugins/agents-team/references/roles/implementation-worker.md`
- Create: `plugins/agents-team/references/roles/test-engineer.md`
- Create: `plugins/agents-team/references/roles/code-reviewer.md`
- Create: `plugins/agents-team/references/roles/security-auditor.md`
- Create: `plugins/agents-team/references/roles/independent-verifier.md`
- Create: `plugins/agents-team/scripts/team_collaboration/roles.py`
- Create: `plugins/agents-team/tests/test_roles.py`

- [ ] **Step 1: Write failing role loader tests**

```python
import unittest

from team_collaboration.roles import compose_role_prompt, load_role_contract


class RoleTests(unittest.TestCase):
    def test_role_contract_contains_required_sections(self):
        text = load_role_contract(PLUGIN_ROOT, "goal-planner")
        for heading in ("## Responsibility", "## Allowed", "## Forbidden", "## Output"):
            self.assertIn(heading, text)

    def test_worker_prompt_includes_file_boundaries(self):
        prompt = compose_role_prompt(
            PLUGIN_ROOT,
            "implementation-worker",
            issue="Goal: upload",
            allowed_files=["src/upload.py"],
            forbidden_files=["src/auth.py"],
        )
        self.assertIn("src/upload.py", prompt)
        self.assertIn("src/auth.py", prompt)
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_roles -v
```

Expected: ERROR because role contracts and loader do not exist.

- [ ] **Step 3: Add the safe role loader**

```python
ROLE_NAMES = {
    "goal-planner",
    "implementation-worker",
    "test-engineer",
    "code-reviewer",
    "security-auditor",
    "independent-verifier",
}


def load_role_contract(plugin_root: Path, role: str) -> str:
    if role not in ROLE_NAMES:
        raise ValueError(f"unknown role: {role}")
    return (plugin_root / "references" / "roles" / f"{role}.md").read_text(encoding="utf-8")
```

`compose_role_prompt` must append the Goal contract plus explicit allowed and forbidden paths. It must not execute commands or mutate files.

- [ ] **Step 4: Write all six contracts using the same four headings**

Each file must define one responsibility, exact permissions, explicit prohibitions, and a structured output. `independent-verifier.md` must state that it cannot participate in implementation and can return only `PASS`, `FAIL`, or `BLOCKED` with findings.

- [ ] **Step 5: Run tests and commit**

```bash
python3 -m unittest tests.test_roles -v
python3 -m unittest discover -s tests -v
git add plugins/agents-team/references/roles plugins/agents-team/scripts/team_collaboration/roles.py plugins/agents-team/tests/test_roles.py
git commit -m "feat: add explicit worker role contracts"
```

### Task 5: Add the Six Engineering Workflow Skills

**Files:**
- Create: `plugins/agents-team/skills/route-team-work/SKILL.md`
- Create: `plugins/agents-team/skills/route-team-work/agents/openai.yaml`
- Create: `plugins/agents-team/skills/plan-team-goal/SKILL.md`
- Create: `plugins/agents-team/skills/plan-team-goal/agents/openai.yaml`
- Create: `plugins/agents-team/skills/build-team-goal/SKILL.md`
- Create: `plugins/agents-team/skills/build-team-goal/agents/openai.yaml`
- Create: `plugins/agents-team/skills/debug-team-goal/SKILL.md`
- Create: `plugins/agents-team/skills/debug-team-goal/agents/openai.yaml`
- Create: `plugins/agents-team/skills/review-team-goal/SKILL.md`
- Create: `plugins/agents-team/skills/review-team-goal/agents/openai.yaml`
- Create: `plugins/agents-team/skills/ship-team-goal/SKILL.md`
- Create: `plugins/agents-team/skills/ship-team-goal/agents/openai.yaml`
- Modify: `plugins/agents-team/tests/test_skills.py`

- [ ] **Step 1: Extend skill contract tests first**

Require every new Skill to contain:

```python
for heading in ["## Entry Gate", "## Workflow", "## Forbidden", "## Exit Gate", "## Evidence"]:
    self.assertIn(heading, text, path.as_posix())
```

Also assert every description starts with `Use when ` and every `openai.yaml` exists.

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_skills -v
```

Expected: FAIL because the six skills are absent.

- [ ] **Step 3: Create the six Skill files**

Every Skill must enforce Protocol 2.0 before its local workflow. Required core behavior:

| Skill | Required workflow |
| --- | --- |
| `route-team-work` | Read config and Issue, call deterministic router, record phase/role/provider/boundaries |
| `plan-team-goal` | Produce small dependency-ordered tasks with acceptance evidence and no code changes |
| `build-team-goal` | Test-first incremental changes, inspect diff, never self-approve |
| `debug-team-goal` | Reproduce, localize, reduce, fix, add regression test, preserve failure record |
| `review-team-goal` | Findings first; correctness, tests, security, boundary and rollback checks |
| `ship-team-goal` | Verify current head CI, QA independence, risks and rollback before MERGEABLE |

- [ ] **Step 4: Add concise `openai.yaml` metadata**

Use this shape for each Skill:

```yaml
interface:
  display_name: "规划团队目标"
  short_description: "Break a Goal into bounded, verifiable tasks"
  default_prompt: "按照 Agents-Team 协议规划当前 Goal，不修改业务代码。"
```

- [ ] **Step 5: Run tests and commit**

```bash
python3 -m unittest tests.test_skills -v
python3 -m unittest discover -s tests -v
git add plugins/agents-team/skills plugins/agents-team/tests/test_skills.py
git commit -m "feat: add engineering lifecycle skills"
```

### Task 6: Wire Routing and Roles into Goal Execution

**Files:**
- Modify: `plugins/agents-team/skills/execute-team-goal/SKILL.md`
- Create: `plugins/agents-team/references/skill-routing.md`
- Create: `plugins/agents-team/references/orchestration-rules.md`
- Modify: `plugins/agents-team/tests/test_skills.py`
- Create: `plugins/agents-team/tests/test_orchestration_contract.py`

- [ ] **Step 1: Write failing orchestration contract tests**

```python
import unittest


class OrchestrationContractTests(unittest.TestCase):
    def test_execute_skill_uses_router_and_role_contracts(self):
        text = EXECUTE_SKILL.read_text(encoding="utf-8")
        for phrase in ["route-team-work", "references/roles", "allowed files", "forbidden files"]:
            self.assertIn(phrase, text)

    def test_nested_role_dispatch_is_forbidden(self):
        text = ORCHESTRATION_RULES.read_text(encoding="utf-8")
        self.assertIn("角色不得调用其他角色", text)
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_orchestration_contract -v
```

Expected: FAIL because the router and role contracts are not referenced.

- [ ] **Step 3: Update `execute-team-goal`**

The workflow must become:

```text
validate Goal contract
-> classify L1/L2/L3
-> run route-team-work
-> select built-in or compatible provider
-> load the selected role contract
-> inject allowed/forbidden files
-> execute and integrate
-> independent verification for L2/L3
-> ship gate
```

Explicitly state that only the main Codex can integrate results, role workers cannot spawn roles, and implementation workers can claim only code-level completion.

- [ ] **Step 4: Run focused and full tests, then commit**

```bash
python3 -m unittest tests.test_orchestration_contract tests.test_skills -v
python3 -m unittest discover -s tests -v
git add plugins/agents-team/skills/execute-team-goal plugins/agents-team/references/skill-routing.md plugins/agents-team/references/orchestration-rules.md plugins/agents-team/tests
git commit -m "feat: integrate engineering workflow orchestration"
```

### Task 7: Publish Attribution, Documentation, and Version 0.3.0

**Files:**
- Create: `NOTICE.md`
- Modify: `plugins/agents-team/.codex-plugin/plugin.json`
- Modify: `.agents/plugins/marketplace.json`
- Modify: `README.md`
- Modify: `docs/usage.md`
- Modify: `CHANGELOG.md`
- Modify: `tools/build_distribution.py`
- Modify: repository tests that assert versions or package contents

- [ ] **Step 1: Add failing metadata and package tests**

Assert:

```python
self.assertEqual(manifest["version"], "0.3.0")
self.assertIn("Engineering lifecycle", manifest["interface"]["capabilities"])
self.assertTrue((ROOT / "NOTICE.md").is_file())
```

- [ ] **Step 2: Verify RED**

```bash
python3 -m unittest tests.test_package tests.test_distribution -v
```

Expected: FAIL because version `0.3.0`, NOTICE, and new package content are absent.

- [ ] **Step 3: Update version and public metadata**

Set Plugin version to `0.3.0`, retain Protocol `2.0.0` and schema `2`, add `Engineering lifecycle` and `Deterministic routing` capabilities, and update the default package name to `dist/agents-team-0.3.0.zip`.

- [ ] **Step 4: Add attribution and usage documentation**

`NOTICE.md` must identify `addyosmani/agent-skills`, its MIT license, and exactly which design ideas were referenced. README and usage docs must explain that Agents-Team remains independent and external skills are optional providers.

- [ ] **Step 5: Run tests and commit**

```bash
python3 -m unittest tests.test_package tests.test_distribution -v
python3 -m unittest discover -s tests -v
git add NOTICE.md README.md CHANGELOG.md docs/usage.md plugins/agents-team/.codex-plugin/plugin.json .agents/plugins/marketplace.json tools plugins/agents-team/tests
git commit -m "docs: publish engineering workflow integration"
```

### Task 8: Verify Distribution and Run a Real L2 Trial

**Files:**
- Create: `plugins/agents-team/tests/test_engineering_workflow.py`
- Modify if required: `tools/verify_distribution.py`
- Produce: `dist/agents-team-0.3.0.zip`
- External trial target: `DOIT-Ben/skill-usage` on an isolated branch

- [ ] **Step 1: Add an end-to-end local lifecycle test**

The test must initialize a temporary Git repository, load Protocol 2.0, route a `status:ready` L2 Goal to planning, validate one deliberately incomplete evidence record as blocked, then validate corrected evidence as healthy.

- [ ] **Step 2: Verify RED, implement only required integration glue, then verify GREEN**

```bash
python3 -m unittest tests.test_engineering_workflow -v
```

Expected first run: FAIL because the workflow integration is incomplete. Expected final run: PASS.

- [ ] **Step 3: Run fresh full verification**

```bash
cd plugins/agents-team
python3 -m unittest discover -s tests -v
cd ../..
python3 tools/build_distribution.py --output dist/agents-team-0.3.0.zip
python3 tools/verify_distribution.py dist/agents-team-0.3.0.zip
```

Expected: zero test failures and distribution status `valid`.

- [ ] **Step 4: Perform the real external trial**

On a new branch in `DOIT-Ben/skill-usage`:

1. Install or materialize the built `agents-team` package externally.
2. Initialize Protocol 2.0 with dry-run first.
3. Create a small documentation-focused L2 Goal Issue.
4. Open a PR with missing evidence and confirm Collaboration Gate fails.
5. Record the exact command, exit code, counts, commit SHA, and independent QA.
6. Confirm the same Gate passes for the corrected current head commit.

- [ ] **Step 5: Record the trial evidence**

Add a dated audit under `docs/superpowers/audits/` containing repository, branch, Issue, PR, failing run, passing run, observed defects, and remediation. Do not claim plug-and-play readiness without both runs.

- [ ] **Step 6: Commit trial harness and evidence**

```bash
git add plugins/agents-team/tests/test_engineering_workflow.py tools/verify_distribution.py docs/superpowers/audits
git commit -m "test: verify engineering workflow end to end"
```

### Final Verification

- [ ] Confirm the design correction removed unsupported `agents/` packaging.
- [ ] Confirm all six roles are loaded through `references/roles/`.
- [ ] Confirm no external Skill is required for installation.
- [ ] Confirm Protocol 2.0 remains the only evidence and lifecycle model.
- [ ] Confirm the current PR head has a successful full test and distribution run.
- [ ] Confirm the real external trial includes one observed failure and one corrected pass.
- [ ] Review `git diff master...HEAD` for unrelated changes and accidental generated files.
