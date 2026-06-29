# Agents-Team Enforcement Protocol 2.0 Design

状态：Approved by direct implementation request
日期：2026-06-29
目标：把现有协作规范升级为可检查、可阻断、可追踪根因的执行系统

## 1. 问题定义

协议 1.0 能初始化模板并检测受控文件漂移，但仍存在五个执行缺口：

1. Issue 字段只靠 Agent 阅读，没有确定性合同校验。
2. PR 是否包含完整证据、QA 结论和回滚方式无法机械判断。
3. 任务状态没有合法状态机，可能跳过设计确认、测试或独立 QA。
4. 失败信息是自由文本，不能稳定定位哪一关、哪条规则和哪份证据失败。
5. CI 只检查项目适配层本身，没有检查当前 PR 的任务合同和交付证据。

## 2. 设计原则

- GitHub Issue 是 Goal 合同真源，PR 是实现与证据真源。
- 仓库不保存当前任务状态，只保存协议、验证器和受控模板。
- L2/L3 默认 fail-closed；任何关键字段、证据或独立 QA 缺失都阻断。
- L1 保持轻量，但仍要求 PR 说明边界和验证证据。
- 所有阻断返回稳定失败码、字段、原因、修复动作和证据位置。
- 叙述不能替代证据，勾选框不能替代命令结果。
- 现有项目文件不得被静默覆盖，升级必须检测漂移并先预览。

## 3. Goal 合同

L2/L3 Issue 必须包含以下有序区块：

1. `Goal`
2. `必须完成`
3. `验收门禁`
4. `任务边界`
5. `风险等级`
6. `依赖与阻塞条件`
7. `失败处理与回滚`

强制语义：

- Goal 不能是空话或实现手段，必须包含可观察结果。
- 必须完成至少包含一个任务项。
- 验收门禁至少包含一个可执行命令或明确的人工行为验收。
- 任务边界必须明确禁止事项；`无` 不合格。
- L3 必须包含用户确认记录、成本或不可逆影响以及回滚方式。
- Issue 未达到 READY 合同标准时，执行 Skill 必须停止。

## 4. PR 证据合同

PR 必须包含：

- 关联 Issue。
- 风险等级。
- 实际改动。
- 范围偏差。
- 必须完成项逐项证据。
- 测试命令、退出码、通过/失败/跳过数量。
- 行为验收的预期和实际结果。
- QA 独立性声明与 PASS/FAIL。
- 剩余风险和回滚方式。
- 失败记录；没有失败时明确写 `无`。

L2/L3 的 QA 不能由实现上下文自我批准。缺少独立性声明或 `QA: PASS` 时不得进入可合并状态。

## 5. 生命周期状态机

GitHub 标签表达动态状态：

```text
DRAFT -> READY -> IN_PROGRESS -> IMPLEMENTED -> QA_PENDING -> PASS -> MERGEABLE
                                             \-> FAIL -> IN_PROGRESS
```

补充规则：

- L3 从 READY 进入 IN_PROGRESS 前必须有 `decision:approved`。
- 任何门禁失败都进入 FAIL，不能保留 PASS 或 MERGEABLE。
- FAIL 只能回到 IN_PROGRESS，修复后重新经过 IMPLEMENTED 和 QA_PENDING。
- 状态不能跳级，不能同时存在多个 `status:*` 标签。

## 6. 证据模型

证据保存在 PR 正文、GitHub Check 输出和 CI Job Summary，不在仓库保存动态状态。

每项证据包含：

```json
{
  "gate": "test:unit",
  "command": "python3 -m unittest",
  "exitCode": 0,
  "passed": 44,
  "failed": 0,
  "skipped": 0,
  "artifact": "GitHub Actions run URL"
}
```

人工验收必须写明场景、预期、实际和证据链接。只写“已验证”不合格。

## 7. 失败诊断

统一诊断结构：

```json
{
  "code": "AT-GATE-003",
  "severity": "error",
  "location": "PR#45/测试门禁",
  "message": "required command has no exit code",
  "remediation": "record the exact command and exit code",
  "evidence": "PR body section: 测试门禁"
}
```

失败码类别：

- `AT-CONTRACT-*`：Issue 或 PR 合同不完整。
- `AT-STATE-*`：非法状态或状态跳转。
- `AT-GATE-*`：测试、行为或安全门禁失败。
- `AT-BOUNDARY-*`：任务边界违规或范围偏差未解释。
- `AT-QA-*`：QA 缺失、不独立或结论不合格。
- `AT-DRIFT-*`：协议、配置或受控文件漂移。
- `AT-SYSTEM-*`：环境、GitHub API 或解析故障。

每个失败必须给出最小复现、预期、实际、已确认根因或待确认假设、下一步动作。修复行为缺少回归证据时继续阻断。

## 8. 项目适配层

初始化器新增：

```text
.codex/scripts/validate_goal_contract.py
.codex/scripts/validate_pr_contract.py
.codex/scripts/doctor_team_collaboration.py
.github/ISSUE_TEMPLATE/team-failure.yml
docs/team-collaboration/runbook.md
```

现有 `collaboration-gate.yml` 升级为两层检查：

1. 验证协议文件未漂移。
2. 在 PR 事件中读取 PR 正文、关联 Issue 和标签，执行合同、状态与证据门禁。

GitHub API 不可用、Issue 无法读取或事件载荷不完整时，L2/L3 fail-closed，并返回 `AT-SYSTEM-*`。

## 9. Doctor 与可观测性

`doctor` 只读检查：

- Plugin、Protocol 和 Schema 版本。
- 受控文件漂移。
- 项目命令是否为空或无法识别。
- GitHub 仓库和默认分支是否已识别。
- Issue/PR 模板与 CI 工作流是否存在。
- 配置中的关键路径和保护文件是否仍为空。
- 当前环境是否具备 GitHub CLI 或 GitHub Actions 上下文。

输出同时支持人类可读文本和 JSON，退出码区分 healthy、warning 和 blocked。

## 10. 版本与迁移

- Plugin：`0.2.0`
- Protocol：`2.0.0`
- Config schema：`2`

1.x 项目升级时先预览新增文件和配置变化。发现任何受控文件漂移则停止，不覆盖本地修改。成功升级后写入 `lastUpgradedAt`，保留原 `initializedAt`。

## 11. 测试策略

- 单元测试：Markdown 合同解析、状态机、证据和诊断结构。
- 负向测试：缺字段、模糊字段、未勾选、失败退出码、意外跳过、QA 不独立、越界和非法状态跳转。
- 故障注入：GitHub API 失败、事件缺字段、损坏 JSON、路径穿越和符号链接。
- 迁移测试：1.0 -> 2.0、漂移阻断、幂等升级。
- 端到端：在多种 fixture 仓库初始化，运行 Doctor、项目验证和 PR 合同 Gate。

## 12. 完成标准

- 所有新行为都有先失败后通过的自动化测试。
- L2/L3 缺少任一强制证据时 Gate 必须失败并返回稳定失败码。
- 每个失败都能定位到合同区块、状态、命令或受控文件。
- 初始化、重复初始化、升级、修复和移除仍然非破坏性。
- 官方 Plugin/Skill 校验、完整单元测试、分发包 E2E 和故障注入全部通过。

