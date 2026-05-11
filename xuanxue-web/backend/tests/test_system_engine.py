import sys
import unittest
from unittest.mock import patch

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')

from core.system_engine import UnifiedConsultRequest, consultation_engine


class TestSystemEngine(unittest.TestCase):
    def test_consultation_engine_builds_trace_and_summaries(self):
        payload = UnifiedConsultRequest(
            question="我现在适合换工作吗？应该怎么做更稳？",
            year=1990,
            month=1,
            day=1,
            hour=12,
            minute=0,
            gender="男",
        )

        with patch("core.system_engine.llm_helper.is_available", return_value=False):
            result = consultation_engine.consult(payload)

        self.assertEqual(result["intent"]["modules"], ["bazi", "liuyao", "qimen"])
        self.assertIn("bazi", result["module_summaries"])
        self.assertIn("liuyao", result["module_summaries"])
        self.assertIn("qimen", result["module_summaries"])
        self.assertTrue(result["ai"]["fallback"])
        self.assertIn("flowchart TD", result["trace"]["mermaid"])
        first_step = result["trace"]["steps"][0]
        self.assertIn("inputs", first_step)
        self.assertIn("rule", first_step)
        self.assertIn("outputs", first_step)
        self.assertIn("evidence", first_step)
        self.assertEqual(result["trace"]["steps"][-1]["id"], "answer")
        self.assertIn("八字", result["trace"]["mermaid"])
        self.assertIn("六爻", result["trace"]["mermaid"])
        self.assertIn("奇门", result["trace"]["mermaid"])

    def test_consultation_engine_adds_zeri_for_clear_purpose(self):
        payload = UnifiedConsultRequest(
            question="今天适合开业吗？",
        )

        with patch("core.system_engine.llm_helper.is_available", return_value=False):
            result = consultation_engine.consult(payload)

        self.assertIn("zeri", result["intent"]["modules"])
        self.assertIn("择日", result["trace"]["mermaid"])
        self.assertTrue(any(step["id"] == "zeri_score" for step in result["trace"]["steps"]))
        self.assertEqual(result["profile"]["purpose"], "开业")


if __name__ == "__main__":
    unittest.main()
