import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from core.llm_helper import LLMHelper


def completion(content, finish_reason):
    return SimpleNamespace(
        choices=[SimpleNamespace(
            message=SimpleNamespace(content=content),
            finish_reason=finish_reason,
        )]
    )


class TestLLMChatContinuation(unittest.TestCase):
    def setUp(self):
        self.helper = LLMHelper()
        self.helper.client = MagicMock()

    def test_continues_mislabeled_truncated_response(self):
        self.helper.client.chat.completions.create.side_effect = [
            completion("根据流年（2026丙午年", "stop"),
            completion("的变化，建议先做好准备。", "stop"),
        ]

        answer = self.helper.chat("适合换工作吗")

        self.assertEqual(answer, "根据流年（2026丙午年\n的变化，建议先做好准备。")
        self.assertEqual(self.helper.client.chat.completions.create.call_count, 2)

    def test_keeps_complete_stop_response_as_is(self):
        self.helper.client.chat.completions.create.return_value = completion("建议先准备，再择机行动。", "stop")

        answer = self.helper.chat("适合换工作吗")

        self.assertEqual(answer, "建议先准备，再择机行动。")
        self.assertEqual(self.helper.client.chat.completions.create.call_count, 1)


if __name__ == "__main__":
    unittest.main()
