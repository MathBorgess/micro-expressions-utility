"""Dublê do Ollama: devolve um relatório Markdown estático com os cabeçalhos obrigatórios."""

STATIC_REPORT_MARKDOWN = """# Relatório de Análise Comercial

## 1. Comportamentos Observados
- [00:00:05] Contato visual reduzido durante menção de preço (vídeo, conf=0.75).

## 2. Linha do Tempo
- 00:00:00-00:00:10: Discussão de produto e preço.

## 3. Mudanças de Comportamento
- Aumento de latência de resposta após custo de implementação.

## 4. Hipóteses Interpretativas
- O padrão visual **pode indicar** processamento cognitivo ou incerteza; alternativa: distração.

## 5. Contexto Conversacional
- Cliente verbalizou preocupação com orçamento (transcrição).

## 6. Confiança e Limitações
- Confiança moderada (0.65). Vídeo único ângulo; sem gaze 3D calibrado.

## 7. Perguntas de Follow-up Sugeridas
- "O que pesaria mais na decisão: custo inicial ou ROI em 12 meses?"

## 8. Oportunidades e Coaching
- Ancorar valor antes de detalhar custos de implementação.
"""


def generate_report(prompt: str = "", *, temperature: float = 0.7) -> str:
    """Simula a resposta do Ollama, ignorando o prompt e devolvendo Markdown fixo."""
    return STATIC_REPORT_MARKDOWN
