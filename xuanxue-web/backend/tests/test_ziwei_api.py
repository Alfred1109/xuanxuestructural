import sys
import unittest
import asyncio

import httpx

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')
import main

app = main.app


class TestZiWeiApi(unittest.TestCase):
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async def _run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, url, **kwargs)
        return asyncio.run(_run())

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
        payload = resp.json()
        self.assertTrue(payload.get("success"))
        self.assertIn("minggong", payload.get("data", {}))
        self.assertIn("palaces", payload.get("data", {}))
        self.assertIn("analysis", payload.get("data", {}))

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


if __name__ == "__main__":
    unittest.main()
