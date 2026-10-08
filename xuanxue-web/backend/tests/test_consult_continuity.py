import asyncio
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


class TestConsultContinuity(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(
            "os.environ",
            {
                "USER_STORE_PATH": self.temp_dir.name + "/users.json",
                "SESSION_STORE_PATH": self.temp_dir.name + "/sessions.json",
                "CONSULT_HISTORY_PATH": self.temp_dir.name + "/history.jsonl",
                "CONSULT_FOLLOWUPS_PATH": self.temp_dir.name + "/followups.jsonl",
                "DECISION_LOG_PATH": self.temp_dir.name + "/decisions.jsonl",
                "WEIGHT_TUNING_PATH": self.temp_dir.name + "/weights.jsonl",
            },
        )
        self.env_patch.start()
        self.owner_token = self.register("owner@example.com")
        self.other_token = self.register("other@example.com")

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def request(self, method, path, token=None, **kwargs):
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = "Bearer " + token

        async def run():
            transport = httpx.ASGITransport(app=main.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, headers=headers, **kwargs)

        return asyncio.run(run())

    def register(self, email):
        response = self.request(
            "POST",
            "/api/auth/register",
            json={"email": email, "password": "password123", "display_name": "测试"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]["token"]

    def create_history(self, token=None):
        result = {
            "question": "我适合换工作吗？",
            "profile": {"year": 1980, "gender": "男", "location": "上海"},
            "intent": {"modules": ["meihua"], "matter_type": "事业", "purpose": "换工作"},
            "modules": {"meihua": {"gua": "示例卦"}},
            "module_summaries": {"meihua": {"summary": "示例摘要"}},
            "decision_kernel": {"recommendation": "谨慎评估"},
            "answer": "现阶段建议先评估机会。",
            "trace": {"steps": [{"id": "s1"}]},
            "ai": {"enabled": False, "synthesized": False, "fallback": True},
        }
        payload = {
            "question": "我适合换工作吗？",
            "year": 1980,
            "gender": "男",
            "location": "上海",
            "purpose": "换工作",
            "matter_type": "事业",
        }
        expected_snapshot = dict(result)
        with patch("api.system.consultation_engine.consult", return_value=result):
            response = self.request("POST", "/api/system/consult", token or self.owner_token, json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]["account_history"]["history_id"], expected_snapshot, payload

    def test_history_detail_preserves_full_result_payload_and_legacy_compatibility(self):
        history_id, expected_result, expected_payload = self.create_history()
        detail = self.request("GET", f"/api/auth/history/{history_id}", self.owner_token)
        self.assertEqual(detail.status_code, 200)
        item = detail.json()["data"]["item"]
        self.assertEqual(item["answer"], expected_result["answer"])
        self.assertEqual(item["consultation"], expected_result)
        self.assertEqual(item["request_payload"], expected_payload)
        self.assertEqual(item["followups"], [])

        # An older history row has no full snapshot. Its existing response
        # fields remain readable, and recoverable request fields are derived.
        from core.runtime.store import append_jsonl, resolve_runtime_path

        append_jsonl(resolve_runtime_path("CONSULT_HISTORY_PATH", "consult_history.jsonl"), {
            "history_id": "legacy-id",
            "user_id": "legacy-user",
            "created_at": "2025-01-01T00:00:00+00:00",
            "question": "旧问题",
            "answer": "旧结论",
            "profile": {
                "birth": {"year": 1988, "month": 4, "day": 2, "hour": 0, "minute": 0},
                "gender": "女",
                "location": "苏州",
            },
            "intent": {"purpose": "旧用途"},
        })
        from core.consult_history import get_consult_history_detail

        legacy = get_consult_history_detail("legacy-user", "legacy-id")
        self.assertEqual(legacy["answer"], "旧结论")
        self.assertIsNone(legacy["consultation"])
        self.assertEqual(legacy["request_payload"], {
            "question": "旧问题",
            "year": 1988,
            "month": 4,
            "day": 2,
            "hour": 0,
            "minute": 0,
            "gender": "女",
            "location": "苏州",
            "purpose": "旧用途",
        })

    def test_followups_require_ownership_use_server_context_and_persist(self):
        history_id, _, _ = self.create_history()
        url = f"/api/system/consult/{history_id}/followups"

        unauthenticated = self.request("POST", url, json={"question": "补充问一句"})
        self.assertEqual(unauthenticated.status_code, 401)
        foreign_read = self.request("GET", url, self.other_token)
        self.assertEqual(foreign_read.status_code, 404)
        foreign_write = self.request("POST", url, self.other_token, json={"question": "越权追问"})
        self.assertEqual(foreign_write.status_code, 404)

        with patch("core.consult.followups.llm_helper.chat", side_effect=["根据原结果，先比较新旧岗位。", "还要核对收入稳定性。"]) as chat:
            first = self.request("POST", url, self.owner_token, json={"question": "具体该怎么比较？"})
            self.assertEqual(first.status_code, 200, first.text)
            first_item = first.json()["data"]["followup"]
            self.assertEqual(first_item["answer"], "根据原结果，先比较新旧岗位。")
            self.assertIn("我适合换工作吗？", chat.call_args_list[0].args[1])
            self.assertIn("现阶段建议先评估机会。", chat.call_args_list[0].args[1])

            second = self.request("POST", url, self.owner_token, json={"question": "还要考虑什么？"})
            self.assertEqual(second.status_code, 200, second.text)
            self.assertIn("具体该怎么比较？", chat.call_args_list[1].args[1])
            self.assertIn("根据原结果，先比较新旧岗位。", chat.call_args_list[1].args[1])

        listed = self.request("GET", url, self.owner_token)
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["data"]["count"], 2)
        detail = self.request("GET", f"/api/auth/history/{history_id}", self.owner_token)
        self.assertEqual(len(detail.json()["data"]["item"]["followups"]), 2)

    def test_unavailable_ai_does_not_create_a_fake_followup(self):
        history_id, _, _ = self.create_history()
        url = f"/api/system/consult/{history_id}/followups"
        with patch("core.consult.followups.llm_helper.chat", return_value=None):
            response = self.request("POST", url, self.owner_token, json={"question": "追问"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["error"]["code"], "followup_ai_unavailable")

        with patch("core.consult.followups.llm_helper.chat", side_effect=RuntimeError("provider error")):
            failed_provider = self.request("POST", url, self.owner_token, json={"question": "再次追问"})
        self.assertEqual(failed_provider.status_code, 503)
        self.assertEqual(failed_provider.json()["error"]["code"], "followup_ai_unavailable")

        listing = self.request("GET", url, self.owner_token)
        self.assertEqual(listing.json()["data"]["count"], 0)

    def test_consultation_request_id_reuses_result_rejects_payload_changes_and_is_user_scoped(self):
        request_id = "consult-retry-key-1"

        def consult(payload):
            return {
                "question": payload.question,
                "profile": {},
                "intent": {"modules": [], "matter_type": "通用", "purpose": "通用"},
                "modules": {},
                "module_summaries": {},
                "decision_kernel": {},
                "answer": "answer for " + payload.question,
                "trace": {"steps": []},
                "ai": {"enabled": False, "synthesized": False, "fallback": True},
            }

        with patch("api.system.consultation_engine.consult", side_effect=consult) as engine_call:
            first = self.request(
                "POST", "/api/system/consult", self.owner_token,
                json={"question": "是否换工作？", "request_id": request_id},
            )
            repeated = self.request(
                "POST", "/api/system/consult", self.owner_token,
                json={"question": "是否换工作？", "request_id": request_id},
            )
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(repeated.status_code, 200, repeated.text)
            first_data = first.json()["data"]
            repeated_data = repeated.json()["data"]
            self.assertEqual(first_data["account_history"]["history_id"], repeated_data["account_history"]["history_id"])
            self.assertEqual(first_data["answer"], repeated_data["answer"])
            engine_call.assert_called_once()
            from core.runtime.store import read_jsonl, resolve_runtime_path

            history_entries = read_jsonl(resolve_runtime_path("CONSULT_HISTORY_PATH", "consult_history.jsonl"))
            matching_entries = [entry for entry in history_entries if entry.get("request_id") == request_id]
            self.assertEqual(len(matching_entries), 1)
            self.assertEqual(matching_entries[0]["history_id"], first_data["account_history"]["history_id"])
            history_detail = self.request(
                "GET", f"/api/auth/history/{first_data['account_history']['history_id']}", self.owner_token
            ).json()["data"]["item"]
            self.assertEqual(history_detail["request_payload"], {"question": "是否换工作？"})

            conflict = self.request(
                "POST", "/api/system/consult", self.owner_token,
                json={"question": "是否搬家？", "request_id": request_id},
            )
            self.assertEqual(conflict.status_code, 409)
            self.assertEqual(conflict.json()["error"]["code"], "idempotency_conflict")

            changed_condition = self.request(
                "POST", "/api/system/consult", self.owner_token,
                json={"question": "是否换工作？", "year": 1980, "request_id": request_id},
            )
            self.assertEqual(changed_condition.status_code, 409)

            other_account = self.request(
                "POST", "/api/system/consult", self.other_token,
                json={"question": "是否换工作？", "request_id": request_id},
            )
            self.assertEqual(other_account.status_code, 200, other_account.text)
            self.assertNotEqual(
                first_data["account_history"]["history_id"],
                other_account.json()["data"]["account_history"]["history_id"],
            )
            matching_entries = [
                entry for entry in read_jsonl(resolve_runtime_path("CONSULT_HISTORY_PATH", "consult_history.jsonl"))
                if entry.get("request_id") == request_id
            ]
            self.assertEqual(len(matching_entries), 2)
            self.assertEqual(engine_call.call_count, 2)

    def test_concurrent_consultation_retries_calculate_and_save_once(self):
        request_id = "concurrent-consult-key"

        def consult(payload):
            time.sleep(0.1)
            return {
                "question": payload.question,
                "profile": {},
                "intent": {"modules": [], "matter_type": "通用", "purpose": "通用"},
                "modules": {},
                "module_summaries": {},
                "decision_kernel": {},
                "answer": "same result",
                "trace": {"steps": []},
                "ai": {"enabled": False, "synthesized": False, "fallback": True},
            }

        def post():
            return self.request(
                "POST", "/api/system/consult", self.owner_token,
                json={"question": "问事去重", "request_id": request_id},
            )

        with patch("api.system.consultation_engine.consult", side_effect=consult) as engine_call:
            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(pool.map(lambda _: post(), range(2)))
        self.assertTrue(all(response.status_code == 200 for response in responses))
        history_ids = [response.json()["data"]["account_history"]["history_id"] for response in responses]
        self.assertEqual(history_ids[0], history_ids[1])
        engine_call.assert_called_once()

    def test_followup_request_id_reuses_answer_and_rejects_other_payload(self):
        history_id, _, _ = self.create_history()
        request_id = "followup-retry-key"
        url = f"/api/system/consult/{history_id}/followups"
        with patch("core.consult.followups.llm_helper.chat", return_value="已保存的追问答复") as chat:
            first = self.request(
                "POST", url, self.owner_token,
                json={"question": "该怎么比较？", "request_id": request_id},
            )
            repeated = self.request(
                "POST", url, self.owner_token,
                json={"question": "该怎么比较？", "request_id": request_id},
            )
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(repeated.status_code, 200, repeated.text)
            first_followup = first.json()["data"]["followup"]
            repeated_followup = repeated.json()["data"]["followup"]
            self.assertEqual(first_followup["followup_id"], repeated_followup["followup_id"])
            self.assertEqual(first_followup["answer"], repeated_followup["answer"])
            chat.assert_called_once()
            from core.runtime.store import read_jsonl, resolve_runtime_path

            stored_followups = read_jsonl(resolve_runtime_path("CONSULT_FOLLOWUPS_PATH", "consult_followups.jsonl"))
            matches = [item for item in stored_followups if item.get("request_id") == request_id]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]["history_id"], history_id)

            conflict = self.request(
                "POST", url, self.owner_token,
                json={"question": "改问另一个问题", "request_id": request_id},
            )
            self.assertEqual(conflict.status_code, 409)
            self.assertEqual(conflict.json()["error"]["code"], "idempotency_conflict")

            second_history_id, _, _ = self.create_history()
            second_history_url = f"/api/system/consult/{second_history_id}/followups"
            with patch("core.consult.followups.llm_helper.chat") as unexpected_chat:
                different_history = self.request(
                    "POST", second_history_url, self.owner_token,
                    json={"question": "该怎么比较？", "request_id": request_id},
                )
            self.assertEqual(different_history.status_code, 409)
            unexpected_chat.assert_not_called()

            other_history_id, _, _ = self.create_history(self.other_token)
            other_url = f"/api/system/consult/{other_history_id}/followups"
            with patch("core.consult.followups.llm_helper.chat", return_value="另一用户的答复") as other_chat:
                other_user = self.request(
                    "POST", other_url, self.other_token,
                    json={"question": "该怎么比较？", "request_id": request_id},
                )
            self.assertEqual(other_user.status_code, 200, other_user.text)
            self.assertNotEqual(first_followup["followup_id"], other_user.json()["data"]["followup"]["followup_id"])
            other_chat.assert_called_once()
            stored_followups = read_jsonl(resolve_runtime_path("CONSULT_FOLLOWUPS_PATH", "consult_followups.jsonl"))
            self.assertEqual(len([item for item in stored_followups if item.get("request_id") == request_id]), 2)

    def test_concurrent_followup_retries_call_ai_and_persist_once(self):
        history_id, _, _ = self.create_history()
        url = f"/api/system/consult/{history_id}/followups"

        def answer(question, context):
            time.sleep(0.1)
            return "相同追问答复"

        def post():
            return self.request(
                "POST", url, self.owner_token,
                json={"question": "具体怎么做？", "request_id": "concurrent-followup-id"},
            )

        with patch("core.consult.followups.llm_helper.chat", side_effect=answer) as chat:
            with ThreadPoolExecutor(max_workers=2) as pool:
                responses = list(pool.map(lambda _: post(), range(2)))
        self.assertTrue(all(response.status_code == 200 for response in responses))
        followup_ids = [response.json()["data"]["followup"]["followup_id"] for response in responses]
        self.assertEqual(followup_ids[0], followup_ids[1])
        chat.assert_called_once()

    def test_request_id_is_optional_but_limited_to_100_characters(self):
        too_long = self.request(
            "POST", "/api/system/consult", self.owner_token,
            json={"question": "校验请求ID长度", "request_id": "x" * 101},
        )
        self.assertEqual(too_long.status_code, 422)
        # Omission remains valid for existing integrations and keeps prior behavior.
        history_id, _, _ = self.create_history()
        self.assertTrue(history_id)


if __name__ == "__main__":
    unittest.main()
