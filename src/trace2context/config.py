from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path


def load_env_file(path: Path | str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    model: str = "gpt-5.4"
    api_mode: str = "responses"

    @classmethod
    def from_env(cls, env_file: Path | str = ".env") -> Settings:
        load_env_file(env_file)
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("TRACE2CONTEXT_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("TRACE2CONTEXT_API_KEY")
        model = os.getenv("TRACE2CONTEXT_MODEL", "gpt-5.4")
        api_mode = os.getenv("TRACE2CONTEXT_API_MODE", "responses")

        if not base_url:
            raise RuntimeError("Missing OPENAI_BASE_URL or TRACE2CONTEXT_BASE_URL.")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY or TRACE2CONTEXT_API_KEY.")
        if api_mode not in {"responses", "chat_completions"}:
            raise RuntimeError("TRACE2CONTEXT_API_MODE must be `responses` or `chat_completions`.")
        return cls(
            base_url=base_url.rstrip("/"),
            api_key=api_key,
            model=model,
            api_mode=api_mode,
        )

    def with_model(self, model: str | None) -> Settings:
        if not model:
            return self
        return replace(self, model=model)

    def with_api_mode(self, api_mode: str | None) -> Settings:
        if not api_mode:
            return self
        if api_mode not in {"responses", "chat_completions"}:
            raise RuntimeError("API mode must be `responses` or `chat_completions`.")
        return replace(self, api_mode=api_mode)
