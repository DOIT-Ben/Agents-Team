# Agents-Team 仓库级 CI 设计

日期：2026-06-29  
状态：已确认

## Goal

为 Agents-Team 仓库本身建立可执行的 GitHub Actions CI，使每个 PR 在合并前都能证明：

1. 插件单元测试通过。
2. 分发包能够构建并在解包后自证。
3. PR 与关联 Goal Issue 符合团队协作契约。
4. 缺少权限、证据或必填契约时明确失败，不静默降级。

## 问题根因

当前 `plugins/agents-team/templates/project/collaboration-gate.yml` 是初始化到消费项目的模板，不位于仓库根目录 `.github/workflows/`，因此 Agents-Team 自身的 PR 不会触发任何 workflow。

## 方案

新增 `.github/workflows/ci.yml`，由仓库自身维护。

### 触发条件

- `pull_request`
- 推送到 `master`
- `workflow_dispatch`

### 权限

默认最小权限：

- `contents: read`
- `pull-requests: read`
- `issues: read`

不得授予写权限。

### 验证任务

#### Test and package

所有触发事件均执行：

1. Checkout 当前提交。
2. 设置仓库支持的 Python 版本。
3. 运行 `python3 -m unittest discover -s plugins/agents-team/tests -v`。
4. 运行 `python3 tools/build_distribution.py --output dist/agents-team-0.1.0.zip`。
5. 运行 `python3 tools/verify_distribution.py dist/agents-team-0.1.0.zip`。

任一步骤退出码非零，CI 失败。

#### Collaboration contract

仅 `pull_request` 执行：

```bash
python3 plugins/agents-team/templates/project/validate_pr_contract.py \
  --event "$GITHUB_EVENT_PATH" \
  --require-issue-lookup
```

PR 必须使用 `Closes/Fixes/Resolves #编号` 关联 Goal Issue。Issue 与 PR 必须满足当前模板契约。GitHub Token 或 Issue 读取权限缺失时失败，不降级通过。

## 首次自验证

1. 创建一个描述本次 CI Goal 的合规 Issue。
2. 在 `codex/repository-ci` 分支提交设计、workflow 及必要测试。
3. 创建符合模板的 PR并关联该 Issue。
4. 确认 GitHub 产生真实 workflow run。
5. CI 失败时读取日志、修复并重新运行。
6. 全部通过后合并。
7. 为 `master` 配置分支保护，要求仓库级 CI 通过后才能合并。

## 失败处理

- 无 workflow run：检查 Actions 是否启用、workflow 路径和 YAML 语法。
- 测试失败：保留失败日志，修复代码或测试，不绕过检查。
- 契约失败：补齐 Issue/PR 证据，不删除契约检查。
- 权限失败：修正 workflow 的只读权限，不改成宽泛写权限。
- 分发验证失败：禁止合并，直到解包验证通过。

## 边界

本任务不修改插件功能、品牌视觉和 README，不引入第三方依赖，不伪造历史 CI 结果，也不把消费项目专属配置直接复制为仓库配置。

## 验收标准

- PR 页面至少出现一次由新 workflow 产生的 run。
- 单元测试、分发构建、分发验证全部成功。
- PR/Issue 契约验证成功。
- 一个故意不合规的契约测试能够失败。
- `master` 合并后再次运行仓库级 CI。
