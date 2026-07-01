from __future__ import annotations

import tiktoken


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    """Estimate tokens for a text chunk.

    Falls back to `cl100k_base` when the requested model is unknown to tiktoken.
    """
    if not text:
        return 0
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
