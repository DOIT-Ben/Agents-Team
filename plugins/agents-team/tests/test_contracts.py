import sys
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from team_collaboration.contracts import extract_linked_issue, validate_issue_contract, validate_pr_contract  # noqa: E402


VALID_ISSUE = """### Goal
用户可以完成一次可观察的上传流程。

### 必须完成
- [ ] 上传成功并返回资源标识

### 验收门禁
命令：`python3 -m unittest`，退出码必须为 0。

### 任务边界
严禁修改认证、计费和生产部署配置。

### 风险等级
L2

### 依赖与阻塞条件
测试凭据可用，否则停止。

### 失败处理与回滚
失败时保留复现证据并回滚本 PR。
"""

VALID_PR = """## 关联任务
Closes #123

## 风险等级
L2

## 实际改动
实现上传客户端和错误处理。

## 范围偏差
无偏差。

## 必须完成项证据
- [x] 上传成功：测试 `test_upload_success`

## 测试门禁
- command: `python3 -m unittest`
  exitCode: 0
  passed: 12
  failed: 0
  skipped: 0

## 行为验收
预期：上传后返回资源标识。实际：返回 `asset-1`。

## QA 独立性与结论
独立上下文：是
结论：PASS

## 剩余风险
无已知剩余风险。

## 回滚方式
回滚本 PR。

## 失败记录
无。
"""


class ContractTests(unittest.TestCase):
    def test_valid_issue_contract_has_no_findings(self):
        self.assertEqual(validate_issue_contract(VALID_ISSUE), [])

    def test_missing_issue_section_returns_stable_code(self):
        findings = validate_issue_contract(VALID_ISSUE.replace("### 任务边界", "### 其他"))
        self.assertIn("AT-CONTRACT-001", [finding.code for finding in findings])

    def test_vague_boundary_is_rejected(self):
        findings = validate_issue_contract(VALID_ISSUE.replace("严禁修改认证、计费和生产部署配置。", "无"))
        self.assertIn("AT-CONTRACT-002", [finding.code for finding in findings])

    def test_l3_requires_user_decision(self):
        findings = validate_issue_contract(VALID_ISSUE.replace("L2", "L3"))
        self.assertIn("AT-CONTRACT-006", [finding.code for finding in findings])

    def test_extracts_linked_issue(self):
        self.assertEqual(extract_linked_issue(VALID_PR), 123)

    def test_valid_pr_contract_has_no_findings(self):
        self.assertEqual(validate_pr_contract(VALID_PR, VALID_ISSUE, ["risk:L2", "status:qa-pending"]), [])

    def test_pr_without_issue_link_is_blocked(self):
        findings = validate_pr_contract(VALID_PR.replace("Closes #123", "none"), VALID_ISSUE, ["risk:L2"])
        self.assertIn("AT-CONTRACT-003", [finding.code for finding in findings])

    def test_unchecked_mandatory_evidence_is_blocked(self):
        findings = validate_pr_contract(VALID_PR.replace("- [x] 上传成功", "- [ ] 上传成功"), VALID_ISSUE, ["risk:L2"])
        self.assertIn("AT-CONTRACT-004", [finding.code for finding in findings])

    def test_self_approved_qa_is_blocked(self):
        findings = validate_pr_contract(VALID_PR.replace("独立上下文：是", "独立上下文：否"), VALID_ISSUE, ["risk:L2"])
        self.assertIn("AT-QA-001", [finding.code for finding in findings])


if __name__ == "__main__":
    unittest.main()
