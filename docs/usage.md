# 使用指南

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

## 执行 Goal

L2/L3 Issue 必须依次包含 Goal、必须完成、验收门禁、任务边界、风险等级、依赖与阻塞条件。

> 按照 Issue #123 执行团队目标。严格实现 Goal，完成全部必须完成项，通过验收门禁，严禁突破任务边界；不满足条件不得宣布完成。

L3 涉及数据、核心契约、权限、密钥、费用、真实 Provider 或生产环境，实施前必须暂停并请求用户确认。

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

## 已知边界

- Plugin 不自动创建 GitHub 仓库。
- GitHub 分支保护属于仓库设置，必须由有权限的用户或连接器配置。
- 自动扫描结果需要 Codex 判断；不能可靠识别的构建和测试命令必须询问用户。
- Plugin 不承诺单靠文字规则实现绝对服从；可机械约束由项目验证器和 CI 承担。
