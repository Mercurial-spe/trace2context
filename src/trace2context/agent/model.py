from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from trace2context.config import Settings


@dataclass(frozen=True)
class ChatResponse:
    content: str
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


class ChatModelClient:
    """Minimal OpenAI-compatible chat completions client."""

    def __init__(
        self,
        settings: Settings,
        timeout_seconds: int = 45,
        max_retries: int = 1,
    ) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries

    def chat(self, messages: list[dict[str, str]], max_tokens: int = 1200) -> ChatResponse:
        endpoint, payload = self._build_request_payload(messages, max_tokens)
        request = urllib.request.Request(
            f"{self.settings.base_url}/{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.settings.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        last_error: RuntimeError | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._send(request)
            except RuntimeError as exc:
                last_error = exc
                if attempt >= self.max_retries or not _is_retryable_error(exc):
                    raise
                time.sleep(1.5 * (attempt + 1))

        raise last_error or RuntimeError("Chat completion failed.")

    def _build_request_payload(
        self,
        messages: list[dict[str, str]],
        max_tokens: int,
    ) -> tuple[str, dict[str, Any]]:
        if self.settings.api_mode == "responses":
            return (
                "responses",
                {
                    "model": self.settings.model,
                    "input": messages,
                    "max_output_tokens": max_tokens,
                    "store": False,
                },
            )

        return (
            "chat/completions",
            {
                "model": self.settings.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0,
            },
        )

    def _send(self, request: urllib.request.Request) -> ChatResponse:
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Model request failed with HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Model request failed: {exc}") from exc
        except TimeoutError as exc:
            raise RuntimeError(f"Model request timed out: {exc}") from exc

        if "output" in data:
            return ChatResponse(
                content=_extract_responses_text(data),
                usage=data.get("usage", {}),
                raw=data,
            )
        message = data["choices"][0]["message"]
        return ChatResponse(
            content=message.get("content") or "",
            usage=data.get("usage", {}),
            raw=data,
        )


def _is_retryable_error(error: RuntimeError) -> bool:
    text = str(error)
    retryable_markers = [
        "HTTP 429",
        "HTTP 500",
        "HTTP 502",
        "HTTP 503",
        "HTTP 504",
        "timed out",
    ]
    return any(marker in text for marker in retryable_markers)


def _extract_responses_text(data: dict[str, Any]) -> str:
    if isinstance(data.get("output_text"), str):
        return data["output_text"]

    parts: list[str] = []
    for item in data.get("output", []):
        for content_part in item.get("content", []):
            text = content_part.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "\n".join(parts)
