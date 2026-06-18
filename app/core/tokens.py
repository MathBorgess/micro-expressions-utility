"""Estimativa de tokens (heurística pura, sem rede).

Usada por padrão no CI/dev. Em produção (extra `ml`), o contador real baseado em `tiktoken`
vive em ``app/integrations/tiktoken_counter.py`` e é injetado no pipeline pela factory.
A aproximação ~4 caracteres/token é próxima o suficiente para decidir a compressão de contexto.
"""

import math

CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Aproxima a contagem de tokens de um texto (~1 token a cada 4 caracteres)."""
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, math.ceil(len(stripped) / CHARS_PER_TOKEN))
