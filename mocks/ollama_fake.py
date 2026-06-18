"""Dublê do Ollama: devolve um relatório Markdown estático com os cabeçalhos obrigatórios."""

STATIC_REPORT_MARKDOWN = """# Relatório de Análise Comercial

## 1. Resumo Executivo
O cliente demonstrou interesse no produto, mas levantou objeções relacionadas a preço.

## 2. Objeções Identificadas
* **Preço**: cliente sinalizou que o valor está acima do orçamento (00:05:12).

## 3. Momentos de Alto Engajamento
1. 00:00:00 - Cliente elogia o produto.

## 4. Próximos Passos Recomendados
* Enviar proposta revisada com condições de preço.
"""


def generate_report(prompt: str = "", *, temperature: float = 0.7) -> str:
    """Simula a resposta do Ollama, ignorando o prompt e devolvendo Markdown fixo."""
    return STATIC_REPORT_MARKDOWN
