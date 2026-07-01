# 独立评审：验收独立性缺口复核

日期：2026-07-02
评审人：外部独立评审（未参与本仓库任何实现提交）
评审范围：`plugins/agents-team` 的路由、生命周期、评估、契约校验代码，以及历史审计文档与 PR 讨论

## 结论摘要

Agents-Team 的契约结构、初始化非破坏性设计、CI 证据格式校验是扎实的工程实现,可以直接使用。但机制标榜的"独立 QA""L2/L3 需要独立验收"这一核心承诺,目前在代码层面不成立——它仍然是可以被同一实现主体自我签署的文本声明。这不是新发现,项目自己在 `2026-06-30-collaboration-mechanism-audit.md`（已随 PR #4 关闭,未合并进 `master`）中详细诊断过完全相同的问题,仓库维护者本人在该 PR 的评论中也确认了诊断成立。本文的目的是核实这三条 P1 结论在当前 `master`（`bdbe5e6`）上是否已修复——核实结果是：**没有修复**,只是诊断文档被替换成了更轻量的 `docs/validation-lessons.md`,而后者不包含这三条架构缺陷。

## 复核方法

1. 逐个 `git log -- <file>` 检查 `routing.py`、`lifecycle.py`、`contracts.py`、`evidence.py` 自 `e6d4172`（引入工程生命周期路由,2026-06-29）之后是否有过修复性提交。结果：无。这两个文件自那次提交后再未被改动。
2. 通读 `templates/project/validate_pr_contract.py`（生成到目标仓库、在 CI 中实际运行的门禁）,确认它检查的是文本模式匹配,而不是执行者身份。
3. 通过 `gh pr view/list` 核实 PR #4（原始诊断)的处置结果：Draft、未合并、于 2026-07-01 以"superseded / close without merge"关闭,关闭理由是"有用的经验已经沉淀进 #9 合并的 `docs/validation-lessons.md`"。
4. 通读 `docs/validation-lessons.md`,确认其内容是"Ready Gate 要监听 `ready_for_review`""PR 正文是 Gate 输入""接入 PR 别混入业务代码"三条**流程性经验**,不包含身份绑定、commit 绑定、verify 阶段路由这三条**架构性缺陷**。

## 复核发现（均为现存,未修复）

### 1. `qa-pending -> pass` 之间没有强制的独立验收动作

`scripts/team_collaboration/routing.py` 的 `STATE_PHASE` 把 `qa-pending` 映射到 `review` 阶段（`code-reviewer` 角色),把 `pass`/`mergeable` 映射到 `ship` 阶段（`independent-verifier` 角色)。产生 PASS 结论的 `verify-team-goal` 本身不在 `ROUTES` 或 `STATE_PHASE` 任何一个状态的映射目标里,只能靠主 Codex 依照 `SKILL.md` 文字说明"记得"手动调用。

后果：状态机允许从 `qa-pending` 直接被标记为 `pass`,而不经过任何代码路径上的 verifier 调用。校验落在 `validate_pr_contract.py:83-91`,而它检查的只是 PR 正文里是否出现 `独立上下文：是` 和 `结论：PASS` 这两行文字模式。同一个实现会话可以自己写这两行,门禁会通过。

维护者本人在 PR #4 的评论中确认了这一点："现有机制没有从代码层面保证独立性,只是文字模式匹配"。

### 2. QA 结论没有绑定 head SHA

`evidence.py` 里 `validate_gate_evidence` 会校验测试证据的 `commitSha` 是否等于 `current_sha`（`AT-GATE-005`),这一层是做对的。但 `validate_qa_evidence`（`evidence.py:70-78`)只检查 `independent` 是否为 `True`、`verdict` 是否为 `"PASS"`,没有任何字段记录这个结论是在哪个 commit 上做出的。

`templates/project/validate_pr_contract.py` 同理：它把测试证据的 `commitSha` 与 `head.sha` 比对,但 QA 区块（`独立上下文` / `结论`)完全不参与这个比对。也就是说,代码在 QA PASS 之后被修改,只要重新填一遍测试证据的 `commitSha`,旧的 QA 文本可以原样保留并通过门禁。

### 3. L3 用户确认可以被实现者代写

`contracts.py:67-68` 对 L3 Issue 的校验只检查"L3 方案与用户确认"这个章节是否非空、且不是"待定"之类的占位符。它不检查这段文字的作者、时间,也不要求任何 GitHub 平台事件（如 Reviewer Approval、Environment 人工批准)。实现者可以在 Issue 正文里自己写一句"用户已确认",校验器无法分辨真伪。

## 与既有材料的关系

这三条不是我的新发现,而是对项目自身诊断的复核确认。区别在于：

- PR #4（`docs: 新增协作机制审查报告`)完整记录了这三条,状态是 **Draft、未合并、已关闭**。
- 关闭理由（DOIT-Ben 本人评论)称有用经验已沉淀进 `docs/validation-lessons.md`（经 PR #9 合并),但后者只覆盖"Ready Gate 事件覆盖""PR 正文是 Gate 输入""接入 PR 范围"三条流程问题,**不包含**身份绑定、commit-QA 绑定、verify 阶段路由这三条架构缺陷。
- 从 `bc7a9c5`（CI workflow)到 `bdbe5e6`（enforcement 深度校验)的十余个后续提交,没有一个触碰 `routing.py`、`lifecycle.py`,或给 QA 证据加上身份/commit 绑定字段。

换言之：诊断被写下、被维护者认可,随后连同解决方案一起被关闭,只留下了不涉及架构修复的经验总结。**这个缺口目前处于"已知但未修复,且未跟踪"的状态**——没有对应的开放 Issue。

## 建议

1. **重开一个明确聚焦架构缺口的 Issue**,而不是把它当作已经被 `docs/validation-lessons.md` 覆盖的问题。建议标题类似"独立 QA 缺少身份与提交绑定"，Goal 直接写：verifier 的结论必须绑定到产生该结论时的 head SHA 与执行者身份,身份和实现者不能相同。
2. **最小可行修复,不需要一次到位**：
   - 给 QA 区块加一个 `commitSha` 字段,`validate_pr_contract.py` 用现成的比对逻辑（已经给测试证据实现过一次）复用到 QA 区块上，head 变化后旧 QA 自动失效。这是本仓库现有代码模式的直接复用，成本很低。
   - 在 `STATE_PHASE` 里插入显式的 `qa-pending -> verify -> pass` 中间态，让 `route_work` 在 `qa-pending` 时确定性返回 `verify-team-goal`，而不是依赖文档说明。
   - 对 L3 确认，最低成本方案是要求确认文本包含用户 GitHub 账号的 `@mention` 加时间戳，或改为要求一条独立于实现 PR 的 Issue 评论（评论作者字段在 GitHub API 里是不可由 PR 作者伪造的），而不必一步做到 Environment 审批。
3. **在 README/docs/usage.md 里明确降级此项能力的措辞**：目前 README 写"没有真正独立的验收上下文就不能伪造独立 QA"，这条陈述描述的是意图而非当前实现状态，容易让新接入者误以为机制已经强制了这一点。建议在修复前明确注明"当前独立性依赖协作者自律，尚未有平台级强制"。

## 复核范围之外

本文没有验证 Checks API 集成、worker 文件边界的机器强制、并行任务冲突处理——这些在原始审计文档里同样列为未解决项，本次复核只聚焦"独立 QA"这一条，因为它是机制对外承诺的核心价值主张。
