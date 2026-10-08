"""Resolve provider-specific LLM settings without exposing credential values."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional
from urllib.parse import urlsplit, urlunsplit

from dotenv import dotenv_values


MINIMAX_DEFAULT_BASE_URL = "https://api.minimaxi.com/v1"
MINIMAX_DEFAULT_MODEL = "MiniMax-M3.1-Flash-Preview"
MINIMAX_DEFAULT_MAX_COMPLETION_TOKENS = 32768


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    base_url: str
    api_key: Optional[str] = field(default=None, repr=False)
    text_model: str = ""
    vision_model: str = ""
    max_completion_tokens: int = MINIMAX_DEFAULT_MAX_COMPLETION_TOKENS


def _read_dotenv(path_value: Optional[str]) -> Mapping[str, str]:
    if not path_value:
        return {}
    try:
        values = dotenv_values(dotenv_path=Path(path_value).expanduser())
    except (OSError, UnicodeError, TypeError, ValueError):
        return {}
    return {str(key): value for key, value in values.items() if isinstance(value, str)}


def _read_config_env(path_value: Optional[str]) -> Mapping[str, str]:
    if not path_value:
        return {}
    try:
        with Path(path_value).expanduser().open("r", encoding="utf-8") as file:
            document = json.load(file)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return {}
    values = document.get("env") if isinstance(document, dict) else None
    if not isinstance(values, dict):
        return {}
    return {str(key): value for key, value in values.items() if isinstance(value, str)}


def _first_value(
    process_env: Mapping[str, str],
    dotenv_env: Mapping[str, str],
    file_env: Mapping[str, str],
    keys: tuple[str, ...],
    default: Optional[str] = None,
) -> Optional[str]:
    for source in (process_env, dotenv_env, file_env):
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return default


def _normalize_minimax_base_url(value: str) -> str:
    base_url = value.rstrip("/")
    parts = urlsplit(base_url)
    if parts.path.rstrip("/").endswith("/anthropic"):
        path = parts.path.rstrip("/")[:-len("/anthropic")] + "/v1"
        return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))
    return base_url


def _completion_budget(
    process_env: Mapping[str, str],
    dotenv_env: Mapping[str, str],
    file_env: Mapping[str, str],
) -> int:
    raw = _first_value(process_env, dotenv_env, file_env, ("LLM_MAX_COMPLETION_TOKENS",))
    if raw is None:
        return MINIMAX_DEFAULT_MAX_COMPLETION_TOKENS
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return MINIMAX_DEFAULT_MAX_COMPLETION_TOKENS
    return value if value > 0 else MINIMAX_DEFAULT_MAX_COMPLETION_TOKENS


def load_llm_config(
    environ: Optional[Mapping[str, str]] = None,
    dotenv_path: Optional[str | Path] = None,
) -> LLMConfig:
    """Resolve process env, project .env, then optional Claude settings values."""
    process_env = os.environ if environ is None else environ
    if dotenv_path is None:
        dotenv_path = Path(__file__).resolve().parents[3] / ".env"
    dotenv_env = _read_dotenv(str(dotenv_path))
    provider = (_first_value(process_env, dotenv_env, {}, ("LLM_PROVIDER",)) or "ark").strip().lower()
    settings_path = _first_value(process_env, dotenv_env, {}, ("LLM_CONFIG_FILE",)) if provider == "minimax" else None
    file_env = _read_config_env(settings_path)

    if provider == "minimax":
        api_key = _first_value(
            process_env,
            dotenv_env,
            file_env,
            ("LLM_API_KEY", "ANTHROPIC_AUTH_TOKEN"),
        )
        base_url = _normalize_minimax_base_url(
            _first_value(
                process_env,
                dotenv_env,
                file_env,
                ("LLM_BASE_URL", "ANTHROPIC_BASE_URL"),
                MINIMAX_DEFAULT_BASE_URL,
            )
        )
        text_model = _first_value(
            process_env,
            dotenv_env,
            file_env,
            ("LLM_TEXT_MODEL", "ANTHROPIC_MODEL"),
            MINIMAX_DEFAULT_MODEL,
        )
        vision_model = _first_value(
            process_env,
            dotenv_env,
            file_env,
            ("LLM_VISION_MODEL", "ANTHROPIC_VISION_MODEL"),
        ) or text_model
        return LLMConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            text_model=text_model,
            vision_model=vision_model,
            max_completion_tokens=_completion_budget(process_env, dotenv_env, file_env),
        )

    # Preserve the existing Ark and OpenAI-compatible provider environment
    # semantics; the Claude settings file is intentionally not a key fallback.
    return LLMConfig(
        provider=provider,
        base_url=_first_value(process_env, dotenv_env, {}, ("LLM_BASE_URL",), "https://ark.cn-beijing.volces.com/api/v3"),
        api_key=_first_value(process_env, dotenv_env, {}, ("LLM_API_KEY", "ARK_API_KEY")),
        text_model=_first_value(process_env, dotenv_env, {}, ("LLM_TEXT_MODEL", "ARK_TEXT_MODEL"), "deepseek-v3-2-251201"),
        vision_model=_first_value(process_env, dotenv_env, {}, ("LLM_VISION_MODEL", "ARK_VISION_MODEL"), "doubao-seed-2-0-lite-260428"),
    )
