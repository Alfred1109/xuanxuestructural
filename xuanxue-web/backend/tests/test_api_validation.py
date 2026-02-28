import sys
import unittest
import asyncio
from unittest.mock import patch

import httpx

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')
import main

app = main.app


class TestApiValidation(unittest.TestCase):
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async def _run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, url, **kwargs)
        return asyncio.run(_run())

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
        self.assertTrue(resp.json().get("success"))

    def test_calendar_invalid_day_returns_422(self):
        resp = self.request(
            "POST",
            "/api/calendar/solar-to-lunar",
            json={"year": 2026, "month": 2, "day": 32},
        )
        self.assertEqual(resp.status_code, 422)

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

    def test_qimen_invalid_real_date_returns_400(self):
        resp = self.request(
            "POST",
            "/api/divination/qimen?year=2026&month=2&day=31&hour=9&minute=0&matter_type=通用",
        )
        self.assertEqual(resp.status_code, 400)

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

    def test_ai_chat_unavailable_returns_503(self):
        with patch("main.llm_helper.is_available", return_value=False):
            resp = self.request("POST", "/api/ai/chat?question=你好")
        self.assertEqual(resp.status_code, 503)

    def test_ai_chat_upstream_empty_returns_502(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.chat", return_value=None
        ):
            resp = self.request("POST", "/api/ai/chat?question=你好")
        self.assertEqual(resp.status_code, 502)

    def test_ai_chat_success_returns_200(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.chat", return_value="测试回复"
        ):
            resp = self.request("POST", "/api/ai/chat?question=你好")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("success"))
        self.assertEqual(payload.get("data", {}).get("answer"), "测试回复")

    def test_ai_status_available_enum(self):
        main.AI_RUNTIME_STATE["last_error"] = None
        main.AI_RUNTIME_STATE["last_error_at"] = None
        with patch("main.llm_helper.is_available", return_value=True):
            resp = self.request("GET", "/api/ai/status")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json().get("data", {})
        self.assertEqual(payload.get("status"), "available")
        self.assertTrue(payload.get("available"))

    def test_ai_status_unconfigured_enum(self):
        with patch("main.llm_helper.is_available", return_value=False):
            resp = self.request("GET", "/api/ai/status")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json().get("data", {})
        self.assertEqual(payload.get("status"), "unconfigured")
        self.assertFalse(payload.get("available"))

    def test_ai_status_degraded_enum(self):
        main.AI_RUNTIME_STATE["last_error"] = "chat_empty_response"
        main.AI_RUNTIME_STATE["last_error_at"] = "2026-02-28T10:00:00"
        with patch("main.llm_helper.is_available", return_value=True):
            resp = self.request("GET", "/api/ai/status")
        self.assertEqual(resp.status_code, 200)
        payload = resp.json().get("data", {})
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
        payload = resp.json()
        self.assertFalse(payload.get("ai_enabled"))
        self.assertFalse(payload.get("ai_enhanced"))
        self.assertTrue(payload.get("ai_message"))

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
        payload = resp.json()
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
        payload = resp.json()
        self.assertTrue(payload.get("ai_enabled"))
        self.assertTrue(payload.get("ai_enhanced"))
        self.assertEqual(payload.get("data", {}).get("ai_interpretation"), "AI解读")

    def test_ai_enhance_qimen_upstream_empty_has_warning(self):
        with patch("main.llm_helper.is_available", return_value=True), patch(
            "main.llm_helper.enhance_qimen_interpretation", return_value=None
        ):
            resp = self.request(
                "POST",
                "/api/ai/enhance-qimen?year=2026&month=2&day=28&hour=9&minute=0&matter_type=通用",
            )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("ai_enabled"))
        self.assertFalse(payload.get("ai_enhanced"))
        self.assertTrue(payload.get("ai_message"))


if __name__ == "__main__":
    unittest.main()
