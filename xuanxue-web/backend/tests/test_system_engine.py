import sys
import unittest
import tempfile
import json
import core.system_engine as legacy_system_engine
from unittest.mock import patch

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')

from core.system_engine import UnifiedConsultRequest, consultation_engine
from core.decision_log import append_feedback_log, read_recent_decision_logs
from core.weight_tuning import DEFAULT_WEIGHT_PRESETS, record_weight_tuning, resolve_effective_weight_presets


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

        self.assertEqual(result["intent"]["modules"], ["bazi", "ziwei", "liuyao", "qimen"])
        self.assertIn("bazi", result["module_summaries"])
        self.assertIn("ziwei", result["module_summaries"])
        self.assertIn("liuyao", result["module_summaries"])
        self.assertIn("qimen", result["module_summaries"])
        self.assertTrue(result["ai"]["fallback"])
        self.assertIn("decision_kernel", result)
        self.assertIn("decision_log", result)
        self.assertTrue(result["decision_log"]["logged"])
        self.assertIn("world_model", result["decision_kernel"])
        self.assertIn("arbitration", result["decision_kernel"])
        self.assertIn("flowchart TD", result["trace"]["mermaid"])
        self.assertTrue(any(step["id"] == "world_model" for step in result["trace"]["steps"]))
        self.assertTrue(any(step["id"] == "arbitration" for step in result["trace"]["steps"]))
        first_step = result["trace"]["steps"][0]
        self.assertIn("inputs", first_step)
        self.assertIn("rule", first_step)
        self.assertIn("outputs", first_step)
        self.assertIn("evidence", first_step)
        self.assertIn("formulas", first_step)
        self.assertIn("derivation", first_step)
        self.assertEqual(result["trace"]["steps"][-1]["id"], "answer")
        self.assertIn("八字", result["trace"]["mermaid"])
        self.assertIn("紫微", result["trace"]["mermaid"])
        self.assertIn("六爻", result["trace"]["mermaid"])
        self.assertIn("奇门", result["trace"]["mermaid"])
        self.assertTrue(any(step["id"] == "bazi_year" for step in result["trace"]["steps"]))
        self.assertTrue(any(step["id"] == "ziwei_mingpan" for step in result["trace"]["steps"]))
        self.assertIn('subgraph bazi_pillars["四柱"]', result["trace"]["mermaid"])
        self.assertIn("direction LR", result["trace"]["mermaid"])
        bazi_year = next(step for step in result["trace"]["steps"] if step["id"] == "bazi_year")
        self.assertTrue(bazi_year["formulas"])
        self.assertEqual(bazi_year["derivation"]["result"], result["modules"]["bazi"]["bazi"]["year"])
        answer_step = result["trace"]["steps"][-1]
        self.assertNotEqual(answer_step["detail"], result["answer"])
        self.assertEqual(answer_step["outputs"]["summary"], answer_step["detail"])
        self.assertIn("完整结论已在上方结果区展示", answer_step["evidence"])

    def test_consultation_engine_uses_ziwei_when_birth_is_present(self):
        payload = UnifiedConsultRequest(
            question="我接下来三年的事业方向如何？",
            year=1990,
            month=1,
            day=1,
            hour=12,
            minute=0,
            gender="男",
        )

        with patch("core.system_engine.llm_helper.is_available", return_value=False):
            result = consultation_engine.consult(payload)

        self.assertIn("ziwei", result["intent"]["modules"])
        self.assertIn("ziwei", result["module_summaries"])
        self.assertTrue(any(step["id"] == "ziwei_judge" for step in result["trace"]["steps"]))

    def test_consultation_engine_uses_meihua_for_non_birth_quick_question(self):
        payload = UnifiedConsultRequest(
            question="我刚刚起心动念，这件事能成吗？"
        )

        with patch("core.system_engine.llm_helper.is_available", return_value=False):
            result = consultation_engine.consult(payload)

        self.assertIn("meihua", result["intent"]["modules"])
        self.assertIn("meihua", result["module_summaries"])
        self.assertTrue(any(step["id"] == "meihua_cast" for step in result["trace"]["steps"]))

    def test_consultation_engine_builds_liuyao_trace_without_birth_profile(self):
        payload = UnifiedConsultRequest(
            question="这段感情还能继续吗？"
        )

        with patch("core.system_engine.llm_helper.is_available", return_value=False):
            result = consultation_engine.consult(payload)

        self.assertIn("liuyao", result["intent"]["modules"])
        self.assertTrue(any(step["id"] == "liuyao_cast" for step in result["trace"]["steps"]))
        self.assertTrue(any(step["id"] == "liuyao_judge" for step in result["trace"]["steps"]))

    def test_consultation_engine_adds_zeri_for_clear_purpose(self):
        payload = UnifiedConsultRequest(
            question="今天适合开业吗？",
        )

        with patch("core.system_engine.llm_helper.is_available", return_value=False):
            result = consultation_engine.consult(payload)

        self.assertIn("zeri", result["intent"]["modules"])
        self.assertIn("择日", result["trace"]["mermaid"])
        self.assertTrue(any(step["id"] == "zeri_score" for step in result["trace"]["steps"]))
        self.assertTrue(any(step["id"] == "zeri_jianxing" for step in result["trace"]["steps"]))
        self.assertEqual(result["profile"]["purpose"], "开业")

    def test_consultation_engine_uses_fengshui_for_space_question(self):
        payload = UnifiedConsultRequest(
            question="这个办公室工位风水怎么样，适合我长期坐吗？",
            location="上海浦东办公室",
        )

        with patch("core.system_engine.llm_helper.is_available", return_value=False):
            result = consultation_engine.consult(payload)

        self.assertIn("fengshui", result["intent"]["modules"])
        self.assertIn("fengshui", result["module_summaries"])
        self.assertTrue(any(step["id"] == "fengshui_judge" for step in result["trace"]["steps"]))

    def test_consultation_engine_writes_decision_log_snapshot(self):
        payload = UnifiedConsultRequest(question="今天适合开业吗？")

        with tempfile.NamedTemporaryFile() as temp_file:
            with patch.dict("os.environ", {"DECISION_LOG_PATH": temp_file.name}):
                with patch("core.system_engine.llm_helper.is_available", return_value=False):
                    result = consultation_engine.consult(payload)

            self.assertTrue(result["decision_log"]["logged"])
            with open(temp_file.name, "r", encoding="utf-8") as file:
                content = file.read()
            self.assertIn("decision_kernel", content)
            self.assertIn("question", content)

    def test_feedback_log_can_be_appended_and_read(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            with patch.dict("os.environ", {"DECISION_LOG_PATH": temp_file.name}):
                append_feedback_log({
                    "log_id": "demo-log",
                    "outcome": "success",
                    "adopted": True,
                    "score": 88,
                    "notes": "结果优于预期",
                })
                items = read_recent_decision_logs(limit=5)

            self.assertTrue(items)
            serialized = json.dumps(items[-1], ensure_ascii=False)
            self.assertIn("demo-log", serialized)
            self.assertIn("success", serialized)

    def test_weight_tuning_event_can_be_recorded(self):
        with tempfile.NamedTemporaryFile() as temp_file:
            with patch.dict("os.environ", {"WEIGHT_TUNING_PATH": temp_file.name}):
                result = record_weight_tuning({
                    "decision_type": "strategic",
                    "module_weights": {"bazi": 0.5, "qimen": 0.2, "liuyao": 0.15, "meihua": 0.1, "zeri": 0.05},
                    "reason": "针对事业类问题提升命理先验权重",
                })

            self.assertTrue(result["recorded"])

    def test_effective_weight_presets_are_applied_to_consultation(self):
        payload = UnifiedConsultRequest(
            question="我现在适合换工作吗？应该怎么做更稳？",
            year=1990,
            month=1,
            day=1,
            hour=12,
            minute=0,
            gender="男",
        )

        with tempfile.NamedTemporaryFile() as temp_file:
            with patch.dict("os.environ", {"WEIGHT_TUNING_PATH": temp_file.name}):
                record_weight_tuning({
                    "decision_type": "strategic",
                    "module_weights": {"bazi": 0.7, "qimen": 0.15, "liuyao": 0.1, "meihua": 0.03, "zeri": 0.02},
                    "reason": "测试提升命理基底权重",
                })
                effective = resolve_effective_weight_presets()
                with patch("core.system_engine.llm_helper.is_available", return_value=False):
                    result = consultation_engine.consult(payload)

            self.assertEqual(effective["strategic"]["bazi"], 0.7)
            self.assertEqual(result["effective_weights"]["strategic"]["bazi"], 0.7)
            self.assertEqual(result["decision_kernel"]["arbitration"]["weights"]["bazi"], 0.7)
            self.assertGreater(
                result["decision_kernel"]["arbitration"]["weights"]["bazi"],
                result["decision_kernel"]["arbitration"]["weights"]["qimen"],
            )

    def test_default_weight_presets_single_source_of_truth(self):
        from core.arbitration import DEFAULT_WEIGHT_PRESETS as arbitration_defaults

        self.assertIs(arbitration_defaults, DEFAULT_WEIGHT_PRESETS)

    def test_legacy_system_engine_exports_remain_available(self):
        from core.consult.models import UnifiedConsultRequest as NewUnifiedConsultRequest

        self.assertIs(legacy_system_engine.UnifiedConsultRequest, NewUnifiedConsultRequest)
        self.assertTrue(hasattr(legacy_system_engine, "consultation_engine"))
        self.assertTrue(callable(legacy_system_engine.generate_simple_analysis))

    def test_decision_package_and_legacy_paths_both_resolve(self):
        from core.decision.kernel import build_unified_world_model as new_kernel
        from core.decision.signal_schema import ModuleSignal as new_signal
        from core.decision.weight_tuning import resolve_effective_weight_presets as new_resolve_weights
        from core.decision_kernel import build_unified_world_model as legacy_kernel
        from core.signal_schema import ModuleSignal as legacy_signal
        from core.weight_tuning import resolve_effective_weight_presets as legacy_resolve_weights

        self.assertIs(new_kernel, legacy_kernel)
        self.assertIs(new_signal, legacy_signal)
        self.assertIsNotNone(new_resolve_weights)
        self.assertIs(new_resolve_weights, legacy_resolve_weights)


if __name__ == "__main__":
    unittest.main()
