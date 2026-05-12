import sys
import unittest
import asyncio

import httpx

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')
import main

app = main.app


class TestFengShuiApi(unittest.TestCase):
    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async def _run():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, url, **kwargs)
        return asyncio.run(_run())

    def test_fengshui_valid_payload_returns_200(self):
        resp = self.request(
            "POST",
            "/api/fengshui",
            json={
                "question": "这个办公室工位适合我长期坐吗？",
                "location": "上海浦东办公室",
                "orientation": "东南向",
                "scene_type": "office",
                "layout_note": "背后有靠，前方较开阔，但左侧杂物较多，采光不错。",
            },
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get("success"))
        self.assertIn("space_support", payload.get("data", {}))
        self.assertIn("calc_trace", payload.get("data", {}))


if __name__ == "__main__":
    unittest.main()
