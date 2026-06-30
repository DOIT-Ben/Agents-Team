# 使用指南

命令示例使用 `python3`；Windows 环境可改用 `py -3`。

## 初始化

在目标 Git 仓库中对 Codex 说：

> 初始化团队协作机制。

Codex 必须先扫描并展示 dry-run，包括技术栈、命令、新增文件、修改文件、冲突和无法确认事项。确认后才允许应用，并通过新分支和 Draft PR 交付。

命令行等价操作：

```bash
python3 PLUGIN_ROOT/scripts/initialize_project.py /path/to/project
python3 PLUGIN_ROOT/scripts/initialize_project.py /path/to/project --apply
python3 PLUGIN_ROOT/scripts/validate_project.py /path/to/project
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

## 执行 Goal

L2/L3 Issue 必须依次包含 Goal、必须完成、验收门禁、任务边界、风险等级、依赖与阻塞条件。

> 按照 Issue #123 执行团队目标。严格实现 Goal，完成全部必须完成项，通过验收门禁，严禁突破任务边界；不满足条件不得宣布完成。

L3 涉及数据、核心契约、权限、密钥、费用、真实 Provider 或生产环境，实施前必须暂停并请求用户确认。

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

## 管理

```bash
python3 PLUGIN_ROOT/scripts/manage_project.py check /path/to/project
python3 PLUGIN_ROOT/scripts/manage_project.py repair /path/to/project
python3 PLUGIN_ROOT/scripts/manage_project.py upgrade /path/to/project
python3 PLUGIN_ROOT/scripts/manage_project.py remove /path/to/project
```

除 `check` 外，默认均只输出预览；使用 `--apply` 才写入。升级或移除前必须由用户确认。

## 本地记录与反馈

运行记录默认只保存在本机，14 天后自动清理。查看和删除均不依赖 GitHub：

```bash
python3 PLUGIN_ROOT/scripts/manage_project.py logs /path/to/project
python3 PLUGIN_ROOT/scripts/manage_project.py logs /path/to/project --run-id RUN_ID
python3 PLUGIN_ROOT/scripts/manage_project.py delete-logs /path/to/project --run-id RUN_ID
python3 PLUGIN_ROOT/scripts/manage_project.py delete-logs /path/to/project --run-id RUN_ID --apply
```

反馈必须先生成脱敏预览：

```bash
python3 PLUGIN_ROOT/scripts/manage_project.py feedback /path/to/project \
  --run-id RUN_ID --feedback-type bug --severity P2 \
  --expected-result "..." --actual-result "..." \
  --reproduction-steps "..."
```

用户检查预览后，添加 `--confirm` 才会在本地写出反馈包；只有用户另外要求时才添加 `--open-issue` 打开 GitHub 待提交页面。工具不会自动提交 Issue，也不会自动附件诊断 JSON。

离线 Beta 对照数据通过 `tools/evaluate_beta.py` 汇总。完整隐私边界和反馈字段见 [隐私说明](privacy.md) 与 [对照评测](evaluation.md)。

## 已知边界

- Plugin 不自动创建 GitHub 仓库。
- 首次初始化必须从完整检出执行；对空目录或不完整投影执行初始化无法证明既有文件未被覆盖。
- GitHub 分支保护属于仓库设置，必须由有权限的用户或连接器配置。
- 自动扫描结果需要 Codex 判断；不能可靠识别的构建和测试命令必须询问用户。
- Plugin 不承诺单靠文字规则实现绝对服从；可机械约束由项目验证器和 CI 承担。
- Codex Plugin 不原生发现 Claude Code 风格的根目录 `agents/`；角色契约位于 `references/roles/`，由主 Skill 显式加载。
