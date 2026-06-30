"""Testes da validação estrutural do relatório."""

from app.core.prompt import FORBIDDEN_EXAMPLE_PHRASES
from app.core.report import contains_forbidden_phrases, missing_headers, validate_report
from mocks.ollama_fake import STATIC_REPORT_MARKDOWN


def test_static_report_is_valid() -> None:
    assert validate_report(STATIC_REPORT_MARKDOWN, forbidden_phrases=FORBIDDEN_EXAMPLE_PHRASES)


def test_empty_is_invalid() -> None:
    assert not validate_report("")


def test_missing_headers_detected() -> None:
    partial = "# Relatório de Análise Comercial\n## 1. Comportamentos Observados\n"
    missing = missing_headers(partial)
    assert "## 2. Linha do Tempo" in missing
    assert not validate_report(partial)


def test_forbidden_phrases_detected() -> None:
    bad = "# Relatório\n## 1. Comportamentos Observados\nO cliente perdeu confiança."
    assert contains_forbidden_phrases(bad, FORBIDDEN_EXAMPLE_PHRASES)


def test_new_headers_required() -> None:
    old_style = "# Relatório de Análise Comercial\n## 1. Resumo Executivo\n"
    assert not validate_report(old_style)
