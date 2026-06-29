# Independent QA Contract

Output:

```markdown
## 验收结论
PASS / FAIL

## Goal 验证
Evidence for the observable end state.

## 必须完成项
Pass / fail / no evidence for each item.

## 测试门禁
Commands, exit codes, counts, unexpected skips.

## 行为验收
Real path, expected result, actual result.

## 任务边界
Violations or confirmation of none.

## 缺陷
P0 / P1 / P2 with reproduction and evidence.

## 未覆盖风险
Explicit gaps.
```

PASS requires all mandatory evidence, all gates green, no P0/P1, and no boundary violation. There is no “mostly PASS”.
