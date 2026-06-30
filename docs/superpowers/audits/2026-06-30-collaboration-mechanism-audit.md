# Agents-Team 协作机制审查报告

日期：2026-06-30

审查基线：`e6d41725f02a650aaafcf7ed79a0c0814762d469`

审查范围：协作协议、生命周期、角色路由、并行边界、独立 QA、证据门禁、GitHub Actions、Windows 兼容性

## 结论

Agents-Team 已经形成了较完整的协作语言和项目初始化能力，但当前实现仍属于“规则与模板驱动的治理层”，尚未达到可信的强制协作系统标准。

最关键的问题不是规则不够多，而是信任边界没有闭合：PR 可以修改验证器及其哈希清单；测试和独立 QA 主要依赖 PR 作者自报；生命周期、路由、并行边界等模块没有接入真正的合并门禁；最新版测试在 Windows 环境中也没有通过。

在这些问题修复前，不应把“Collaboration Gate 通过”解释为任务真实完成、QA 真正独立或协作边界没有被突破。当前机制可以作为协作清单和脚手架使用，但不能单独承担高风险任务的可信验收。

## 审查方法

本次审查执行了以下核验：

1. 阅读核心协议、编排规则、风险分级、角色契约和各阶段 Skill。
2. 建立生命周期、路由、worker prompt、证据校验和生成 CI 之间的调用关系。
3. 运行完整单元测试。
4. 在隔离临时仓库中初始化项目适配器，并尝试篡改验证器。
5. 构造伪造测试证据，验证生成的 PR 门禁是否会拒绝。
6. 检查 Windows 下 SessionStart Hook 和测试进程的 Python 启动方式。
7. 修改 PR head SHA 并复用旧 QA 文本，验证 QA 是否绑定当前提交。
8. 构造缺少用户批准记录的 L3 Goal，验证生成门禁是否阻止执行。
9. 检查路由表能否在 PASS 之前创建真正独立的 verifier。

## 问题清单

### P0：PR 可以同时修改验证器和哈希清单，绕过协作门禁

生成的 GitHub Actions 工作流先检出 PR 内容，再运行 PR 分支内的：

- `.codex/scripts/validate_team_collaboration.py`
- `.codex/scripts/validate_pr_contract.py`

项目适配器使用 `.codex/team-collaboration.json` 中的 `managedFiles` 校验受管文件哈希，但该配置文件自身没有不可变的信任锚点。提交者可以同时修改验证器和配置中的预期哈希，使被篡改的验证器继续通过完整性检查。

相关位置：

- `plugins/agents-team/templates/project/collaboration-gate.yml:18-25`
- `plugins/agents-team/templates/project/validate_team_collaboration.py:33-54`
- `plugins/agents-team/scripts/team_collaboration/initialize.py:180-187`

隔离复现结果：

```json
{
  "managedGateBypassAccepted": true
}
```

复现过程：

1. 初始化一个临时 Git 仓库。
2. 将生成的 `validate_pr_contract.py` 修改为直接以状态码 0 退出。
3. 更新 `team-collaboration.json` 中该文件的哈希。
4. 运行官方 `validate_team_collaboration.py`。
5. 验证器返回成功，并输出 `team collaboration project adapter: valid`。

影响：任何能够提交 PR 的主体都可能让门禁失去意义；即使分支保护要求该检查通过，也只能证明 PR 自带的验证器认可了自己。

建议：

1. 将强制验证器发布为独立 GitHub Action 或可复用工作流，并固定到不可变提交 SHA。
2. 把 PR 中的脚本、配置和 Markdown 都当作待验证数据，禁止执行 PR 提供的门禁代码。
3. 在可信 Action 内维护协议版本和受管文件清单，或从默认分支读取可信基线。
4. 如果使用 `pull_request_target`，不得检出或执行 PR head 中的代码，只能读取其文件和元数据。

### P1：测试证据可以伪造，门禁不验证真实执行结果

生成的 PR 验证器只检查测试区块中是否存在若干字符串，并要求：

- `exitCode` 等于 `0`
- `failed` 等于 `0`
- `artifact` 以 `https://` 开头
- `commitSha` 与 PR head SHA 相同

但它没有验证：

- `passed`、`failed`、`skipped` 是否为合法非负整数；
- 跳过测试时是否提供 `skipReason`；
- artifact URL 是否真实存在；
- artifact 是否属于当前仓库、当前工作流和当前提交；
- 命令是否在 CI 中执行过；
- CI conclusion 是否为 success。

相关位置：

- `plugins/agents-team/templates/project/validate_pr_contract.py:64-78`

以下伪造证据被实测接受：

```yaml
passed: fabricated
failed: 0
skipped: 999
artifact: https://example.invalid/not-evidence
```

复现结果：

```json
{
  "fabricatedEvidenceAccepted": true
}
```

建议：

1. PR 正文只用于展示，不作为测试真相源。
2. 通过 GitHub Checks/Actions API 获取当前 head SHA 对应的真实 Check Run。
3. 验证 workflow、job、repository、head SHA、conclusion 和 artifact 归属。
4. 所有计数字段使用结构化 JSON 和严格类型校验。

### P1：实现者与审查者没有可验证的上下文隔离

L2/L3 QA 的机器校验仅匹配以下文字：

```text
独立上下文：是
结论：PASS
```

相关位置：

- `plugins/agents-team/templates/project/validate_pr_contract.py:80-86`
- `plugins/agents-team/scripts/team_collaboration/evidence.py:70-77`

门禁没有验证验收者身份、运行上下文、会话 ID、执行时间或验收产物，也无法确认验收者是否参与过实现。同一个实现者可以完成代码后切换角色提示词，再自行填写“独立上下文：是”。

协议虽然要求 `verify-team-goal` 在全新上下文中运行，但仓库没有实现以下任一能力：

- 创建一个不继承实现对话的新顶层线程；
- 证明 verifier 没有接收实现过程和实现者结论；
- 区分普通角色切换、继承父上下文的子智能体和真正独立的审查主体；
- 记录实现参与者和审查参与者的主体标识；
- 阻止同一主体同时写入实现结果和 QA PASS。

相关规则目前只存在于 Markdown 和 prompt 中：

- `plugins/agents-team/references/orchestration-rules.md:18-20`
- `plugins/agents-team/skills/verify-team-goal/SKILL.md:8-10`
- `plugins/agents-team/references/roles/independent-verifier.md:13-17`

真正的独立 QA 至少需要满足：

1. verifier 使用未参与实现的新顶层上下文，默认不继承实现会话；
2. verifier 自行从 GitHub 获取 Issue、完整 PR diff、当前 head SHA 和 CI，不接受实现者转述的节选；
3. verifier 使用只读权限，不能修改代码、测试、合同和验收阈值；
4. verifier 的身份、线程或运行 ID、输入摘要、开始时间和结果形成可验证证明；
5. 实现主体与验收主体不能是同一运行身份。

普通子智能体不是天然不独立：如果平台能够证明它以空白上下文启动、没有继承实现推理、只读取最终产物，也可以成为 verifier。但当前机制既没有创建这种隔离子智能体，也没有提供可验证证明，因此普通子智能体结果不应被计为独立 QA。

建议：

1. 独立 QA 由单独工作流、GitHub App 或受保护环境生成 Check Run。
2. QA 证明至少绑定验收者、运行 ID、协议版本、PR head SHA 和结果摘要。
3. 实现工作流不得拥有写入 QA PASS 结论的权限。
4. head SHA 变化后自动使旧 QA 失效。

### P1：独立 verifier 的路由发生在 PASS 之后，形成验收循环

确定性路由表把：

- `implemented`、`qa-pending` 路由给 `review-team-goal` / `code-reviewer`；
- `pass`、`mergeable` 路由给 `ship-team-goal` / `independent-verifier`。

相关位置：

- `plugins/agents-team/references/skill-routing.md:7-13`
- `plugins/agents-team/scripts/team_collaboration/routing.py:35-50`

这意味着系统只有在状态已经是 PASS 后，才会确定性选择 independent-verifier。理论上应负责产生 PASS 的 `verify-team-goal` 并不在 `ROUTES` 或 `STATE_PHASE` 中，只能依赖主 Codex 按文字说明手动调用。

结果是验收链存在循环：必须先有 PASS 才会路由 verifier，但 PASS 本应由 verifier 产生。主 Codex 可以跳过独立 verifier，直接写入 PASS 证据，再进入 ship 阶段。

建议新增明确的 `verify` 阶段：

```text
implemented -> review -> qa-pending -> verify -> pass/fail -> ship
```

`qa-pending` 必须创建独立 verifier 运行；只有该运行绑定当前 head 并返回 PASS，状态机才允许进入 `pass`。

### P1：QA 结论没有绑定提交，代码更新后旧 QA 可以原样复用

测试证据包含 `commitSha`，但 QA 区块没有提交 SHA、运行 ID 或时间戳。PR head 更新后，只要把测试证据中的 `commitSha` 换成新值，原来的 QA 文本可以完全不变并继续通过门禁。

隔离复现结果：

```json
{
  "originalAccepted": true,
  "oldQaReusedAfterHeadChange": true,
  "qaTextChanged": false
}
```

这会让“审查通过后又修改代码”的提交继承旧 PASS，违反 current-head evidence 原则。

建议将 QA 证明绑定 `repository + PR number + head SHA + verifier identity + run ID + verdict`。任何 head SHA 变化都必须自动撤销旧 QA 状态并重新进入 `qa-pending`。

### P1：生命周期状态机没有接入 GitHub 事件和合并门禁

仓库实现了 `status_from_labels()` 和 `validate_transition()`，但生产路径中没有代码读取标签变更历史并调用状态转换校验。生成的 Collaboration Gate 也没有检查 Issue 状态标签。

相关位置：

- `plugins/agents-team/scripts/team_collaboration/lifecycle.py:11-58`
- `plugins/agents-team/templates/project/collaboration-gate.yml:14-25`

因此以下情况不会被当前 CI 阻止：

- 从 `status:ready` 直接跳到 `status:mergeable`；
- L3 在没有可信用户批准记录时进入实现；
- 多个状态标签被并发写入；
- QA FAIL 后绕过规定的返工路径；
- PR 合并后 Issue 状态仍停留在中间阶段。

建议：

1. 对 Issue label、PR synchronize、review 和 merge 事件建立可信状态转换检查。
2. 保存上一状态、触发者、时间和 head SHA，执行 compare-and-set 转换。
3. 非法转换必须产生失败 Check，而不是只在文档中规定。

### P1：L3 用户批准也属于自我声明，可以被实现者代填

库代码要求 L3 Issue 包含“L3 方案与用户确认”，但生成到项目中的真实 PR 门禁只检查通用 Issue 标题是否非空，没有检查 L3 用户确认章节、确认者身份或确认发生时间。

相关位置：

- `plugins/agents-team/scripts/team_collaboration/contracts.py:64-68`
- `plugins/agents-team/templates/project/validate_pr_contract.py:49-87`
- `plugins/agents-team/scripts/team_collaboration/lifecycle.py:37-56`

隔离复现中，将 Issue 和 PR 风险改为 L3，同时完全不提供“L3 方案与用户确认”，生成门禁仍返回通过：

```json
{
  "l3WithoutUserApprovalAccepted": true
}
```

即使补上该章节，当前系统也只验证“存在一段文字”，无法确认文字是否由用户本人授权。实现者可以代写“用户已批准”，再把 `decision_approved=True` 传给状态检查。

建议把 L3 批准建模为不可由实现主体伪造的平台事件，例如：

- 指定 GitHub 用户的 approving review；
- 受保护 Environment 的人工批准；
- 用户在 Goal Issue 上提交具有固定格式、可追溯 URL 的批准评论；
- GitHub App 记录批准者、时间、方案摘要哈希和适用 head SHA。

方案、成本或风险发生实质变化后，旧批准必须失效。

### P1：worker 文件边界和并行条件没有机器约束

`allowed_files` 和 `forbidden_files` 只被写入 worker prompt。系统没有记录每个 worker 的实际 base SHA、最终 diff 和文件归属，也没有检查 worker 是否修改禁区文件。

并行判断同样依赖调用者传入四个布尔值：

- `independent_tasks`
- `disjoint_files`
- `stable_contracts`
- `independent_tests`

相关位置：

- `plugins/agents-team/scripts/team_collaboration/roles.py:32-48`
- `plugins/agents-team/scripts/team_collaboration/routing.py:8-23`

这些值不是从任务图、文件集合或测试依赖中计算出来的，因此仍属于自我声明。两个 worker 可能在实际执行中修改同一文件、共享测试夹具或覆盖彼此结果。

建议：

1. 给每个 worker 分配明确 base SHA、路径集合和工作树。
2. 回收结果时根据真实 diff 校验允许/禁止路径。
3. 并行任务建立文件所有权或租约，冲突时退回串行。
4. 主协调器必须拒绝来源不明、超出 base SHA 或越界的补丁。

### P1：最新版测试与当前实现已经发生接口漂移

完整测试结果：

```text
Ran 116 tests in 9.717s
FAILED (failures=3, errors=6)
```

其中 `test_pr_contract.py` 仍按旧接口调用 `validate()`：

```python
module.validate(VALID_PR, issue_bodies={12: VALID_ISSUE}, require_issue_lookup=True)
```

而当前模板验证器接口已经变为：

```python
validate(pr_body, issue_body, head_sha)
```

相关位置：

- `plugins/agents-team/tests/test_pr_contract.py:80-101`
- `plugins/agents-team/templates/project/validate_pr_contract.py:49`

这说明旧版和新版 PR 合同验证逻辑并存，发布前没有完成测试迁移。

### P1：Windows 环境中的 Python 启动方式不可用

SessionStart Hook 和多项测试硬编码调用 `python3`：

- `plugins/agents-team/hooks/hooks.json:7-9`
- `plugins/agents-team/tests/test_cli.py:16-24`
- `plugins/agents-team/tests/test_distribution.py:16-18`
- `plugins/agents-team/tests/test_hook.py:20`

在本次 Windows 环境中，这些子进程返回状态码 `9009`，导致 Hook、CLI 初始化测试、分发测试失败。安全测试中的符号链接用例也没有根据 Windows 权限状态正确跳过。

建议：

1. 测试子进程使用 `sys.executable`。
2. Hook 提供跨平台启动器，不假设 `python3` 命令存在。
3. Windows 符号链接测试在缺少权限时显式 skip，并在具备权限的 CI 中另行覆盖。
4. 增加 Windows GitHub Actions 任务作为发布门禁。

### P2：存在两套漂移的合同与证据验证逻辑

库代码中的 `contracts.py` 和 `evidence.py` 会检查模糊内容、必选清单、L3 用户确认、跳过原因等内容，但生成到项目中的 `validate_pr_contract.py` 使用另一套独立实现，规则明显更弱。

相关位置：

- `plugins/agents-team/scripts/team_collaboration/contracts.py`
- `plugins/agents-team/scripts/team_collaboration/evidence.py`
- `plugins/agents-team/templates/project/validate_pr_contract.py`

这种复制会持续导致“库测试通过，但真实项目门禁未执行相同规则”。

建议：只保留一个合同引擎。生成项目时不再复制业务逻辑，而是调用固定版本的可信 Action。

### P2：外部 Skill 只按名称匹配，缺少来源和版本约束

Provider 选择只检查可用 Skill 名称是否出现在集合中，没有验证插件来源、版本、能力声明或内容哈希。

相关位置：

- `plugins/agents-team/scripts/team_collaboration/providers.py:33-42`

同名但不兼容或恶意的 Skill 可能被选为工程能力提供者，协议中的“外部 Skill 不能削弱治理”目前仍依赖主 Codex 自觉遵守。

建议：建立 Provider allowlist，并绑定插件 ID、来源、最低版本、能力契约和内容摘要。

### P2：严格模式初始化后，关键风险路径仍为空

初始化配置默认将以下字段全部设为空数组：

- `criticalPaths`
- `protectedFiles`
- `productionPaths`
- `realProviderPaths`

Doctor 只把其中部分空值报告为 warning，不会阻止 L2/L3 开始执行。

相关位置：

- `plugins/agents-team/scripts/team_collaboration/initialize.py:138-146`
- `plugins/agents-team/scripts/team_collaboration/doctor.py:58-67`

这会产生“已启用 strict 模式”的错误安全感。

建议：L2/L3 首次执行前必须完成人工确认的风险路径分类；未分类状态应为 BLOCKED，而不是 warning。

## 建议修复顺序

### 第一阶段：关闭信任边界漏洞

1. 将验证器移出 PR 可修改范围。
2. 固定可信 Action/工作流版本。
3. 禁止执行 PR 提供的治理脚本。
4. 增加门禁篡改攻击测试。

### 第二阶段：把叙述证据升级为平台证据

1. 从 Checks API 验证当前提交的真实 CI。
2. 增加显式 `verify` 阶段，在 PASS 之前创建独立 verifier。
3. 将独立 QA 建模为单独 Check Run，记录 verifier 身份和上下文证明。
4. 让旧 head 的测试、QA 和 L3 批准自动失效。
5. 严格验证测试计数、跳过原因和 artifact 归属。

### 第三阶段：真正约束协作过程

1. 接入 Issue/PR 生命周期事件。
2. 强制实现者与 verifier 使用不同运行身份和隔离上下文。
3. 将 L3 用户批准转换为可追溯的平台事件。
4. 对 worker diff 执行路径边界检查。
5. 建立并行任务文件所有权和冲突处理。
6. 对外部 Provider 建立来源和版本 allowlist。

### 第四阶段：恢复发布可信度

1. 合并重复验证实现。
2. 修复 9 项失败/错误测试。
3. 增加 Windows CI。
4. 在全部门禁通过后再恢复“tests verified”等发布声明。

## 建议新增的回归测试

- PR 同时修改验证器和 `managedFiles` 时必须失败。
- PR 修改 Collaboration Gate 工作流时必须要求受信任审核者批准。
- `passed: fabricated`、负数、浮点数、超大跳过数必须失败。
- artifact 不属于当前仓库或当前 head SHA 时必须失败。
- 实现者自行填写“独立上下文：是”不能生成 QA PASS。
- 同一线程内从 implementation-worker 切换成 independent-verifier 不能生成 QA PASS。
- 继承实现对话的普通子智能体不能被记录为独立 verifier。
- `qa-pending` 必须先运行 verifier，不能在没有 verifier run 的情况下进入 `pass`。
- head SHA 更新后旧测试证据和 QA 自动失效。
- L3 没有真实用户批准事件时必须 BLOCKED。
- 方案、成本或风险变化后旧 L3 批准自动失效。
- 非法生命周期跳转必须产生失败 Check。
- worker 修改 forbidden path 时集成必须失败。
- 两个并行 worker 路径发生交集时必须回退串行。
- Windows 上 SessionStart、初始化、验证和分发流程必须通过。

## 最终判断

当前实现的优势是协议结构清楚、初始化具备非破坏性设计、Issue/PR 模板覆盖较完整；但强制层仍没有形成不可自我修改的可信根，也没有形成“一个主体实现、另一个独立主体审查”的可验证职责分离。

把同一个智能体依次命名为 implementation-worker、code-reviewer 和 independent-verifier，不会自动产生独立性。独立性必须来自隔离上下文、不同运行身份、只读权限、独立取证和绑定当前提交的平台证明。

发布定位建议暂时调整为：

> Agents-Team 是一套协作治理模板与检查框架，而不是能够独立证明多智能体协作正确性的安全边界。

完成 P0/P1 修复并加入攻击回归测试后，再将其定位升级为强制协作机制。
