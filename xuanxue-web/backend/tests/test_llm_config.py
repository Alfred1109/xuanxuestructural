import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from core import llm_config
from core.llm_config import (
    MINIMAX_DEFAULT_MAX_COMPLETION_TOKENS,
    load_llm_config,
)

with patch.dict(os.environ, {"LLM_PROVIDER": "ark", "LLM_API_KEY": "", "ARK_API_KEY": ""}), patch.object(
    llm_config, "_read_dotenv", return_value={}
):
    from core.llm_helper import LLMHelper


class TestLLMConfig(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(prefix="xuanxue-llm-config-test-")
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def write_settings(self, env):
        path = self.root / "settings.json"
        path.write_text(json.dumps({"env": env}), encoding="utf-8")
        return path

    def test_minimax_reads_claude_env_without_falling_back_to_ark_key(self):
        config_path = self.write_settings({
            "ANTHROPIC_AUTH_TOKEN": "settings-secret",
            "ANTHROPIC_BASE_URL": "https://api.minimaxi.com/anthropic",
            "ANTHROPIC_MODEL": "MiniMax-M3.1-Flash-Preview",
        })
        config = load_llm_config(
            {
                "LLM_PROVIDER": "minimax",
                "LLM_CONFIG_FILE": str(config_path),
                "ARK_API_KEY": "ark-secret-must-not-be-used",
            },
            dotenv_path=self.root / "missing.env",
        )

        self.assertEqual(config.provider, "minimax")
        self.assertEqual(config.api_key, "settings-secret")
        self.assertEqual(config.base_url, "https://api.minimaxi.com/v1")
        self.assertEqual(config.text_model, "MiniMax-M3.1-Flash-Preview")
        self.assertEqual(config.vision_model, "MiniMax-M3.1-Flash-Preview")
        self.assertNotIn("settings-secret", repr(config))
        self.assertIsNone(load_llm_config({"LLM_PROVIDER": "minimax", "ARK_API_KEY": "ark-only"}, self.root / "missing.env").api_key)

    def test_nonempty_process_env_then_dotenv_then_settings_precedence(self):
        settings_path = self.write_settings({
            "ANTHROPIC_AUTH_TOKEN": "settings-key",
            "ANTHROPIC_BASE_URL": "https://settings.example/anthropic",
            "ANTHROPIC_MODEL": "settings-model",
            "LLM_MAX_COMPLETION_TOKENS": "10000",
        })
        dotenv_path = self.root / ".env"
        dotenv_path.write_text(
            "LLM_PROVIDER=minimax\n"
            f"LLM_CONFIG_FILE={settings_path}\n"
            "LLM_API_KEY=dotenv-key\n"
            "LLM_BASE_URL=https://dotenv.example/anthropic\n"
            "LLM_TEXT_MODEL=dotenv-model\n"
            "LLM_MAX_COMPLETION_TOKENS=40960\n",
            encoding="utf-8",
        )
        config = load_llm_config(
            {
                "LLM_PROVIDER": "minimax",
                "LLM_API_KEY": "",
                "LLM_TEXT_MODEL": "process-model",
                "LLM_MAX_COMPLETION_TOKENS": "24576",
            },
            dotenv_path=dotenv_path,
        )

        self.assertEqual(config.api_key, "dotenv-key")
        self.assertEqual(config.base_url, "https://dotenv.example/v1")
        self.assertEqual(config.text_model, "process-model")
        self.assertEqual(config.vision_model, "process-model")
        self.assertEqual(config.max_completion_tokens, 24576)

        process_overrides = load_llm_config(
            {
                "LLM_PROVIDER": "minimax",
                "LLM_API_KEY": "process-key",
                "LLM_BASE_URL": "https://process.example/anthropic",
                "LLM_VISION_MODEL": "process-vision",
            },
            dotenv_path=dotenv_path,
        )
        self.assertEqual(process_overrides.api_key, "process-key")
        self.assertEqual(process_overrides.base_url, "https://process.example/v1")
        self.assertEqual(process_overrides.vision_model, "process-vision")

        config = load_llm_config(
            {"LLM_PROVIDER": "minimax", "LLM_CONFIG_FILE": str(settings_path)},
            dotenv_path=self.root / "missing.env",
        )
        self.assertEqual(config.api_key, "settings-key")
        self.assertEqual(config.base_url, "https://settings.example/v1")
        self.assertEqual(config.text_model, "settings-model")
        self.assertEqual(config.max_completion_tokens, 10000)

    def test_minimax_budget_defaults_safely_and_ark_environment_semantics_remain(self):
        minimax = load_llm_config({"LLM_PROVIDER": "minimax", "LLM_MAX_COMPLETION_TOKENS": "invalid"}, self.root / "missing.env")
        self.assertEqual(minimax.max_completion_tokens, MINIMAX_DEFAULT_MAX_COMPLETION_TOKENS)

        ark = load_llm_config(
            {
                "LLM_PROVIDER": "ark",
                "ARK_API_KEY": "ark-key",
                "ARK_TEXT_MODEL": "ark-text",
                "ARK_VISION_MODEL": "ark-vision",
            },
            self.root / "missing.env",
        )
        self.assertEqual(ark.provider, "ark")
        self.assertEqual(ark.api_key, "ark-key")
        self.assertEqual(ark.base_url, "https://ark.cn-beijing.volces.com/api/v3")
        self.assertEqual(ark.text_model, "ark-text")
        self.assertEqual(ark.vision_model, "ark-vision")

    def test_completion_helper_uses_one_minimax_budget_and_preserves_ark_max_tokens(self):
        create = Mock(return_value="response")
        helper = LLMHelper.__new__(LLMHelper)
        helper.provider = "minimax"
        helper.max_completion_tokens = 32768
        helper.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

        response = helper._create_completion(model="MiniMax-M3.1-Flash-Preview", messages=[], max_tokens=1200, temperature=0.2)

        self.assertEqual(response, "response")
        self.assertEqual(create.call_args.kwargs["max_completion_tokens"], 32768)
        self.assertNotIn("max_tokens", create.call_args.kwargs)
        self.assertEqual(create.call_args.kwargs["temperature"], 0.2)

        create.reset_mock()
        helper.provider = "ark"
        helper._create_completion(model="ark-model", messages=[], max_tokens=1200)
        self.assertEqual(create.call_args.kwargs["max_tokens"], 1200)
        self.assertNotIn("max_completion_tokens", create.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
