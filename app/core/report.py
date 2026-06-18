"""Validação estrutural do relatório Markdown gerado pelo LLM (regex dos cabeçalhos)."""

import re

# (padrão regex, rótulo legível) — todos obrigatórios na saída do LLM.
REQUIRED_HEADERS: tuple[tuple[str, str], ...] = (
    (r"#\s*Relatório de Análise Comercial", "# Relatório de Análise Comercial"),
    (r"##\s*1\.\s*Resumo Executivo", "## 1. Resumo Executivo"),
    (r"##\s*2\.\s*Objeções Identificadas", "## 2. Objeções Identificadas"),
    (r"##\s*3\.\s*Momentos de Alto Engajamento", "## 3. Momentos de Alto Engajamento"),
    (r"##\s*4\.\s*Próximos Passos Recomendados", "## 4. Próximos Passos Recomendados"),
)


def missing_headers(markdown: str) -> list[str]:
    """Lista os cabeçalhos obrigatórios ausentes na resposta."""
    return [label for pattern, label in REQUIRED_HEADERS if not re.search(pattern, markdown)]


def validate_report(markdown: str) -> bool:
    """True se a resposta contém todos os cabeçalhos obrigatórios e não está vazia."""
    return bool(markdown.strip()) and not missing_headers(markdown)
