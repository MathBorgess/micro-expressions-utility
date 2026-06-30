"""Métrica binária de taxa de frases proibidas em relatórios Markdown."""

from app.core.report import contains_forbidden_phrases


def forbidden_phrase_rate(markdown: str, phrases: tuple[str, ...]) -> float:
    """Retorna 1.0 se alguma frase proibida aparecer, senão 0.0."""
    return 1.0 if contains_forbidden_phrases(markdown, phrases) else 0.0
