import unittest

from app.services.novel_agent_service import NovelAgentService


class AuditReportTest(unittest.TestCase):
    def test_normalize_audit_report_keeps_and_infers_location(self):
        draft = "第一段没有问题。\n\n第二段有突兀跳转和解释腔。\n\n第三段结束。"
        raw = {
            "issues": [
                {
                    "type": "pacing",
                    "severity": "medium",
                    "description": "转场突兀",
                    "evidenceText": "第二段有突兀跳转和解释腔",
                }
            ],
            "summary": "需要修",
            "should_revise": True,
        }

        result = NovelAgentService._normalize_audit_report(raw, draft)
        issue = result["issues"][0]

        self.assertTrue(result["shouldRevise"])
        self.assertEqual(issue["paragraphIndex"], 2)
        self.assertGreaterEqual(issue["startOffset"], 0)
        self.assertGreater(issue["endOffset"], issue["startOffset"])

    def test_normalize_audit_report_tolerates_missing_location(self):
        result = NovelAgentService._normalize_audit_report({"issues": [{"description": "泛泛问题"}]}, "正文")
        self.assertEqual(result["issues"][0]["paragraphIndex"], None)
        self.assertEqual(result["issues"][0]["evidenceText"], "")


if __name__ == "__main__":
    unittest.main()
