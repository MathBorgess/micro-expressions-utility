"""Testes do scaffold de avaliação de frases proibidas."""

from app.core.prompt import FORBIDDEN_EXAMPLE_PHRASES
from scripts.eval.forbidden_phrase_rate import forbidden_phrase_rate


def test_rate_zero_on_clean_report() -> None:
    clean = "## 1. Comportamentos Observados\nObservação neutra."
    assert forbidden_phrase_rate(clean, FORBIDDEN_EXAMPLE_PHRASES) == 0.0


def test_rate_one_on_bad_report() -> None:
    bad = "O cliente odiou o produto."
    assert forbidden_phrase_rate(bad, FORBIDDEN_EXAMPLE_PHRASES) == 1.0
