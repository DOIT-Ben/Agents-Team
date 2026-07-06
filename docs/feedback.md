# Feedback Guide

Agents-Team 的反馈闭环遵循一个原则：**先脱敏预览，再由用户决定是否提交**。不要上传你不愿公开的源码、日志、路径、仓库名、客户名、密钥或测试输出。

## 反馈入口

优先对 Codex 说：`提交反馈到 GitHub`。这会触发 `submit-team-feedback` Skill，把用户允许的本地片段、日志摘要或经验沉淀整理成 `Beta feedback` Issue 草稿。该 Skill 默认只预览，不上传、不创建 Issue；用户确认后才允许调用 `gh issue create`。

也可以手动使用 GitHub Issue 模板：`Beta feedback`。如果只需要整理本地反馈片段，可以先使用插件内置的本地反馈导出命令生成脱敏预览；该命令默认只输出到 stdout，不写文件、不上传、不创建 Issue。

反馈分为五类：

| 类型 | 例子 |
| --- | --- |
| 安装问题 | 插件安装失败、重启后不显示、manifest 识别异常 |
| 初始化问题 | dry-run 不清楚、识别错技术栈、模板冲突处理不好 |
| 执行问题 | Goal 读取不准、任务边界被扩大、路由阶段不合理 |
| 验收问题 | PR 证据不完整、独立 QA 无法判断、CI 门禁误报 |
| 隐私问题 | 不确定哪些日志能提交、脱敏结果不够清楚、反馈字段太敏感 |
| 体验问题 | 文档看不懂、提示太重、首次路径太长、错误信息不可操作 |

## 建议提交内容

| 字段 | 是否必需 | 说明 |
| --- | --- | --- |
| 插件版本 | 必需 | 例如 `0.3.0` |
| Codex 环境 | 必需 | CLI、插件、操作系统和大致版本 |
| 项目类型 | 必需 | Python、Next.js、.NET、Monorepo 等 |
| 试用阶段 | 必需 | 安装、初始化、执行 Goal、独立 QA、CI、发布 |
| 期望行为 | 必需 | 你希望 Agents-Team 怎么处理 |
| 实际行为 | 必需 | 实际发生了什么 |
| 可复现步骤 | 推荐 | 尽量用脱敏命令和描述 |
| 脱敏日志 | 可选 | 只提交你确认可公开的片段 |

## 不要提交

- 密钥、token、cookie、账号、私有邮箱。
- 未脱敏的客户名、项目代号、仓库私有 URL。
- 完整源码、完整测试日志、完整 CI artifact。
- 任何你不希望出现在公开 GitHub Issue 中的信息。

## 本地反馈导出原则

内置反馈导出必须遵守：

1. 默认只在 stdout 预览脱敏 JSON。
2. 默认不写文件、不上传、不创建 Issue。
3. 使用 `--apply` 才写入本地脱敏文件。
4. 用户明确确认后才提交到 GitHub Issue 或其他渠道。
5. 用户可以删减任意片段。

命令示例见 [usage.md#本地反馈导出](usage.md#本地反馈导出)。

## 本地反馈导出示例

默认只预览，不写文件：

```bash
python PLUGIN_ROOT/scripts/export_feedback.py feedback.json --output feedback-redacted.json
```

确认预览无敏感信息后，才写入本地脱敏文件：

```bash
python PLUGIN_ROOT/scripts/export_feedback.py feedback.json --output feedback-redacted.json --apply
```

## 一句话提交反馈

对 Codex 说：

```text
提交反馈到 GitHub：初始化 dry-run 把 Python 项目识别成 Node 项目，期望能识别 pytest，实际给了 npm test。
```

Skill 应先生成 Issue 草稿并等待确认。命令行等价操作：

```bash
python PLUGIN_ROOT/scripts/submit_feedback.py feedback.json
```

确认草稿安全后，才提交到默认仓库 `DOIT-Ben/Agents-Team`：

```bash
python PLUGIN_ROOT/scripts/submit_feedback.py feedback.json --apply
```

提交依赖本机已安装并登录 GitHub CLI `gh`。如果 `gh` 不可用，请复制预览草稿，手动提交到 `Beta feedback` Issue 模板。

## 高质量反馈示例

```text
插件版本: 0.3.0
环境: Windows, Codex Plugin
项目类型: Next.js monorepo
阶段: 初始化 dry-run
期望行为: 识别 pnpm test:unit 作为最小验证命令
实际行为: dry-run 只识别到 npm test，且没有提示 monorepo workspace
复现步骤: 在仓库根目录执行“初始化团队协作机制”，查看 dry-run 的 commands 部分
脱敏日志: 已附 dry-run commands 片段，无源码
```
