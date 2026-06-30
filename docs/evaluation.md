# Beta 对照评测

评测采用配对任务：相近复杂度的任务分别通过普通单智能体流程和 Agents-Team 完成，两种结果都交给没有参与实现、不了解实现推理的独立上下文验收。

本地数据使用 `plugins/agents-team/references/beta-evaluation.schema.json`，离线运行：

```powershell
py -3 tools/evaluate_beta.py .\beta-dataset.json --output .\beta-report.json
```

可从 `release/beta-dataset.example.json` 复制结构。`cohortId` 只使用邀请编号，不填写姓名、邮箱或 GitHub 账号。

进入稳定版需要同时满足：20 名有效测试者、100 次真实运行、40 组配对任务、安装/升级/回滚成功率至少 95%、诊断复现率至少 85%、上下文隔离违规为 0、无未解决的 P0/P1 隐私或数据破坏问题。

效果门槛为验证后成功率至少提高 **15 个百分点**，或缺陷逃逸率至少下降 **30%**。耗时和成本不能同时增长超过 50%；再次使用意愿至少 70%，平均评分至少 4/5。

样本用于产品决策，不宣称统计学显著性。每个确认缺陷必须关联回归用例、修复版本、验证证据和原反馈者回访结果。
