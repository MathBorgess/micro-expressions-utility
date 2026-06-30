"""Validação estrutural do relatório Markdown gerado pelo LLM (regex dos cabeçalhos)."""

import re

# (padrão regex, rótulo legível) — todos obrigatórios na saída do LLM.
REQUIRED_HEADERS: tuple[tuple[str, str], ...] = (
    (r"#\s*Relatório de Análise Comercial", "# Relatório de Análise Comercial"),
    (r"##\s*1\.\s*Comportamentos Observados", "## 1. Comportamentos Observados"),
    (r"##\s*2\.\s*Linha do Tempo", "## 2. Linha do Tempo"),
    (r"##\s*3\.\s*Mudanças de Comportamento", "## 3. Mudanças de Comportamento"),
    (r"##\s*4\.\s*Hipóteses Interpretativas", "## 4. Hipóteses Interpretativas"),
    (r"##\s*5\.\s*Contexto Conversacional", "## 5. Contexto Conversacional"),
    (r"##\s*6\.\s*Confiança e Limitações", "## 6. Confiança e Limitações"),
    (r"##\s*7\.\s*Perguntas de Follow-up Sugeridas", "## 7. Perguntas de Follow-up Sugeridas"),
    (r"##\s*8\.\s*Oportunidades e Coaching", "## 8. Oportunidades e Coaching"),
)


def missing_headers(markdown: str) -> list[str]:
    """Lista os cabeçalhos obrigatórios ausentes na resposta."""
    return [label for pattern, label in REQUIRED_HEADERS if not re.search(pattern, markdown)]


def contains_forbidden_phrases(markdown: str, phrases: tuple[str, ...]) -> bool:
    lowered = markdown.lower()
    return any(p.lower() in lowered for p in phrases)


def validate_report(markdown: str, *, forbidden_phrases: tuple[str, ...] = ()) -> bool:
    """True se a resposta contém todos os cabeçalhos obrigatórios e não está vazia."""
    if not markdown.strip() or missing_headers(markdown):
        return False
    return not (forbidden_phrases and contains_forbidden_phrases(markdown, forbidden_phrases))
