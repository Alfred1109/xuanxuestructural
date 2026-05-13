import sys
import unittest
import asyncio
import tempfile
from unittest.mock import patch

import httpx

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')
import main

app = main.app


class TestApiValidation(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.env_patch = patch.dict(
            "os.environ",
            {
                "USER_STORE_PATH": self.temp_dir.name + "/users.json",
                "SESSION_STORE_PATH": self.temp_dir.name + "/sessions.json",
                "CONSULT_HISTORY_PATH": self.temp_dir.name + "/consult_history.jsonl",
                "DECISION_LOG_PATH": self.temp_dir.name + "/decision_logs.jsonl",
                "WEIGHT_TUNING_PATH": self.temp_dir.name + "/weight_tuning.jsonl",
            },
        )
        self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop()
        self.temp_dir.cleanup()

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async def _run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, url, **kwargs)
        return asyncio.run(_run())

    def assert_success_envelope(self, response: httpx.Response) -> dict:
        payload = response.json()
        self.assertTrue(payload.get("success"))
        self.assertIn("data", payload)
        meta = payload.get("meta", {})
        self.assertTrue(meta.get("schema_version"))
        self.assertTrue(meta.get("generated_at"))
        self.assertTrue(meta.get("request_id"))
        return payload

    def assert_error_envelope(self, response: httpx.Response, code: str = None) -> dict:
        payload = response.json()
        self.assertFalse(payload.get("success"))
        error = payload.get("error", {})
        self.assertTrue(error.get("code"))
        self.assertTrue(error.get("message"))
        self.assertIn("retryable", error)
        meta = payload.get("meta", {})
        self.assertTrue(meta.get("schema_version"))
        self.assertTrue(meta.get("generated_at"))
        self.assertTrue(meta.get("request_id"))
        if code is not None:
            self.assertEqual(error.get("code"), code)
        return payload

    def test_bazi_invalid_gender_returns_422(self):
        resp = self.request(
            "POST",
            "/api/bazi",
            json={
                "year": 1990,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "gender": "X",
            },
        )
        self.assertEqual(resp.status_code, 422)
        self.assert_error_envelope(resp, "validation_error")

    def test_bazi_invalid_month_returns_422(self):
        resp = self.request(
            "POST",
            "/api/bazi",
            json={
                "year": 1990,
                "month": 13,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "gender": "男",
            },
        )
        self.assertEqual(resp.status_code, 422)
        self.assert_error_envelope(resp, "validation_error")

    def test_bazi_valid_payload_returns_200(self):
        resp = self.request(
            "POST",
            "/api/bazi",
            json={
                "year": 1990,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "gender": "男",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assert_success_envelope(resp)

    def test_ziwei_valid_payload_returns_200(self):
        resp = self.request(
            "POST",
            "/api/ziwei",
            json={
                "year": 1990,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "gender": "男",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assert_success_envelope(resp)

    def test_ziwei_invalid_gender_returns_422(self):
        resp = self.request(
            "POST",
            "/api/ziwei",
            json={
                "year": 1990,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "gender": "X",
            },
        )
        self.assertEqual(resp.status_code, 422)
        self.assert_error_envelope(resp, "validation_error")

    def test_fengshui_valid_payload_returns_200(self):
        resp = self.request(
            "POST",
            "/api/fengshui",
            json={
                "question": "这个办公室工位适合我长期坐吗？",
                "location": "上海浦东办公室",
                "orientation": "东南向",
                "scene_type": "office",
                "layout_note": "背后有靠，前方较开阔，但左侧杂物较多。",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assert_success_envelope(resp)

    def test_calendar_invalid_day_returns_422(self):
        resp = self.request(
            "POST",
            "/api/calendar/solar-to-lunar",
            json={"year": 2026, "month": 2, "day": 32},
        )
        self.assertEqual(resp.status_code, 422)
        self.assert_error_envelope(resp, "validation_error")

    def test_calendar_invalid_year_returns_422(self):
        resp = self.request(
            "POST",
            "/api/calendar/solar-to-lunar",
            json={"year": 1800, "month": 2, "day": 1},
        )
        self.assertEqual(resp.status_code, 422)

    def test_calendar_invalid_real_date_returns_400(self):
        resp = self.request(
            "POST",
            "/api/calendar/solar-to-lunar",
            json={"year": 2026, "month": 2, "day": 31},
        )
        self.assertEqual(resp.status_code, 400)
        self.assert_error_envelope(resp, "bad_request")

    def test_lunar_to_solar_valid_payload_returns_200(self):
        resp = self.request(
            "POST",
            "/api/calendar/lunar-to-solar",
            json={"year": 2024, "month": 1, "day": 1, "is_leap": False},
        )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertEqual(payload.get("data", {}).get("solar"), {"year": 2024, "month": 2, "day": 10})

    def test_lunar_to_solar_invalid_lunar_date_returns_400(self):
        resp = self.request(
            "POST",
            "/api/calendar/lunar-to-solar",
            json={"year": 2024, "month": 1, "day": 31, "is_leap": False},
        )
        self.assertEqual(resp.status_code, 400)
        self.assert_error_envelope(resp, "bad_request")

    def test_qimen_invalid_real_date_returns_400(self):
        resp = self.request(
            "POST",
            "/api/divination/qimen?year=2026&month=2&day=31&hour=9&minute=0&matter_type=通用",
        )
        self.assertEqual(resp.status_code, 400)

    def test_qimen_missing_query_params_returns_422(self):
        resp = self.request(
            "POST",
            "/api/divination/qimen?year=2026&month=2",
        )
        self.assertEqual(resp.status_code, 422)
        payload = self.assert_error_envelope(resp, "validation_error")
        self.assertEqual(payload.get("error", {}).get("details"), [
            {"field": "day", "message": "Field required"},
            {"field": "hour", "message": "Field required"},
        ])

    def test_liuyao_accepts_json_body(self):
        resp = self.request(
            "POST",
            "/api/divination/liuyao",
            json={"question": "这周项目推进如何？"},
        )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertEqual(payload.get("data", {}).get("question"), "这周项目推进如何？")

    def test_qimen_accepts_json_body(self):
        resp = self.request(
            "POST",
            "/api/divination/qimen",
            json={
                "year": 2026,
                "month": 2,
                "day": 28,
                "hour": 9,
                "minute": 0,
                "matter_type": "通用",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assert_success_envelope(resp)

    def test_ai_enhance_qimen_missing_query_params_returns_422(self):
        resp = self.request(
            "POST",
            "/api/ai/enhance-qimen?year=2026&month=2",
        )
        self.assertEqual(resp.status_code, 422)
        payload = self.assert_error_envelope(resp, "validation_error")
        self.assertEqual(payload.get("error", {}).get("details"), [
            {"field": "day", "message": "Field required"},
            {"field": "hour", "message": "Field required"},
        ])

    def test_zeri_auspicious_days_out_of_range_returns_422(self):
        resp = self.request("GET", "/api/zeri/auspicious?year=2026&month=2&days=1000")
        self.assertEqual(resp.status_code, 422)

    def test_zeri_invalid_real_date_returns_400(self):
        resp = self.request("GET", "/api/zeri/date/2026/2/31")
        self.assertEqual(resp.status_code, 400)

    def test_ganzhi_year_out_of_range_returns_422(self):
        resp = self.request("GET", "/api/ganzhi/year/1800")
        self.assertEqual(resp.status_code, 422)

    def test_ai_chat_missing_question_returns_422(self):
        resp = self.request("POST", "/api/ai/chat")
        self.assertEqual(resp.status_code, 422)
        self.assert_error_envelope(resp, "missing_question")

    def test_system_consult_requires_login(self):
        resp = self.request(
            "POST",
            "/api/system/consult",
            json={"question": "我现在适合换工作吗？"},
        )
        self.assertEqual(resp.status_code, 401)
        self.assert_error_envelope(resp, "unauthorized")

    def test_auth_register_login_profile_and_history_flow(self):
        register_resp = self.request(
            "POST",
            "/api/auth/register",
            json={
                "email": "demo@example.com",
                "password": "password123",
                "display_name": "演示用户",
            },
        )
        self.assertEqual(register_resp.status_code, 200)
        register_payload = self.assert_success_envelope(register_resp)
        token = register_payload["data"]["token"]
        self.assertEqual(register_payload["data"]["user"]["display_name"], "演示用户")

        me_resp = self.request(
            "GET",
            "/api/auth/me",
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(me_resp.status_code, 200)
        me_payload = self.assert_success_envelope(me_resp)
        self.assertEqual(me_payload["data"]["user"]["email"], "demo@example.com")

        profile_resp = self.request(
            "PATCH",
            "/api/auth/profile",
            headers={"Authorization": "Bearer " + token},
            json={
                "display_name": "新昵称",
                "gender": "男",
                "year": 1990,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "location": "上海",
            },
        )
        self.assertEqual(profile_resp.status_code, 200)
        profile_payload = self.assert_success_envelope(profile_resp)
        self.assertEqual(profile_payload["data"]["user"]["display_name"], "新昵称")
        self.assertEqual(profile_payload["data"]["user"]["profile"]["location"], "上海")

        consult_resp = self.request(
            "POST",
            "/api/system/consult",
            headers={"Authorization": "Bearer " + token},
            json={"question": "我现在适合换工作吗？"},
        )
        self.assertEqual(consult_resp.status_code, 200)
        consult_payload = self.assert_success_envelope(consult_resp)
        self.assertTrue(consult_payload["data"]["account_history"]["saved"])

        history_resp = self.request(
            "GET",
            "/api/auth/history",
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(history_resp.status_code, 200)
        history_payload = self.assert_success_envelope(history_resp)
        self.assertEqual(history_payload["data"]["count"], 1)
        history_id = history_payload["data"]["items"][0]["history_id"]

        detail_resp = self.request(
            "GET",
            "/api/auth/history/" + history_id,
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(detail_resp.status_code, 200)
        detail_payload = self.assert_success_envelope(detail_resp)
        self.assertIn("换工作", detail_payload["data"]["item"]["question"])

        preset_save_resp = self.request(
            "POST",
            "/api/auth/consult-presets",
            headers={"Authorization": "Bearer " + token},
            json={
                "name": "我的事业问事模板",
                "question": "我现在适合换工作吗？",
                "year": 1990,
                "month": 1,
                "day": 1,
                "hour": 12,
                "minute": 0,
                "gender": "男",
                "location": "上海",
                "is_default": True,
            },
        )
        self.assertEqual(preset_save_resp.status_code, 200)
        preset_save_payload = self.assert_success_envelope(preset_save_resp)
        self.assertEqual(preset_save_payload["data"]["count"], 1)
        preset_id = preset_save_payload["data"]["items"][0]["preset_id"]

        preset_list_resp = self.request(
            "GET",
            "/api/auth/consult-presets",
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(preset_list_resp.status_code, 200)
        preset_list_payload = self.assert_success_envelope(preset_list_resp)
        self.assertEqual(preset_list_payload["data"]["items"][0]["name"], "我的事业问事模板")
        self.assertTrue(preset_list_payload["data"]["items"][0]["is_default"])

        preset_delete_resp = self.request(
            "DELETE",
            "/api/auth/consult-presets/" + preset_id,
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(preset_delete_resp.status_code, 200)
        preset_delete_payload = self.assert_success_envelope(preset_delete_resp)
        self.assertEqual(preset_delete_payload["data"]["count"], 0)

        logout_resp = self.request(
            "POST",
            "/api/auth/logout",
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(logout_resp.status_code, 200)
        self.assert_success_envelope(logout_resp)

    def test_auth_login_rejects_wrong_password(self):
        self.request(
            "POST",
            "/api/auth/register",
            json={
                "email": "demo@example.com",
                "password": "password123",
                "display_name": "演示用户",
            },
        )

        login_resp = self.request(
            "POST",
            "/api/auth/login",
            json={
                "email": "demo@example.com",
                "password": "wrong-pass",
            },
        )
        self.assertEqual(login_resp.status_code, 401)
        self.assert_error_envelope(login_resp, "unauthorized")

    def test_ai_chat_unavailable_returns_503(self):
        with patch("main.llm_helper.is_available", return_value=False):
            resp = self.request("POST", "/api/ai/chat?question=你好")
        self.assertEqual(resp.status_code, 503)
        self.assert_error_envelope(resp, "ai_unconfigured")

    def test_ai_chat_upstream_empty_returns_502(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.chat", return_value=None
        ):
            resp = self.request("POST", "/api/ai/chat?question=你好")
        self.assertEqual(resp.status_code, 502)
        self.assert_error_envelope(resp, "ai_upstream_empty")

    def test_ai_chat_success_returns_200(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.chat", return_value="测试回复"
        ):
            resp = self.request("POST", "/api/ai/chat?question=你好")
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertEqual(payload.get("data", {}).get("answer"), "测试回复")

    def test_ai_chat_accepts_json_body(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.chat", return_value="Body回复"
        ):
            resp = self.request(
                "POST",
                "/api/ai/chat",
                json={"question": "使用Body提问", "context": "上下文"},
            )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertEqual(payload.get("data", {}).get("question"), "使用Body提问")
        self.assertEqual(payload.get("data", {}).get("context"), "上下文")
        self.assertEqual(payload.get("data", {}).get("answer"), "Body回复")

    def test_ai_status_available_enum(self):
        main.AI_RUNTIME_STATE["last_error"] = None
        main.AI_RUNTIME_STATE["last_error_at"] = None
        with patch("main.llm_helper.is_available", return_value=True):
            resp = self.request("GET", "/api/ai/status")
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp).get("data", {})
        self.assertEqual(payload.get("status"), "available")
        self.assertTrue(payload.get("available"))

    def test_ai_status_unconfigured_enum(self):
        with patch("main.llm_helper.is_available", return_value=False):
            resp = self.request("GET", "/api/ai/status")
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp).get("data", {})
        self.assertEqual(payload.get("status"), "unconfigured")
        self.assertFalse(payload.get("available"))

    def test_ai_status_degraded_enum(self):
        main.AI_RUNTIME_STATE["last_error"] = "chat_empty_response"
        main.AI_RUNTIME_STATE["last_error_at"] = "2026-02-28T10:00:00"
        with patch("main.llm_helper.is_available", return_value=True):
            resp = self.request("GET", "/api/ai/status")
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp).get("data", {})
        self.assertEqual(payload.get("status"), "degraded")
        self.assertTrue(payload.get("available"))
        self.assertEqual(payload.get("last_error"), "chat_empty_response")
        main.AI_RUNTIME_STATE["last_error"] = None
        main.AI_RUNTIME_STATE["last_error_at"] = None

    def test_ai_enhance_bazi_unavailable_returns_base_with_flags(self):
        with patch("main.llm_helper.is_available", return_value=False):
            resp = self.request(
                "POST",
                "/api/ai/enhance-bazi",
                json={
                    "year": 1990,
                    "month": 1,
                    "day": 1,
                    "hour": 12,
                    "minute": 0,
                    "gender": "男",
                },
            )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertFalse(payload.get("ai_enabled"))
        self.assertFalse(payload.get("ai_enhanced"))
        self.assertTrue(payload.get("ai_message"))
        self.assertIn("ai", payload.get("data", {}))

    def test_ai_enhance_bazi_upstream_empty_has_warning(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.enhance_bazi_analysis", return_value=None
        ):
            resp = self.request(
                "POST",
                "/api/ai/enhance-bazi",
                json={
                    "year": 1990,
                    "month": 1,
                    "day": 1,
                    "hour": 12,
                    "minute": 0,
                    "gender": "男",
                },
            )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertTrue(payload.get("ai_enabled"))
        self.assertFalse(payload.get("ai_enhanced"))
        self.assertTrue(payload.get("ai_message"))
        self.assertIsNone(payload.get("data", {}).get("ai_analysis"))

    def test_ai_enhance_liuyao_success_sets_ai_enhanced(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.enhance_liuyao_interpretation", return_value="AI解读"
        ):
            resp = self.request("POST", "/api/ai/enhance-liuyao?question=测试")
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertTrue(payload.get("ai_enabled"))
        self.assertTrue(payload.get("ai_enhanced"))
        self.assertEqual(payload.get("data", {}).get("ai_interpretation"), "AI解读")

    def test_ai_enhance_liuyao_accepts_json_body(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.enhance_liuyao_interpretation", return_value="AI解读"
        ):
            resp = self.request(
                "POST",
                "/api/ai/enhance-liuyao",
                json={"question": "Body提问"},
            )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertEqual(payload.get("data", {}).get("question"), "Body提问")
        self.assertTrue(payload.get("ai_enhanced"))

    def test_ai_enhance_qimen_upstream_empty_has_warning(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.enhance_qimen_interpretation", return_value=None
        ):
            resp = self.request(
                "POST",
                "/api/ai/enhance-qimen?year=2026&month=2&day=28&hour=9&minute=0&matter_type=通用",
            )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertTrue(payload.get("ai_enabled"))
        self.assertFalse(payload.get("ai_enhanced"))
        self.assertTrue(payload.get("ai_message"))

    def test_ai_enhance_qimen_accepts_json_body(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.enhance_qimen_interpretation", return_value="AI奇门解读"
        ):
            resp = self.request(
                "POST",
                "/api/ai/enhance-qimen",
                json={
                    "year": 2026,
                    "month": 2,
                    "day": 28,
                    "hour": 9,
                    "minute": 0,
                    "matter_type": "学业",
                },
            )
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertTrue(payload.get("ai_enhanced"))
        self.assertEqual(payload.get("data", {}).get("ai_interpretation"), "AI奇门解读")

    def test_ai_enhance_zeri_today_returns_200(self):
        with patch("main.llm_helper.is_available", return_value=False):
            resp = self.request("GET", "/api/ai/enhance-zeri/today?purpose=通用")
        self.assertEqual(resp.status_code, 200)
        payload = self.assert_success_envelope(resp)
        self.assertFalse(payload.get("ai_enabled"))
        self.assertIn("date", payload.get("data", {}))

    def test_main_exports_runtime_state_and_app_after_router_split(self):
        self.assertTrue(hasattr(main, "app"))
        self.assertTrue(hasattr(main, "llm_helper"))
        self.assertTrue(hasattr(main, "AI_RUNTIME_STATE"))


if __name__ == "__main__":
    unittest.main()
