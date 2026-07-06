# 使用指南

## 初始化

在目标 Git 仓库中对 Codex 说：

> 初始化团队协作机制。

Codex 必须先扫描并展示 dry-run，包括技术栈、命令、新增文件、修改文件、冲突和无法确认事项。确认后才允许应用，并通过新分支和 Draft PR 交付。

命令行等价操作：

```bash
python PLUGIN_ROOT/scripts/initialize_project.py /path/to/project
python PLUGIN_ROOT/scripts/initialize_project.py /path/to/project --apply
python PLUGIN_ROOT/scripts/validate_project.py /path/to/project
```

### 首次安装 bootstrap

初始化后的首次 PR 必须按以下顺序执行：

1. 从完整仓库检出创建初始化分支，保留既有 `AGENTS.md` 和项目规则。
2. 创建完整 Goal Issue 和 Draft PR。
3. 将 PR 转为 Ready 后，再向同一分支推送一个经过审查的提交。
4. `synchronize` 事件核对 Issue、当前 head SHA、证据和独立 QA。
5. 缺少 Token、Issue 权限或证据时一律失败，不得降级通过。

bootstrap Gate 通过后才可考虑合并初始化 PR。
修正 PR 正文证据时不需要制造新提交；`edited` 事件会针对同一 head SHA 重新执行门禁，避免证据刚写入就因新提交失效。
PR 正文中的测试门禁字段只是可读摘要；生成的 Gate 会读取当前 head 的 GitHub Checks / workflow run 作为测试事实源。

## 执行 Goal

L2/L3 Issue 必须依次包含 Goal、必须完成、验收门禁、任务边界、风险等级、依赖与阻塞条件。

> 按照 Issue #123 执行团队目标。严格实现 Goal，完成全部必须完成项，通过验收门禁，严禁突破任务边界；不满足条件不得宣布完成。

PR 必须在 `Worker ownership` 区块声明允许修改的仓库相对路径，目录以 `/` 结尾。生成的 Gate 会读取 PR changed files，任何未被声明路径覆盖的文件变更都会 BLOCK，而不是 warning。
L2/L3 PR 还必须在 `Risk path classification` 区块为每个 changed file 声明路径分类，分类限 `standard`、`criticalPaths`、`protectedFiles`、`productionPaths`、`realProviderPaths`；缺失或未覆盖的 changed file 必须 BLOCK。L1 可保持轻量规则，不强制该分类。

L3 涉及数据、核心契约、权限、密钥、费用、真实 Provider 或生产环境，实施前必须暂停并请求用户确认。
L3 的正文确认只作为说明；PR Gate 还必须取得可审计的 `L3 approval event`，字段至少包含 `actor`、`timestamp`、`scope`、`risk: L3` 和当前 PR head 的 `commitSha`。无法接入平台事件时，可先用本地 JSON fixture 接入验证器，但不得把 Issue/PR 正文文本当作批准事件。

### 工程生命周期

`execute-team-goal` 会先调用 `route-team-work`，再根据当前状态选择：

```text
plan-team-goal -> build-team-goal -> review-team-goal -> ship-team-goal
                         |
                         -> debug-team-goal
```

每个工作角色只承担一种职责。主 Codex 是唯一整合者；角色不得继续调用其他角色，实现者不得签发独立 QA。

检测到兼容的外部工程 Skill 时可以选择使用，但 Agents-Team Protocol 2.0 始终优先。没有外部 Skill 时自动使用内置流程，不影响安装和执行。

## 独立验收

> 在未参与实现的全新上下文中独立验收 PR #45，只依据 Issue、最终差异和实际证据给出 PASS 或 FAIL。

没有独立上下文时不能伪造独立 QA。任何必须完成项无证据、指定测试失败、P0/P1 未解决或任务边界违规都必须 FAIL。

L2/L3 的 PR 必须记录可验证的 QA 证据：独立上下文、验收者、实现上下文、QA 上下文、QA 复核的当前 `commitSha`、PASS/FAIL/BLOCKED 结论和证据链接。QA 上下文必须与实现上下文不同，`commitSha` 必须等于当前 PR head。
L3 的批准事件同样必须绑定当前 head；事件缺失、字段缺失、风险不是 L3、时间戳无效或 `commitSha` 与当前 head 不一致时，Gate 必须失败。
生命周期标签顺序为 `status:draft -> status:ready -> status:in-progress -> status:implemented -> status:verifying -> status:pass|status:fail -> status:mergeable`；`status:pass` 必须由 verifier 在 QA 区块记录 `验证阶段：verify` 后才允许出现。

## 本地反馈导出

反馈导出默认只在 stdout 预览脱敏后的 JSON，不写文件、不上传、不创建 Issue：

```bash
python PLUGIN_ROOT/scripts/export_feedback.py feedback.json --output feedback-redacted.json
```

确认预览内容后，使用 `--apply` 才会写入本地导出文件：

```bash
python PLUGIN_ROOT/scripts/export_feedback.py feedback.json --output feedback-redacted.json --apply
```

## 提交反馈 Issue

在 Codex 中可以直接说：

> 提交反馈到 GitHub。

`submit-team-feedback` Skill 会收集用户允许发布的反馈事实、日志摘要和经验沉淀，生成 `Beta feedback` Issue 草稿。默认只预览，不提交：

```bash
python PLUGIN_ROOT/scripts/submit_feedback.py feedback.json
```

用户确认草稿安全后，才允许提交：

```bash
python PLUGIN_ROOT/scripts/submit_feedback.py feedback.json --apply
```

该命令默认提交到 `DOIT-Ben/Agents-Team`，依赖本机已安装并登录 GitHub CLI `gh`。如果 `gh` 不可用，复制预览草稿手动提交即可。

## 管理

```bash
python PLUGIN_ROOT/scripts/manage_project.py check /path/to/project
python PLUGIN_ROOT/scripts/manage_project.py repair /path/to/project
python PLUGIN_ROOT/scripts/manage_project.py upgrade /path/to/project
python PLUGIN_ROOT/scripts/manage_project.py remove /path/to/project
```

除 `check` 外，默认均只输出预览；使用 `--apply` 才写入。升级或移除前必须由用户确认。

## 已知边界

- Plugin 不自动创建 GitHub 仓库。
- 首次初始化必须从完整检出执行；对空目录或不完整投影执行初始化无法证明既有文件未被覆盖。
- GitHub 分支保护属于仓库设置，必须由有权限的用户或连接器配置。
- 自动扫描结果需要 Codex 判断；不能可靠识别的构建和测试命令必须询问用户。
- Plugin 不承诺单靠文字规则实现绝对服从；可机械约束由项目验证器和 CI 承担。
- Codex Plugin 不原生发现 Claude Code 风格的根目录 `agents/`；角色契约位于 `references/roles/`，由主 Skill 显式加载。
