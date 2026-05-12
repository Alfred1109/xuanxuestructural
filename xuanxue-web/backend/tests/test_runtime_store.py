import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append('/home/alfred/multiproject/xuanxue/xuanxue-web/backend')

from core.runtime.store import append_jsonl, read_recent_jsonl


class TestRuntimeStore(unittest.TestCase):
    def test_append_jsonl_and_read_recent_jsonl(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "events.jsonl"
            append_jsonl(path, {"id": 1, "name": "first"})
            append_jsonl(path, {"id": 2, "name": "second"})

            items = read_recent_jsonl(path, limit=5)

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], 1)
        self.assertEqual(items[1]["name"], "second")

    def test_read_recent_jsonl_handles_missing_or_empty_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing.jsonl"
            self.assertEqual(read_recent_jsonl(path, limit=5), [])

            path.write_text("", encoding="utf-8")
            self.assertEqual(read_recent_jsonl(path, limit=5), [])

    def test_read_recent_jsonl_skips_broken_lines(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "broken.jsonl"
            path.write_text(
                "\n".join(
                    [
                        json.dumps({"id": 1}, ensure_ascii=False),
                        "{broken json}",
                        json.dumps({"id": 2}, ensure_ascii=False),
                        "[]",
                    ]
                ),
                encoding="utf-8",
            )

            items = read_recent_jsonl(path, limit=5)

        self.assertEqual(items, [{"id": 1}, {"id": 2}])
