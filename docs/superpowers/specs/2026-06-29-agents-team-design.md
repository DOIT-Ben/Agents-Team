# Agents-Team Plugin Design

状态：Approved
日期：2026-06-29
目标用户：单一项目负责人 + 主 Codex + 按需子智能体
适用范围：需要长任务、系统开发、跨模块协作、独立验收和持续迭代的 GitHub 项目

## 1. Goal

构建一个跨项目复用的 `agents-team` Plugin。用户在任意 GitHub 项目中说“初始化团队协作机制”后，Codex 能安全扫描项目、生成项目级协作适配层，并在后续任务中自动使用 Goal、必须完成、验收门禁、任务边界、风险分级、独立 QA 和 GitHub Issue/PR 真源机制。

## 2. 核心架构

- 通用 Plugin 保存完整协议、Skills、脚本、模板和版本迁移。
- 项目级 `AGENTS.md` 保存精简入口和项目特有规则。
- `.codex/team-collaboration.json` 保存结构化项目画像与机制版本。
- GitHub Issue 保存 Goal、必须完成、验收门禁和任务边界。
- Pull Request 保存实际改动、验证证据、QA 结论和剩余风险。
- CI 负责可机械执行的硬门禁；独立 QA 负责语义和行为验收。

## 3. Plugin 组成

Plugin 提供四个 Skill：

1. `initialize-team-collaboration`：初始化、接入或修复项目机制。
2. `execute-team-goal`：读取 Goal Issue，定级并组织实现。
3. `verify-team-goal`：由未参与实现的上下文执行独立验收。
4. `manage-team-collaboration`：检查、升级、修复或移除机制。

Plugin 提供确定性脚本：

- 项目扫描。
- 配置与模板渲染。
- JSON Schema 和受控区块校验。
- 机制版本检测。
- 受控文件哈希与升级漂移检查。

## 4. 初始化行为

初始化器支持 `initialize`、`adopt`、`upgrade`、`repair` 四种模式。默认先执行只读扫描和 dry-run，用户确认后才写文件。

生成的项目层包含：

```text
AGENTS.md
.codex/team-collaboration.json
.codex/schemas/team-collaboration.schema.json
.codex/scripts/validate_team_collaboration.py
.github/ISSUE_TEMPLATE/team-goal.yml
.github/ISSUE_TEMPLATE/critical-goal.yml
.github/pull_request_template.md
.github/workflows/collaboration-gate.yml
docs/adr/README.md
```

已有 `AGENTS.md` 时只维护：

```markdown
<!-- TEAM-COLLABORATION:START protocol=1.0.0 -->
...
<!-- TEAM-COLLABORATION:END -->
```

不得覆盖区块外内容。已有 GitHub 模板和业务 CI 不得删除。

## 5. 任务协议

### L1

局部、可逆、不触及数据、契约、权限、真实 Provider、生产环境和核心用户流程。可直接通过 PR 执行，不强制 Issue。

### L2

用户功能、跨模块联动、兼容 API、重试/上传/下载行为或需要浏览器 E2E 的任务。必须使用 Issue、PR 和独立 QA。

### L3

数据迁移、状态机、核心契约、权限、密钥、付费 Provider、部署、产品红线或不可逆操作。实施前必须请求用户确认，实施后必须独立复核和 QA。

Issue 必须按顺序包含：

1. Goal。
2. 必须完成。
3. 验收门禁。
4. 任务边界。
5. 风险等级。
6. 依赖与阻塞条件。

任意必须完成项没有证据、指定测试失败、行为验收失败或任务边界被突破时，不得判定 PASS。

## 6. 自动读取与强制层

- Plugin 的 Skill metadata 让 Codex 能发现初始化、执行、验收和管理工作流。
- 项目级 `AGENTS.md` 让 Codex 每次进入仓库时获得持久项目规则。
- 项目配置让脚本和 Skill 使用同一项目画像。
- GitHub Issue/PR 模板阻止需求字段缺失。
- 项目内验证器和 CI 检查结构、版本和模板契约。
- SessionStart Hook 只读检测是否初始化或版本过期，不得静默写文件。

## 7. 版本兼容

分别管理 Plugin Version、Protocol Version 和 Config Schema Version。项目独立锁定协议版本；Plugin 升级不得静默传播到所有项目。

- Patch：修复，不改变语义。
- Minor：兼容新增，通过 Draft PR 升级。
- Major：不兼容变化，必须提供迁移方案并由用户确认。

受控文件记录哈希。发现人工修改时停止覆盖，要求用户选择保留、恢复或转换为配置覆盖。

## 8. 安全边界

- 不直接推送默认分支。
- 不静默覆盖已有规则、CI 或模板。
- 不读取或打印密钥内容。
- 不跟随危险符号链接写出仓库。
- 不允许路径穿越。
- 写入采用 staged tree，验证成功后再原子应用。
- 真实付费 Provider、数据迁移和生产发布必须显式确认。

## 9. 测试策略

自动化测试覆盖：

- Python/FastAPI、Next.js、.NET、Monorepo 夹具。
- 已有 AGENTS、已有 CI、旧机制、脏工作区。
- 初始化、重复初始化、接入、修复、升级和移除。
- Windows 与 POSIX 路径。
- 配置损坏、区块漂移、路径穿越和符号链接。
- Skill 与 Plugin 结构校验。
- L1/L2/L3 前向行为场景。

正式 1.0.0 前必须在至少三个不同类型的真实项目上通过 Draft PR 试运行。

## 10. 设计边界

- 不模拟固定的前端、后端、测试或架构师席位。
- 不保存 Markdown 动态任务台账。
- 不要求所有小任务建立 Issue。
- 不把付费 Provider 加入普通 CI。
- 不在初始化阶段修改业务代码或生产环境。
- 不承诺单靠文字规则实现百分之百服从；可机械规则必须用脚本和 CI 强制。

## 11. Definition of Done

- Plugin manifest、四个 Skill、脚本、模板、Hook、测试和文档完整。
- 初始化器可在夹具项目中安全 dry-run 和 apply。
- 重复初始化幂等。
- 既有 `AGENTS.md` 区块外内容不变。
- 生成项目可在没有 Plugin 的情况下运行最小验证器。
- Skill 和 Plugin 验证器全部通过。
- 安全负面测试通过。
- 提供可安装的 ZIP 包和独立 Git 仓库。
