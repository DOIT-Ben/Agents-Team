# Agents-Team 可扩展能力与可信协作架构设计

状态：提案

日期：2026-06-30

适用版本：Agents-Team 0.4.0+

审查基线：`e6d41725f02a650aaafcf7ed79a0c0814762d469`

关联审计：GitHub Draft PR #4

## 1. 执行摘要

Agents-Team 当前已经具备 Goal 合同、风险分级、角色提示词、工程阶段路由、项目初始化模板和基础 PR 门禁。它已经能够表达“应该怎样协作”，但还没有形成一个可以安全接入外部能力的稳定平台。

现有外部 Skill 兼容逻辑只根据少量固定名称进行匹配，无法回答以下问题：

- 这个 Skill 来自哪里、是什么版本、许可证是否允许使用；
- 它具备哪些能力，需要哪些工具和权限；
- 它是否与当前 Protocol 版本兼容；
- 它能否修改代码、合同、状态或证据；
- 它的输出如何转换为 Agents-Team 可验证证据；
- 它失效、升级或被篡改时如何回退；
- 它是否有权参与独立 QA 或签发 PASS。

本设计建议把 Agents-Team 建设成一条“可信能力总线”：

```text
稳定治理内核
    ↓
能力注册、发现与信任解析
    ↓
Skill / Plugin / MCP / Agent / Policy Provider
    ↓
受限执行与标准证据转换
    ↓
GitHub Check、独立 QA、发布证明
```

Agents-Team 不需要自己重写所有优秀工程方法，也不应该把几十个外部仓库复制进插件。它应当保留对 Goal、风险、权限、生命周期、职责分离和验收证据的最终控制，把规划、实现、调试、浏览器、GitHub、设计、安全扫描和发布等能力交给经过审核的外部 Provider。

最终定位：

> Agents-Team 是面向 Codex 工程协作的治理内核、能力路由器和证据总线。它允许优秀 Skills、Plugins、MCP 工具和 Agent 参与工作，但任何外部能力都不能绕过 Goal、权限、风险、独立 QA 和可信交付门禁。

## 2. 动机

### 2.1 不应重复制造所有轮子

工程 Agent 生态已经积累了大量成熟能力：

- 需求澄清、产品设计和任务分解；
- TDD、系统化调试和增量实现；
- 代码审查、安全审查和浏览器验收；
- GitHub Issue、PR、Actions 和 Release 操作；
- Figma、Sentry、文档、CI、部署和供应链证明；
- 多 Agent handoff、guardrail、trace 和 human-in-the-loop。

如果 Agents-Team 自行实现所有能力，会出现重复维护、能力落后、测试面膨胀和上下文占用过大的问题。更合理的做法是建立稳定的治理协议，让外部 Provider 以可验证方式参与。

### 2.2 不能把“安装了 Skill”误认为“可以安全调用”

当前 `providers.py` 只检查 Skill 名称是否存在：

```python
if external in available:
    return ProviderDecision("external", external, normalized)
```

这种方式只能证明“当前会话中出现了同名字符串”，不能证明来源、版本、行为、权限或兼容性。名称冲突、同名恶意 Skill、过期版本和行为漂移都可能导致路由错误。

### 2.3 外部能力越多，治理缺陷的影响越大

在可信根没有闭合之前增加更多 Skills、MCP 和 Agent，会扩大以下风险：

- 更多工具获得写入、网络、密钥和外部系统权限；
- 外部 Skill 可能改变验收阈值或绕过失败；
- 多 Agent 并发可能覆盖文件、重复收费或重复发布；
- 不同 Provider 产生不可比较的“完成”声明；
- 依赖升级可能无声改变工作流；
- 供应链来源和许可证变得不可追踪。

因此，扩展能力必须建立在可信门禁、职责分离和标准证据之上，而不是先追求 Provider 数量。

### 2.4 独立审查需要真实运行时支持

把同一智能体依次命名为 implementation-worker、code-reviewer 和 independent-verifier，不会自然产生独立性。真正的独立审查需要：

- 未参与实现的新上下文；
- 不继承实现推理和完成叙述；
- 只读权限；
- 独立读取 GitHub Issue、完整 diff、当前提交和 CI；
- 可验证的 verifier 身份、运行 ID 和输入摘要；
- 绑定当前 head SHA 的 PASS/FAIL；
- 代码变化后旧 QA 自动失效。

Codex App Server、Codex SDK、GitHub Action 和自定义 Agent 为这一能力提供了官方基础，不需要继续停留在 Markdown 自我声明层。

## 3. 设计目标

### 3.1 必须达到

1. 保持 Agents-Team 治理协议高于任何外部 Provider。
2. 支持 Skill、Plugin、MCP、Agent、Policy 和 Evidence Provider。
3. 使用统一 Manifest 描述来源、版本、能力、权限、依赖和证据输出。
4. 使用 allowlist、固定版本和兼容性测试控制供应链。
5. 将外部输出转换为统一 Evidence Envelope。
6. 建立显式 `verify` 阶段，在 PASS 之前创建独立 verifier。
7. 将 QA、用户批准和发布证明绑定当前 head SHA。
8. 支持 Provider 不可用时安全回退，不把缺失能力降级成成功。
9. 保持 Windows、Linux 和 macOS 的可运行性。
10. 提供清晰的诊断、审计日志和升级策略。

### 3.2 非目标

1. 不复制或常驻加载所有外部 Skill。
2. 不建立无边界的公共 Skill 市场。
3. 不让外部 Provider 直接修改治理协议和验收结果。
4. 不在首版引入深层递归 Agent 树。
5. 不自动执行生产发布、付款、数据迁移或不可逆操作。
6. 不用 Agent 自述替代 GitHub、CI、运行时和签名证据。
7. 不要求所有项目安装 OPA、in-toto 或 A2A；高级能力按风险和规模启用。

## 4. 核心原则

### 4.1 治理与能力分层

```text
Goal、风险、权限、生命周期、职责分离、验收
    > Provider 路由与适配
    > 外部 Skill / Plugin / MCP / Agent 的局部工作流
```

外部 Provider 可以决定“怎样完成被授权的任务”，不能决定“任务是否被授权、是否已经完成、是否允许合并”。

### 4.2 默认拒绝，按能力授权

Provider 没有声明的能力视为禁止。没有通过信任解析、版本校验和健康检查的 Provider 不参与路由。

### 4.3 证据高于叙述

“测试通过”“用户已确认”“独立 QA：是”都不是证据。可信证据必须具有来源、主体、时间、当前提交、执行结果和可验证引用。

### 4.4 独立性是可证明属性

独立 verifier 必须拥有独立运行身份和上下文证明。角色名称、提示词和模型自报不能构成独立性。

### 4.5 固定版本优于自动追新

生产路由只使用固定版本或固定提交。升级经过发现、评估、兼容性测试、人工批准和回滚准备，不自动跟随外部 `latest`。

### 4.6 插件失效不能拖垮治理内核

外部 Provider 不可用时：

- 非必要能力回退内置 Provider；
- 必要能力返回 BLOCKED；
- 不允许把缺失的真实环境、验证器或权限转换成 PASS。

## 5. 备选方案与取舍

### 5.1 方案 A：完整复制外部 Skills

做法：把 Addy Agent Skills、Superpowers 等内容复制到 Agents-Team 仓库，作为内置能力维护。

优点：

- 离线可用；
- 路由简单；
- 能统一调整文案和接口。

缺点：

- 上游升级难以同步；
- 许可证和版权维护复杂；
- 大量低频 Skill 占用分发包和技能发现预算；
- 容易产生本地分叉和过期实现；
- Agents-Team 从治理项目膨胀为综合 Skill 仓库。

结论：不采用。只吸收必要思想和最低回退能力。

### 5.2 方案 B：继续按名称匹配外部 Skill

做法：扩充 `EXTERNAL` 字典，检测到同名 Skill 就调用。

优点：

- 实现成本最低；
- 与当前结构兼容。

缺点：

- 无法验证来源和版本；
- 无法声明权限和工具依赖；
- 名称冲突和同名恶意 Skill 无法处理；
- 不支持 MCP、独立 Agent 和策略引擎；
- 输出没有统一证据转换。

结论：仅作为迁移期兼容模式，0.5.0 后默认关闭。

### 5.3 方案 C：治理内核 + Provider Registry + 适配器

做法：建立标准能力模型、Provider Manifest、信任解析、适配器、受限执行和证据总线。

优点：

- 不复制外部实现；
- 可接入不同类型能力；
- 来源、版本、权限和证据可追踪；
- 能安全回退和升级；
- 适合逐步接入官方和社区生态。

缺点：

- 需要设计 Manifest、兼容性测试和运行时；
- 初期开发量高于名称匹配；
- 独立 Agent 和 Check Run 需要外部服务或 GitHub 权限。

结论：采用方案 C。

## 6. 目标架构

```text
┌─────────────────────────────────────────────────────────────┐
│                        Goal Contract                        │
│ Goal / Must Complete / Gates / Boundary / Risk / Rollback  │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│                    Agents-Team Governance Core              │
│ Policy / Lifecycle / Authority / Separation / State        │
└──────────────┬──────────────────────┬───────────────────────┘
               │                      │
┌──────────────▼─────────────┐  ┌─────▼──────────────────────┐
│ Capability Registry       │  │ Trust & Policy Engine      │
│ discover / pin / health   │  │ allow / deny / escalate    │
└──────────────┬─────────────┘  └─────┬──────────────────────┘
               │                      │
┌──────────────▼──────────────────────▼───────────────────────┐
│                     Provider Adapter Layer                  │
│ Skill │ Plugin │ MCP │ Agent │ Policy │ Evidence Adapter    │
└───┬────────┬────────┬────────┬──────────┬───────────────────┘
    │        │        │        │          │
    ▼        ▼        ▼        ▼          ▼
 Skills   Plugins   Tools   Verifiers   Attestations
    │        │        │        │          │
┌───▼────────▼────────▼────────▼──────────▼───────────────────┐
│                      Evidence Bus                           │
│ command / check / diff / behavior / approval / QA / release│
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│ GitHub Check Runs / PR / Issue / Release / Audit Log       │
└─────────────────────────────────────────────────────────────┘
```

## 7. 组件设计

### 7.1 Governance Core

职责：

- 解析并验证 Goal 合同；
- 确定风险等级；
- 计算允许和禁止权限；
- 管理生命周期状态；
- 决定是否允许并行；
- 强制职责分离；
- 评估 Evidence Envelope；
- 产生 PASS、FAIL 或 BLOCKED。

禁止：

- 不直接执行具体工程 Skill；
- 不下载 Provider；
- 不接受 Provider 自行提升权限；
- 不让 Provider 直接设置 `status:pass` 或 `mergeable`。

Governance Core 必须是唯一能够改变协作生命周期的组件。

### 7.2 Capability Registry

职责：

- 发现已安装 Provider；
- 读取 Provider Manifest；
- 校验来源、版本和摘要；
- 执行兼容性与健康检查；
- 输出可用于路由的标准能力集合；
- 保存固定版本和升级状态。

Provider 状态：

```text
discovered
  → quarantined
  → verified
  → enabled
  → degraded
  → disabled
  → revoked
```

只有 `enabled` Provider 可以参与路由。必要 Provider 进入 `degraded` 或 `revoked` 时，相关任务必须 BLOCKED。

### 7.3 Trust Resolver

信任解析输入：

- Provider ID 和类型；
- 安装来源；
- 固定版本或 Git SHA；
- 内容摘要；
- 许可证；
- 发布者 allowlist；
- 当前 Protocol 兼容范围；
- 请求的权限和工具；
- 是否通过兼容性测试；
- 是否存在已知撤销记录。

信任结果：

```json
{
  "decision": "allow | deny | review-required",
  "provider": "superpowers",
  "version": "5.1.4",
  "capabilities": ["planning", "tdd", "review"],
  "grantedPermissions": ["repo:read", "workspace:write"],
  "deniedPermissions": ["governance:write", "qa:sign"],
  "reasonCodes": ["SOURCE_ALLOWLISTED", "COMPATIBILITY_PASSED"]
}
```

### 7.4 Skill Adapter

Skill Adapter 负责把 Agent Skills 标准和不同社区 Skill 映射为 Agents-Team 能力。

标准能力建议：

```text
goal.refine
plan.decompose
design.review
build.incremental
test.tdd
debug.systematic
review.code
review.security
verify.behavior
ship.prepare
release.execute
```

适配器不修改外部 Skill 原文，只负责：

1. 识别触发条件；
2. 注入 Goal 和任务边界；
3. 限制工具和路径权限；
4. 定义超时与失败策略；
5. 将输出转换为标准证据；
6. 拒绝外部 Skill 的越权结论。

### 7.5 Plugin Adapter

Plugin 是 Skills、MCP、Apps、Hooks 和资源的分发单元。Agents-Team 应支持从 Codex Marketplace 安装外部 Plugin，但不把“已安装”直接视为“已授权”。

Plugin Adapter 读取：

- `.codex-plugin/plugin.json`；
- Skills 列表；
- `.mcp.json`；
- `.app.json`；
- hooks；
- 版本、开发者、许可证和仓库地址。

每个组件分别授权。例如一个 Plugin 可以被允许使用只读 GitHub MCP，但其写入 Issue 工具保持禁用。

### 7.6 MCP Tool Broker

MCP Tool Broker 统一管理工具发现和权限：

- 使用 `enabled_tools` 建立工具 allowlist；
- 使用 `disabled_tools` 阻止危险工具；
- 为每个工具设置 approval mode；
- 记录调用主体、参数摘要、结果和耗时；
- 对敏感字段进行脱敏；
- 将工具调用转换为 Evidence Envelope。

首批推荐 MCP：

| MCP | 用途 | 默认权限 |
| --- | --- | --- |
| GitHub MCP | Issue、PR、Checks、Actions、Release | 只读；写入需单独授权 |
| Playwright MCP | 浏览器行为验收 | 测试环境写入 |
| Chrome DevTools MCP | 性能、网络、运行时诊断 | 只读优先 |
| Sentry MCP | 错误和回归证据 | 只读 |
| Context7 | 最新依赖文档 | 只读 |
| Figma MCP | 设计上下文和视觉核对 | 只读优先 |

### 7.7 Agent Runtime Adapter

Agent Runtime Adapter 负责创建、隔离和追踪 Agent 运行，不把角色文档等同于真实 Agent。

支持的运行方式：

1. Codex App Server；
2. Codex SDK；
3. Codex GitHub Action；
4. 本地 Codex 自定义 Agent；
5. 后期支持 A2A 远程 Agent。

每次 Agent Run 必须记录：

```json
{
  "runId": "run_...",
  "threadId": "thr_...",
  "agentType": "implementation-worker",
  "provider": "codex-app-server",
  "model": "configured-model",
  "baseSha": "...",
  "sandbox": "workspace-write",
  "toolPolicyHash": "sha256:...",
  "inputDigest": "sha256:...",
  "startedAt": "...",
  "completedAt": "...",
  "result": "success | fail | blocked"
}
```

### 7.8 Independent Verifier Runtime

独立 verifier 是 Agent Runtime 的特殊安全角色。

硬要求：

1. 使用 `thread/start` 创建新线程，不使用继承实现历史的 `thread/fork`；
2. verifier 的 runId 和 threadId 与所有 implementation run 不同；
3. verifier 只接收 Goal、完整最终 diff、当前 head SHA、CI、行为入口和回滚要求；
4. verifier 自行从 GitHub 获取证据，不接受实现者提供的摘录；
5. verifier 使用只读 sandbox；
6. verifier 不能修改代码、测试、合同、证据和验收阈值；
7. verifier 只能签发 PASS、FAIL 或 BLOCKED；
8. PASS 必须写入单独 GitHub Check Run；
9. head SHA 变化后旧 verifier run 自动失效；
10. verifier 不得与实现者共享同一运行身份。

对于暂时无法自动创建独立线程的环境，允许人工在 Codex App 中新建线程，但必须记录线程 ID 和人工触发者。无法证明独立上下文时只能返回 BLOCKED。

### 7.9 Policy Engine

首版使用 Python 结构化策略；后期可选接入 Open Policy Agent。

Policy 输入：

- Goal 风险；
- 当前状态和请求转换；
- actor/run identity；
- Provider 信任结果；
- 文件 diff；
- 工具权限；
- Evidence Envelope；
- 用户批准和 QA 证明。

典型策略：

```text
deny if L3 and approvedByUser is absent
deny if verifier.runId belongs to implementation runs
deny if evidence.headSha != pullRequest.headSha
deny if changedFile matches forbiddenPaths
deny if provider is not pinned
deny if provider requests governance:write
deny if paid tool lacks explicit approval
```

Policy Engine 返回稳定 reason code，不能只返回自然语言。

### 7.10 Evidence Bus

所有 Provider 输出统一转换为 Evidence Envelope：

```json
{
  "schemaVersion": 1,
  "evidenceId": "ev_...",
  "type": "command | check-run | behavior | approval | qa | release",
  "subject": {
    "repository": "owner/repo",
    "pullRequest": 45,
    "headSha": "..."
  },
  "producer": {
    "providerId": "github-mcp",
    "providerVersion": "pinned-version",
    "runId": "run_...",
    "actor": "..."
  },
  "result": "pass | fail | blocked",
  "startedAt": "...",
  "completedAt": "...",
  "artifact": {
    "url": "https://...",
    "digest": "sha256:..."
  },
  "details": {},
  "signature": null
}
```

首版 signature 可以为空，但来源必须是可信 GitHub Check 或本地受控运行。L3 后期要求 in-toto/Sigstore attestation。

### 7.11 GitHub Evidence Adapter

GitHub 是任务和交付的动态真源，但不能继续信任 PR 作者手填证据。

适配器应通过 GitHub API 或 GitHub MCP 验证：

- Issue 是否存在且属于当前仓库；
- Issue 作者、状态、标签和批准评论；
- PR head SHA；
- required checks；
- Check Run 的 app、workflow、结论和 head SHA；
- Review 作者和 approval 状态；
- artifact URL 是否属于对应 run；
- 合并目标和分支保护；
- Release 和部署状态。

PR 正文仍然保留人类可读摘要，但不再是机器证据的真源。

### 7.12 Observability Adapter

最低记录：

- Goal ID；
- 生命周期转换；
- 路由决策；
- Provider 选择和回退；
- Agent run；
- MCP 调用摘要；
- Policy decision；
- Evidence Envelope；
- QA 和批准失效事件；
- 最终交付状态。

默认不记录密钥、完整 Prompt、用户隐私数据和未经脱敏的工具输出。后期可输出 OpenTelemetry trace，但日志与 trace 必须遵守项目数据策略。

### 7.13 核心接口边界

建议先固定纯数据接口，再实现具体 Provider：

```python
def discover_providers(search_roots: list[Path]) -> list[ProviderManifest]: ...

def verify_provider(
    manifest: ProviderManifest,
    lock: ProviderLock,
    environment: RuntimeEnvironment,
) -> ProviderVerification: ...

def resolve_capability(
    request: CapabilityRequest,
    providers: list[VerifiedProvider],
    policy: PolicyContext,
) -> RouteDecision: ...

def start_agent_run(
    decision: RouteDecision,
    contract: GoalContract,
    runtime: AgentRuntime,
) -> AgentRunIdentity: ...

def normalize_evidence(
    provider_output: object,
    adapter: EvidenceAdapter,
    subject: EvidenceSubject,
) -> EvidenceEnvelope: ...

def evaluate_transition(
    previous: LifecycleState,
    requested: LifecycleState,
    evidence: list[EvidenceEnvelope],
    policy: PolicyContext,
) -> PolicyDecision: ...

def invalidate_stale_evidence(
    previous_head: str,
    current_head: str,
    evidence: list[EvidenceEnvelope],
) -> list[EvidenceInvalidation]: ...
```

接口要求：

- 输入和输出可 JSON 序列化；
- 核心函数不直接读取全局环境；
- Provider 执行与 Policy 判定分离；
- Evidence Adapter 不具备生命周期写权限；
- 每个失败返回稳定 reason code；
- 所有路径使用仓库相对规范化形式；
- 所有时间使用 UTC ISO 8601；
- 所有提交使用完整 SHA。

### 7.14 诊断码

建议增加：

| 代码 | 含义 |
| --- | --- |
| `AT-PROVIDER-001` | Provider Manifest 缺失或无效 |
| `AT-PROVIDER-002` | Provider 来源、版本或摘要不可信 |
| `AT-PROVIDER-003` | Provider 与 Protocol 不兼容 |
| `AT-PROVIDER-004` | Provider 请求未授权权限 |
| `AT-PROVIDER-005` | Provider 健康检查失败 |
| `AT-ROUTE-001` | 没有满足能力和权限的 Provider |
| `AT-RUN-001` | Agent runtime 无法创建隔离运行 |
| `AT-QA-003` | verifier 与实现运行身份重叠 |
| `AT-QA-004` | QA evidence 不属于当前 head |
| `AT-EVIDENCE-001` | Evidence Envelope schema 无效 |
| `AT-EVIDENCE-002` | Evidence producer 不可信 |
| `AT-EVIDENCE-003` | Evidence artifact 无法验证 |
| `AT-POLICY-001` | Policy Engine 不可用，已 fail closed |
| `AT-APPROVAL-001` | L3 缺少可验证用户批准 |
| `AT-SUPPLY-001` | Provider 许可证或供应链状态阻断 |

## 8. Provider Manifest

### 8.1 示例

```yaml
schemaVersion: 1
id: superpowers
displayName: Superpowers
type: skill-pack

source:
  kind: git
  repository: obra/superpowers
  ref: v5.1.4
  digest: sha256:...
  license: MIT

compatibility:
  agentsTeamProtocol: ">=2.0.0 <3.0.0"
  codex: ">=required-version"
  platforms: [windows, linux, macos]

capabilities:
  - id: plan.decompose
    entrypoint: writing-plans
  - id: test.tdd
    entrypoint: test-driven-development
  - id: debug.systematic
    entrypoint: systematic-debugging
  - id: review.code
    entrypoint: requesting-code-review

permissions:
  requested:
    - repo:read
    - workspace:write
    - command:test
  forbidden:
    - governance:write
    - lifecycle:write
    - qa:sign
    - release:execute

evidence:
  adapter: superpowers-v1
  outputs:
    - task-result
    - command-result
    - review-findings

fallback:
  provider: builtin
```

### 8.2 Provider 类型

| 类型 | 说明 | 示例 |
| --- | --- | --- |
| `skill` | 单个可复用工作流 | systematic-debugging |
| `skill-pack` | 多个相关 Skills | Superpowers、Agent Skills |
| `plugin` | Skills + MCP + Apps + Hooks | Codex Plugin |
| `mcp` | 外部工具和数据 | GitHub MCP |
| `agent-runtime` | 创建和运行 Agent | Codex SDK |
| `policy` | 规则决策 | OPA |
| `evidence` | 证明与签名 | in-toto、Sigstore |
| `remote-agent` | 远程 Agent 服务 | A2A Agent |

### 8.3 Manifest 不可声明的权限

以下权限只能由项目治理配置授予，Provider Manifest 自己声明无效：

- `governance:write`
- `risk:downgrade`
- `goal:change`
- `boundary:expand`
- `approval:forge`
- `qa:sign`
- `merge:authorize`
- `release:production`
- `billing:approve`
- `secret:read-all`

## 9. 路由设计

### 9.1 新生命周期

```text
draft
  → ready
  → planned
  → in-progress
  → implemented
  → review-pending
  → reviewed
  → qa-pending
  → verifying
  → pass | fail | blocked
  → mergeable
  → merged
  → released
```

关键变化：

- `verify` 成为显式阶段；
- independent-verifier 在 `qa-pending` 时创建，而不是 PASS 后才路由；
- `pass` 必须由可信 verifier evidence 触发；
- head SHA 变化将 `reviewed`、`pass`、`mergeable` 退回相应待验状态；
- 发布与合并成为独立状态。

### 9.2 路由输入

```json
{
  "intent": "implement upload",
  "status": "in-progress",
  "risk": "L2",
  "goalCapabilities": ["build.incremental", "test.tdd"],
  "allowedPaths": ["src/upload/**", "tests/upload/**"],
  "forbiddenPaths": ["auth/**", "billing/**"],
  "availableProviders": [],
  "requiredEvidence": [],
  "runtimeConstraints": {
    "platform": "windows",
    "network": true,
    "paidToolsAllowed": false
  }
}
```

### 9.3 路由评分

候选 Provider 先经过硬门禁，再按以下因素评分：

1. 能力完全匹配；
2. Protocol 兼容；
3. 来源可信且版本固定；
4. 所需权限不超过任务授权；
5. 当前平台可用；
6. 健康检查通过；
7. 证据适配器存在；
8. 项目显式偏好；
9. 历史成功率和稳定性；
10. 成本和时延。

不能通过硬门禁的 Provider 不进入评分。

### 9.4 回退规则

| 场景 | 行为 |
| --- | --- |
| 外部 Skill 不存在 | 使用内置 Provider |
| 外部 Skill 版本不兼容 | BLOCKED 或内置回退 |
| 必需 MCP 不可用 | BLOCKED |
| 只读 MCP 不可用且证据可由 GitHub API获得 | 使用 API Adapter |
| verifier runtime 不可用 | L2/L3 BLOCKED |
| Policy Engine 不可用 | fail closed |
| Evidence Adapter 失败 | 不接受 Provider 完成声明 |

## 10. 关键流程

### 10.1 L2 正常交付

```text
1. Goal Issue 验证
2. 风险确定为 L2
3. Capability Registry 发现 Provider
4. Trust Resolver 过滤并授权
5. planner 创建任务图和路径所有权
6. implementation worker 在隔离工作树执行
7. 主协调器验证真实 diff 和测试证据
8. code reviewer 审查当前 head
9. 状态进入 qa-pending
10. 创建全新只读 verifier thread
11. verifier 独立读取 GitHub 和运行验收
12. 生成绑定 head SHA 的 QA Check Run
13. Policy Engine 允许进入 pass
14. ship 阶段验证 required checks 和回滚
15. 状态进入 mergeable
```

### 10.2 head SHA 更新

```text
PR synchronize
  → 识别新 head SHA
  → 旧测试证据标记 stale
  → 旧 review 标记 stale
  → 旧 QA Check 标记 stale
  → pass / mergeable 失效
  → 回到 review-pending 或 qa-pending
```

### 10.3 L3 用户批准

```text
方案摘要 + 成本 + 风险 + 回滚
  → 用户通过受信任 GitHub 身份或 Environment 批准
  → 生成 Approval Evidence
  → 绑定方案摘要哈希与适用 head/base SHA
  → 允许进入实现
```

方案、成本、权限或不可逆影响变化时，批准自动失效。

### 10.4 Provider 升级

```text
发现新版本
  → 生成升级报告
  → 许可证和来源复核
  → 在隔离环境运行兼容性测试
  → 比较行为和权限变化
  → 人工批准
  → 更新固定版本与摘要
  → 保留上一版本回滚入口
```

## 11. 外部轮子集成建议

### 11.1 OpenAI Plugins 与 Agent Skills 标准

用途：

- 作为 Skill 和 Plugin 的标准分发格式；
- 使用渐进披露降低上下文占用；
- 声明 MCP 工具依赖；
- 通过 Marketplace 管理安装和更新。

说明：`openai/skills` 已提示迁移到 `openai/plugins`。新集成应以 OpenAI Plugins 仓库和 Codex Plugin 文档为当前参考，不再把已弃用仓库作为上游真源。

优先级：P0，作为 Provider Registry 的格式基础。

### 11.2 Addy Osmani Agent Skills

适合能力：

- planning-and-task-breakdown；
- incremental-implementation；
- debugging-and-error-recovery；
- code-review-and-quality；
- shipping-and-launch。

当前仓库已经映射这些名称，但需要补充固定版本、来源、兼容性、权限和证据适配器。

优先级：P1，作为首个兼容性 Provider。

### 11.3 Superpowers

适合吸收：

- brainstorming 与设计批准；
- writing-plans；
- TDD；
- systematic-debugging；
- verification-before-completion；
- subagent-driven-development；
- 规格符合性审查与代码质量审查分离；
- Skill 行为评测。

不直接采用：

- 把普通子智能体结果自动视为独立 QA；
- 让外部 Skill 决定 Agents-Team 生命周期；
- 自动扩大并行深度。

优先级：P1，作为第二个兼容性 Provider和 Skill 测试参考。

### 11.4 GitHub MCP Server

用途：

- 获取 Issue、PR、Review、Check Run、Workflow Run 和 Release；
- 将 PR 手工证据替换为平台真实证据；
- 创建受控评论、Check 和 Issue；
- 监控 head SHA 与 required checks。

优先级：P0，是可信证据的核心依赖。

### 11.5 Codex App Server、SDK 与 GitHub Action

用途：

- 创建全新独立线程；
- 控制 read-only / workspace-write sandbox；
- 记录 thread、turn 和 item 事件；
- 在 CI 中执行独立审查；
- 构建可验证 verifier runtime。

优先级：P0，解决独立 QA 真实性。

### 11.6 Open Policy Agent

用途：

- 把风险、路径、权限、状态和职责分离规则写成可测试策略；
- 返回稳定 allow/deny 结果；
- 将治理策略与执行代码解耦。

首版不强制安装。先定义 Policy Adapter，待 Python 策略稳定后增加 OPA Provider。

优先级：P2。

### 11.7 in-toto、Sigstore 与 SLSA

用途：

- 证明哪个主体执行了哪个步骤；
- 绑定输入、输出和产物摘要；
- 对发布物和 attestation 签名；
- 建立供应链可追溯性。

优先用于 L3、正式发布和分发包，不要求普通 L1/L2 项目启用。

优先级：P2。

### 11.8 OpenTelemetry

用途：

- 记录跨 Provider 的 trace；
- 分析路由耗时、失败点和重试；
- 关联 Goal、run、tool call 和 evidence。

默认只记录元数据和摘要，禁止无条件收集 Prompt、密钥和用户内容。

优先级：P2。

### 11.9 OpenAI Agents SDK

Agents SDK 已提供 handoff、guardrail、human-in-the-loop、session 和 tracing 等多 Agent 原语。如果 Agents-Team 未来从 Codex Plugin 演进为独立服务，可以把 Agents SDK 作为一种 Agent Runtime Provider。

当前阶段不建议把治理内核迁移到 Agents SDK，原因是：

- 会同时维护 Codex Skill/Plugin 运行时和 Agents SDK 运行时；
- 需要额外处理身份、会话、工具权限和证据转换；
- 当前最紧迫的问题是可信门禁和独立 verifier，不是重新实现整个编排器。

推荐做法：先通过统一 `AgentRuntimeAdapter` 接入 Codex App Server/SDK；接口稳定后，再实现可选 `openai-agents-sdk` Provider。Agents SDK 的 tracing、guardrail 和 handoff 思想可以先吸收进标准运行合同。

优先级：P3。

### 11.10 安全与供应链扫描 Provider

建议把静态安全扫描、依赖漏洞和制品扫描作为 Evidence Provider 接入，而不是把所有扫描器嵌入 Governance Core。

候选能力：

- GitHub CodeQL：代码语义安全扫描；
- Semgrep：可配置静态规则；
- OSV-Scanner：开源依赖漏洞；
- Trivy：依赖、容器、文件系统和配置扫描；
- Gitleaks：密钥泄露检测。

统一要求：

- 扫描结果绑定当前 head SHA；
- 记录规则集和扫描器版本；
- P0/P1 阈值由项目策略决定，扫描器不能自行降低；
- SARIF 或原始 artifact 必须可追溯；
- 缺失必需扫描器时返回 BLOCKED，而不是 N/A。

优先级：P1，可从 CodeQL 和密钥扫描开始。

### 11.11 A2A Protocol

用途：

- 连接不同框架、不同组织或远程服务中的 Agent；
- 通过 Agent Card 声明能力和连接方式；
- 在保留内部实现不透明的情况下协作。

A2A 适合远程 Agent，MCP 适合工具。当前版本不需要 A2A；完成本地可信运行和证据模型后再接入。

优先级：P3。

## 12. 仓库结构建议

```text
plugins/agents-team/
├── providers/
│   ├── builtin/
│   ├── manifests/
│   │   ├── addy-agent-skills.yaml
│   │   ├── superpowers.yaml
│   │   ├── github-mcp.yaml
│   │   └── codex-verifier.yaml
│   └── adapters/
│       ├── skill_adapter.py
│       ├── plugin_adapter.py
│       ├── mcp_adapter.py
│       ├── agent_runtime_adapter.py
│       ├── github_evidence_adapter.py
│       └── policy_adapter.py
├── schemas/
│   ├── provider-manifest.schema.json
│   ├── evidence-envelope.schema.json
│   ├── run-identity.schema.json
│   └── approval-evidence.schema.json
├── scripts/team_collaboration/
│   ├── registry.py
│   ├── trust.py
│   ├── permissions.py
│   ├── policy.py
│   ├── evidence_bus.py
│   ├── verifier_runtime.py
│   └── github_checks.py
├── templates/project/
│   ├── .codex/agents/
│   │   ├── implementation-worker.toml
│   │   ├── code-reviewer.toml
│   │   └── independent-verifier.toml
│   └── .github/workflows/
│       ├── collaboration-contract.yml
│       └── independent-qa.yml
└── tests/
    ├── providers/
    ├── policy/
    ├── evidence/
    ├── attacks/
    └── compatibility/
```

## 13. 项目配置建议

`.codex/team-collaboration.json` 增加：

```json
{
  "providers": {
    "mode": "allowlist",
    "lockFile": ".codex/providers.lock.json",
    "allow": [
      "builtin",
      "addy-agent-skills",
      "superpowers",
      "github-mcp",
      "codex-verifier"
    ],
    "autoUpdate": false
  },
  "permissions": {
    "default": "deny",
    "qaSigner": ["codex-verifier"],
    "governanceWriter": ["agents-team-core"]
  },
  "verification": {
    "requireFreshThread": {
      "L1": false,
      "L2": true,
      "L3": true
    },
    "invalidateOnHeadChange": true,
    "requireCheckRun": {
      "L1": false,
      "L2": true,
      "L3": true
    }
  },
  "policy": {
    "engine": "builtin",
    "failClosed": true
  }
}
```

Lock file 记录：

```json
{
  "providers": [
    {
      "id": "superpowers",
      "version": "5.1.4",
      "source": "obra/superpowers",
      "ref": "v5.1.4",
      "digest": "sha256:...",
      "verifiedAt": "...",
      "compatibilityResult": "pass"
    }
  ]
}
```

## 14. 安全与威胁模型

### 14.1 主要威胁

| 威胁 | 防护 |
| --- | --- |
| 同名恶意 Skill | 来源 allowlist、版本和摘要固定 |
| PR 修改治理脚本 | 从可信 Action/默认分支运行验证器 |
| Provider 扩大权限 | 默认拒绝、Policy Engine |
| 实现者自签 QA | 独立运行身份和 Check Run |
| 旧 QA 复用 | 绑定 head SHA，变化即失效 |
| MCP 泄露密钥 | 工具 allowlist、环境变量隔离、脱敏 |
| 自动升级破坏行为 | 禁止自动更新、兼容性测试、回滚 |
| 并行 worker 覆盖文件 | 工作树隔离、路径租约、diff 校验 |
| Provider 伪造证据 | GitHub API、签名和证据适配器 |
| 许可证违规 | 安装前许可证扫描和 NOTICE 记录 |

### 14.2 权限域

```text
repo:read
workspace:write
command:test
network:read
github:read
github:write
secret:scoped
paid-provider:invoke
governance:write
qa:sign
merge:authorize
release:execute
```

Provider 必须声明最小权限。L3 权限不能由 Provider 自行申请后自动获得。

### 14.3 数据最小化

- Skill 只接收完成任务所需的 Goal 片段；
- MCP 不获得无关仓库、组织和账号权限；
- verifier 不接收实现推理历史；
- trace 默认不保存完整 Prompt；
- Evidence Envelope 不包含密钥和隐私内容；
- 日志保留周期由项目配置控制。

## 15. 兼容性与许可证

### 15.1 兼容性矩阵

每个 Provider 至少在以下维度测试：

- Agents-Team Protocol；
- Codex 版本；
- Windows / Linux / macOS；
- Skill 或 Plugin 版本；
- 所需 MCP 工具；
- 只读和写入 sandbox；
- 离线/断网行为；
- 回退 Provider。

### 15.2 许可证处理

1. Manifest 必须声明 SPDX license。
2. 无法识别许可证时默认禁止自动集成。
3. 直接复制或修改上游内容时保留版权和许可证。
4. 只吸收思想和重新实现时，在设计文档和 NOTICE 中说明参考来源。
5. Provider 升级必须重新检查许可证变化。

## 16. 测试策略

### 16.1 单元测试

- Manifest schema；
- 版本范围和摘要校验；
- 能力映射；
- 权限计算；
- Policy allow/deny；
- Evidence Envelope；
- 状态转换和证据失效；
- Provider 评分与回退。

### 16.2 合同测试

每个 Provider 必须通过统一测试套件：

- 输入 Goal 和边界后不得越权；
- 失败时返回结构化失败；
- 不得签发自己无权签发的 QA；
- 输出能转换为 Evidence Envelope；
- 当前平台和依赖缺失时正确 BLOCKED；
- 固定版本内容与 lock file 摘要一致。

### 16.3 安全负向测试

- 同名恶意 Skill 不能替代 allowlist Provider；
- 修改 Provider Manifest 后摘要不匹配必须失败；
- PR 修改验证器和哈希清单不能绕过门禁；
- Provider 请求 `governance:write` 必须拒绝；
- implementation run 不能签发 QA；
- 继承实现上下文的 verifier 不能被标记独立；
- head SHA 更新后旧 QA 和用户批准必须失效；
- MCP 返回含密钥内容时必须脱敏；
- artifact 来自其他仓库或提交时必须拒绝；
- 外部 Provider 不可用时不能降级成 PASS。

### 16.4 集成测试

1. 内置 Provider 完整 L1 流程；
2. Addy Skill Provider 完整 L2 流程；
3. Superpowers Provider 规划、TDD 和代码审查；
4. GitHub MCP 读取真实 Check Run；
5. Codex verifier 创建全新线程并生成 QA Check；
6. Provider 故障后的内置回退；
7. L3 用户批准、真实 Provider smoke 和回滚；
8. Windows、Linux 和 macOS 初始化与运行。

### 16.5 Skill 行为评测

不能只测试 Skill 文档是否包含某句话。应建立场景评测：

- 模糊需求是否先澄清；
- 测试失败时是否停止；
- 用户要求越权时是否拒绝；
- 同一主体要求自签 QA 时是否 BLOCKED；
- 证据缺失时是否避免完成声明；
- 反复失败时是否收敛诊断。

## 17. 分阶段实施

### 阶段 0：修复可信根

目标：关闭审计报告中的 P0/P1 门禁问题。

交付：

- 不可由 PR 修改的验证器；
- 仓库自身 Linux/Windows CI；
- GitHub Check 真实证据；
- 当前 head 证据失效机制；
- 独立 QA 不再依赖 PR 自报。

退出条件：门禁篡改、伪造证据和旧 QA 复用攻击测试全部失败关闭。

### 阶段 1：能力模型与 Provider Registry

交付：

- Provider Manifest schema；
- Capability taxonomy；
- lock file；
- Trust Resolver；
- 内置 Provider 迁移；
- 旧名称匹配兼容层和弃用警告。

退出条件：内置流程全部通过 Registry 执行，旧项目行为保持兼容。

### 阶段 2：首批 Skill Provider

交付：

- Addy Agent Skills Adapter；
- Superpowers Adapter；
- 许可证和 NOTICE；
- 兼容性测试；
- Provider 失败回退。

退出条件：两个外部 Provider 能完成受控 L2 流程，且不能越过治理边界。

### 阶段 3：GitHub MCP 与 Evidence Bus

交付：

- GitHub MCP 可选依赖；
- GitHub API fallback；
- Evidence Envelope；
- Check、Review、artifact 验证；
- PR 人类摘要自动生成。

退出条件：机器门禁不再依赖 PR 作者手填测试和 QA 结果。

### 阶段 4：独立 verifier runtime

交付：

- 显式 verify 生命周期；
- Codex App Server/SDK Adapter；
- read-only verifier；
- run/thread identity；
- QA Check Run；
- head 更新自动失效。

退出条件：同一实现运行无法签发 QA PASS，独立 verifier 的身份和输入可审计。

### 阶段 5：Policy 与高级证明

交付：

- Policy Adapter；
- 可选 OPA Provider；
- L3 Approval Evidence；
- 可选 in-toto/Sigstore；
- OpenTelemetry 元数据追踪。

退出条件：L3 权限、批准、产物和发布路径具备可验证证明。

### 阶段 6：远程 Agent 生态

交付：

- A2A Provider；
- Agent Card 信任映射；
- 远程 Agent 身份、权限和证据转换；
- 跨框架兼容性测试。

退出条件：远程 Agent 不需要共享内部记忆，也能在受控权限下参与任务。

## 18. 迁移策略

### 18.1 Protocol 2.x 到 3.0

本方案涉及 Provider Manifest、verify 阶段、运行身份和 Evidence Envelope，建议升级为 Protocol 3.0，而不是在 2.x 内隐式改变语义。

迁移步骤：

1. 读取现有内置和外部 Skill 配置；
2. 把现有五个外部 Skill 名称转换成固定 Provider Manifest；
3. 生成 lock file；
4. 保留旧路由但输出弃用警告；
5. 为 L2/L3 启用新 `verify` 状态；
6. 将 PR 自报证据迁移为展示字段；
7. 新门禁开始读取 GitHub Check 和 Evidence Envelope；
8. 完成一次失败回滚演练；
9. 确认后提升 protocolVersion。

### 18.2 回滚

- 保留上一 Protocol 模板和迁移前配置备份；
- Provider Registry 可整体关闭并回退内置能力；
- 新 Evidence 字段只追加，不破坏旧 Issue/PR 正文；
- 迁移失败时不修改生命周期标签；
- 不自动删除现有 Skill 和 Plugin。

## 19. 运维与治理

### 19.1 Provider 维护流程

```text
提议 Provider
  → 安全与许可证审查
  → Manifest PR
  → 兼容性测试
  → 隔离试运行
  → allowlist
  → 固定版本发布
  → 定期健康检查
```

### 19.2 撤销

当发现 Provider 被入侵、许可证变化、行为漂移或严重缺陷时：

1. 将 Provider 标记 revoked；
2. 阻止新路由；
3. 查找使用该 Provider 产生的未合并证据；
4. 使相关 QA、审批或产物证明失效；
5. 回退内置 Provider 或 BLOCKED；
6. 发布安全公告和修复版本。

### 19.3 版本策略

- Provider Manifest schema 使用独立版本；
- Evidence Envelope 使用独立版本；
- Protocol 使用主版本表达语义变化；
- Provider 适配器遵循语义版本；
- lock file 固定精确版本和摘要。

## 20. 成功指标

### 20.1 安全与可信度

- 100% L2/L3 PASS 具有独立 verifier run；
- 100% QA 绑定当前 head SHA；
- 0 个未固定版本 Provider 参与生产路由；
- 0 个 PR 自报测试结果被当作机器真源；
- 所有治理绕过攻击测试稳定失败；
- 所有 L3 批准具有可追溯主体和适用范围。

### 20.2 可扩展性

- 新增一个 Skill Provider 不修改 Governance Core；
- 新增一个 MCP Provider 只需 Manifest、权限和 Adapter；
- 外部 Provider 故障时能明确回退或 BLOCKED；
- Provider 升级有兼容报告和一键回滚；
- 能在不复制上游仓库的情况下接入成熟能力。

### 20.3 工程质量

- Linux、Windows、macOS CI 通过；
- Provider 合同测试覆盖所有启用 Provider；
- Registry、Policy、Evidence 和 verifier 具备负向测试；
- 文档与真实运行行为由集成测试保持一致。

## 21. 风险与缓解

| 风险 | 影响 | 缓解 |
| --- | --- | --- |
| 架构过重 | 小项目使用成本上升 | L1 使用内置轻量模式 |
| Provider 数量过多 | 发现预算和维护失控 | allowlist、按需加载、场景路由 |
| 外部升级频繁 | 行为漂移 | 固定版本、兼容测试、人工升级 |
| MCP 权限过大 | 数据和账号风险 | 工具 allowlist、最小权限、审批 |
| verifier 成本增加 | 时延和费用增加 | L1 不强制，L2/L3按风险使用 |
| GitHub 不可用 | 证据链中断 | BLOCKED，不伪造离线 PASS |
| OPA 学习成本 | 维护复杂 | 先内置策略，后可选接入 |
| trace 泄露数据 | 隐私风险 | 只记录元数据、脱敏、保留策略 |
| 社区 Skill 许可证不清 | 法律风险 | 无明确许可证默认拒绝 |

## 22. 已确定决策

1. 采用 Provider Registry 与适配器，不整包复制外部生态。
2. Agents-Team Governance Core 保持唯一最终裁决权。
3. `openai/plugins` 和 Agent Skills 标准作为格式参考。
4. Addy Agent Skills 与 Superpowers 作为首批 Skill Provider。
5. GitHub MCP 与 Codex verifier runtime 为最高优先级集成。
6. 独立 QA 使用新线程、只读权限和当前 head Check Run。
7. OPA、in-toto、Sigstore、OpenTelemetry 和 A2A 分阶段启用。
8. 所有生产 Provider 固定版本和摘要，禁止自动追随 latest。
9. 旧名称匹配只保留一个迁移周期。
10. 该架构以 Protocol 3.0 发布，避免悄然改变 Protocol 2.0 语义。

## 23. Definition of Done

该架构完成必须同时满足：

- Provider Manifest、Registry、Trust Resolver 和 lock file 可运行；
- 内置 Provider 通过新 Registry 执行；
- Addy Agent Skills 与 Superpowers 完成兼容适配；
- GitHub 真实 Checks 取代 PR 自报测试真源；
- `qa-pending` 能创建全新 read-only verifier；
- QA Check 绑定 verifier identity、run ID 和 head SHA；
- head SHA 更新会自动撤销旧 review、QA 和 mergeable；
- L3 用户批准为可验证平台事件；
- 外部 Provider 不能获得 governance、qa signer 和 merge 权限；
- Provider 不可用时正确回退或 BLOCKED；
- 所有攻击、兼容性、跨平台和分发测试通过；
- 仓库自身启用必需 CI；
- 迁移、升级、撤销和回滚流程完成演练；
- README、使用指南、协议、Schema、NOTICE 和发布说明同步更新。

## 24. 参考资料

- Codex Agent Skills：<https://developers.openai.com/codex/skills>
- Codex Plugins：<https://developers.openai.com/codex/plugins>
- 构建 Codex Plugin：<https://developers.openai.com/codex/plugins/build>
- Codex MCP：<https://developers.openai.com/codex/mcp>
- Codex Subagents：<https://developers.openai.com/codex/subagents>
- Codex App Server：<https://developers.openai.com/codex/app-server>
- Codex SDK：<https://developers.openai.com/codex/sdk>
- Codex GitHub Action：<https://developers.openai.com/codex/github-action>
- OpenAI Plugins：<https://github.com/openai/plugins>
- Agent Skills 标准：<https://agentskills.io/specification>
- Addy Osmani Agent Skills：<https://github.com/addyosmani/agent-skills>
- Superpowers：<https://github.com/obra/superpowers>
- GitHub MCP Server：<https://github.com/github/github-mcp-server>
- Open Policy Agent：<https://github.com/open-policy-agent/opa>
- in-toto：<https://github.com/in-toto/in-toto>
- Sigstore Cosign：<https://github.com/sigstore/cosign>
- OpenTelemetry：<https://github.com/open-telemetry/opentelemetry-specification>
- A2A Protocol：<https://github.com/a2aproject/A2A>
- OpenAI Agents SDK：<https://github.com/openai/openai-agents-python>
- GitHub CodeQL Action：<https://github.com/github/codeql-action>
- Semgrep：<https://github.com/semgrep/semgrep>
- OSV-Scanner：<https://github.com/google/osv-scanner>
- Trivy：<https://github.com/aquasecurity/trivy>
- Gitleaks：<https://github.com/gitleaks/gitleaks>
