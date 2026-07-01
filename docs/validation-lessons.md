# Agents-Team 验证复盘

本文记录 Agents-Team 在真实仓库验证中暴露出的可复用机制问题。它不是完整验证台账；具体任务状态仍以目标仓库的 Issue、Pull Request、CI 和 Gate 记录为准。

## 发现的问题

### 1. Ready Gate 必须监听 ready_for_review

#### 现象

接入验证中出现过 Draft 阶段 Gate 已通过，但 Draft 转 Ready 后未必触发新 Gate 的风险。

#### 根因

GitHub Actions 的 `pull_request` 默认 activity types 不覆盖完整 PR 生命周期。Draft 转 Ready 属于 `ready_for_review`，需要显式写入 workflow。

#### 修复

在 Collaboration Gate workflow 中使用：

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:
```

如果目标仓库使用 managed hash，也要同步更新 `.codex/team-collaboration.json`。

#### 复用规则

- Draft 阶段 Gate 不能替代 Ready 后 Gate。
- 转 Ready 后必须看到新的 Gate run。
- 新仓库接入时必须检查 `ready_for_review` 触发路径。

### 2. 治理接入 PR 会被既有 CI baseline 阻塞

#### 现象

治理接入 PR 只修改治理文件，但目标仓库主 CI 仍可能失败。

#### 根因

失败可能来自接入前已经存在的格式化、测试或构建基线问题，不一定由治理文件导致。治理安装 Goal 通常禁止修改产品代码，因此不能在同一个 PR 中顺手修业务基线。

#### 修复

先开前置 Goal 修复主 CI baseline，再从干净默认分支重建治理接入 PR。

#### 复用规则

- 接入前先检查默认分支 CI 是否绿色。
- 如果默认分支 CI 已红，先开前置 Goal 修基线。
- 治理安装 PR 只改治理文件，避免混入产品代码。
- 旧 PR 如果携带阻塞历史，优先关闭并从干净默认分支重建。

### 3. PR 正文是 Gate 输入，不是说明文字

#### 现象

实现和 CI 都可能已经满足要求，但 Ready Gate 仍因 PR 正文字段不完整而失败。

#### 根因

PR 正文不是普通说明文字，而是治理 Gate 的输入。缺少固定段落、证据字段、风险记录或 QA 结论时，机械检查会失败。

#### 修复

参照目标仓库模板补齐关联任务、风险等级、实际改动、QA 独立性与结论、失败记录和 Gate 证据。

#### 复用规则

- PR 正文必须按目标仓库模板写。
- 失败记录要保留，不要只写最终成功。
- 独立 QA 结论必须可追溯，不能由实现者代签。

## 新仓库接入前检查清单

- 默认分支和目标分支明确。
- 主 CI 最近一次为绿色；如果不是，先开前置 Goal。
- 已识别允许修改范围和禁止修改范围。
- 已确认现有 Issue / PR 模板如何保留。
- Collaboration Gate workflow 覆盖 `ready_for_review`。
- PR 正文模板包含固定证据段。
- 计划中有独立 QA，不由实现者代签。

## 后续验证建议

治理适配器接入成功后，应继续跑一个小范围真实 L2 Goal。这样才能验证机制不仅能安装，还能稳定管理后续产品迭代。
