# Agents-Team Engineering Skills Integration Design

状态：Approved
日期：2026-06-30
上游参考：`addyosmani/agent-skills`
适用版本：Agents-Team Protocol 2.0+

## 1. Goal

在不改变 Agents-Team 治理定位的前提下，选择性吸收成熟的工程生命周期、Skill 路由和专业角色设计，使 Agents-Team 同时具备：

- Goal 驱动、风险分级、任务边界和独立 QA。
- 从计划、实现、调试、审查到交付的完整工程执行能力。
- 可追踪、可阻断、可定位根因的真实性门禁。
- 不依赖外部 Skill 仓库也能独立安装和运行的最低能力集。

本设计吸收方法和结构，不完整复制上游 24 个 Skill，也不把 Agents-Team 改造成通用 Skill 集市。

## 2. 定位与边界

Agents-Team 继续作为治理与交付层：决定任务为什么做、谁可以做、允许改什么、何时必须暂停，以及用什么证据才能完成。

工程能力层负责如何把代码做好：规划、增量实现、测试驱动、系统调试、代码审查、安全审查和交付检查。

两层遵循以下优先级：

```text
Goal 合同与风险规则
    > Agents-Team 路由与角色边界
    > 工程 Skill 的局部流程
    > 外部兼容 Skill 的建议
```

外部 Skill 不得绕过 Issue 合同、风险分级、受保护路径、用户确认、独立 QA 或 CI 门禁。

## 3. 分层架构

### 3.1 治理层

沿用现有四个核心 Skill：

- `initialize-team-collaboration`
- `execute-team-goal`
- `verify-team-goal`
- `manage-team-collaboration`

沿用 Protocol 2.0 的合同、状态机、证据、诊断、Doctor、版本迁移和 fail-closed 规则。

### 3.2 路由层

新增 `route-team-work`，根据 Goal 状态、任务意图、风险等级和当前失败类型选择工程 Skill。路由只负责编排，不实现业务代码，也不代替独立 QA。

路由结果至少包含：

- 当前阶段。
- 选中的 Skill。
- 选中的角色。
- 风险等级及依据。
- 允许和禁止的文件范围。
- 前置门禁与完成条件。
- 是否允许并行。

### 3.3 工程能力层

首轮新增六项精简能力：

| Skill | 责任 | 退出条件 |
| --- | --- | --- |
| `route-team-work` | 识别阶段并选择流程 | 路由决策完整且没有合同阻塞 |
| `plan-team-goal` | 拆分任务、依赖和验收条件 | 每项任务可独立验证且边界明确 |
| `build-team-goal` | 按小批次增量实现 | 实现证据齐全，未越界，不自我验收 |
| `debug-team-goal` | 复现、定位、缩小、修复、回归 | 根因与回归证据完整 |
| `review-team-goal` | 审查正确性、测试、安全和范围 | 所有阻断项关闭或明确 FAIL |
| `ship-team-goal` | 检查 CI、风险、回滚和发布条件 | 当前提交满足交付合同 |

`execute-team-goal` 是总调度入口。它读取 Issue 和项目配置、完成风险定级，再调用路由层和工程能力层。

### 3.4 角色层

Codex Plugin 当前不原生发现 Claude Code 风格的 `agents/` 目录，因此角色以 `references/roles/*.md` 契约交付。主 Skill 创建子智能体时必须读取对应契约，并把角色职责、允许范围、禁止事项和输出格式显式注入任务。

| 角色 | 单一职责 | 明确禁止 |
| --- | --- | --- |
| `goal-planner` | 拆分任务与依赖 | 修改业务代码 |
| `implementation-worker` | 在授权范围内实现 | 宣布整个 Goal 完成 |
| `test-engineer` | 设计测试、复现和检查缺口 | 隐藏失败或替实现者批准 |
| `code-reviewer` | 检查正确性、复杂度和范围 | 审批自己的实现 |
| `security-auditor` | 检查权限、密钥、输入和依赖风险 | 扩张为无边界通用审查 |
| `independent-verifier` | 依据合同和证据给出 PASS/FAIL | 参与被验收实现 |

主 Codex 是唯一整合者。角色不能调用其他角色；需要组合时由主 Codex 扁平调度。

## 4. 风险与调度规则

### L1

主 Codex 可直接实现、测试和自证。若任务触及用户功能、跨模块契约或当前项目配置要求更严格，则升级为 L2。

### L2

执行顺序为：规划、实现、测试或调试、审查、独立 QA。必须关联 Goal Issue 和 PR，不允许实现上下文自签 QA。

### L3

执行顺序为：方案与用户确认、专项实现、测试、安全审查、代码审查、独立 QA、用户或发布负责人确认。成本、密钥、真实 Provider、不可逆影响和回滚必须进入证据合同。

### 并行条件

只有同时满足以下条件才能并行：

- 子任务相互独立。
- 文件所有权不重叠。
- 输入和输出合同稳定。
- 测试可独立运行。
- 合并顺序不影响语义。

不满足任一条件时必须串行。不得建立角色调用角色的多层树。

## 5. 真实性门禁

工程能力接入现有 `contracts.py`、`evidence.py`、`lifecycle.py`、`diagnostics.py` 和 `doctor.py`，不新建平行证据体系。

最低证据要求：

- 自动化测试记录准确命令、退出码、通过/失败/跳过数量、执行时间和提交 SHA。
- CI 运行必须对应当前 PR head commit。
- 人工行为验收记录入口、步骤、预期、实际和证据位置。
- L2/L3 记录 QA 执行上下文和独立性声明。
- L3 记录方案确认、成本、密钥处理、真实 Provider smoke 和回滚。
- 权限、Token、CI 或真实环境缺失时返回 `BLOCKED` 或 `FAIL`，不得降级为通过。

新增诊断沿用 Protocol 2.0 的稳定失败码体系。每个失败必须包含位置、原因、修复动作和证据位置。

## 6. 目录结构

```text
plugins/agents-team/
├── skills/
│   ├── route-team-work/
│   ├── plan-team-goal/
│   ├── build-team-goal/
│   ├── debug-team-goal/
│   ├── review-team-goal/
│   └── ship-team-goal/
├── references/
│   ├── skill-routing.md
│   ├── orchestration-rules.md
│   └── roles/
│       ├── goal-planner.md
│       ├── implementation-worker.md
│       ├── test-engineer.md
│       ├── code-reviewer.md
│       ├── security-auditor.md
│       └── independent-verifier.md
└── scripts/team_collaboration/
    ├── routing.py
    ├── contracts.py
    ├── evidence.py
    ├── lifecycle.py
    ├── diagnostics.py
    └── doctor.py
```

每个 Skill 必须包含触发条件、前置门禁、执行步骤、禁止事项、退出条件和证据要求。结构验证器必须检查名称、描述、必要章节和失效交叉引用。

## 7. 外部 Skill 兼容

Agents-Team 默认独立运行，不要求安装 `addyosmani/agent-skills`。

检测到外部同类 Skill 时，可以将其作为工程执行提供者，但必须满足：

- 路由结果明确记录实际使用的 Skill 和版本或来源。
- Agents-Team 合同和风险规则始终优先。
- 外部 Skill 的验证结论必须转换为 Agents-Team 证据模型。
- 外部 Skill 不可用或不兼容时回退到内置流程，不得导致核心机制失效。

首轮只定义兼容接口，不实现自动下载、自动更新或跨仓库代码同步。

## 8. 来源与许可

新增 `NOTICE.md`，说明参考了 `addyosmani/agent-skills` 的生命周期、元 Skill、单一职责 Persona、扁平编排、渐进披露和反逃避设计。

原则：

- 优先重新实现思想，不复制具体文本。
- 直接采用或修改 MIT 许可内容时保留原版权和许可声明。
- 不使用 Google 官方项目名义宣传本项目。
- 上游更新只通过人工审查吸收，不自动覆盖本地流程。

## 9. 测试策略

### 单元测试

- 六项 Skill 的结构、触发和交叉引用。
- 六份角色契约可被 Skill 定位，并包含职责、权限、禁止事项和输出格式。
- 路由决策、风险升级和阶段识别。
- 角色权限、禁止行为和独立性判定。
- 证据到 Protocol 2.0 模型的转换。

### 负向测试

- 子智能体越权修改文件。
- 实现者自签 QA。
- 多层角色调用。
- 测试证据缺命令、退出码、时间或提交 SHA。
- CI 属于旧提交。
- 缺少权限时错误降级为 PASS。

### 集成测试

- L1、L2、L3 完整生命周期。
- Protocol 1.0 到 2.0 的迁移后路由。
- 内置工程流程和外部兼容提供者两种路径。
- 分发包解压后的 Skill、角色、脚本和引用完整性。

### 真实试运行

选择一个小型真实仓库，完成：

1. 外部安装 Agents-Team。
2. 初始化或升级 Protocol 2.0。
3. 创建一个 L2 Goal Issue。
4. 故意提交缺失证据的 PR 并确认 Gate 阻断。
5. 补齐真实证据并确认 Gate 通过。
6. 完成独立 QA、合并和回滚演练。

没有完成真实试运行前，不得宣称工程能力融合已经达到交付级或完全即插即用。

## 10. 非目标

- 不引入完整的 24 Skill 副本。
- 不把 Agents-Team 变成 Claude Code 或 Gemini CLI 的镜像插件。
- 不自动执行生产发布、付费操作或数据迁移。
- 不允许角色自由扩权或深层递归调度。
- 不用 Markdown 台账替代 GitHub Issue、PR 和 Check 真源。
- 不在本轮重写 Protocol 2.0 的合同、证据、诊断和生命周期模块。

## 11. Definition of Done

- 六项工程 Skill、六份角色契约和路由模块通过结构及行为测试。
- `execute-team-goal` 能在 L1/L2/L3 下选择正确流程。
- Protocol 2.0 仍是唯一合同、证据、诊断和状态模型。
- 外部 Skill 不存在时，插件仍能完整运行。
- 所有硬门禁保持 fail-closed，且失败可定位和修复。
- 分发包端到端验证通过。
- 至少一个真实仓库完成失败阻断、修复通过和独立 QA 闭环。
- README、使用指南、变更日志、NOTICE 和迁移说明同步更新。
