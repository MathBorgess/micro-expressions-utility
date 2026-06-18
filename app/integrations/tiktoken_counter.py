"""Contagem de tokens real com tiktoken (codificação do GPT-4 como aproximação)."""

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def _encoding() -> Any:
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    return len(_encoding().encode(text))
