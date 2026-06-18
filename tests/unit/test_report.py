"""Testes da validação estrutural do relatório."""

from app.core.report import missing_headers, validate_report
from mocks.ollama_fake import STATIC_REPORT_MARKDOWN


def test_static_report_is_valid() -> None:
    assert validate_report(STATIC_REPORT_MARKDOWN)


def test_empty_is_invalid() -> None:
    assert not validate_report("")


def test_missing_headers_detected() -> None:
    partial = "# Relatório de Análise Comercial\n## 1. Resumo Executivo\n"
    missing = missing_headers(partial)
    assert "## 2. Objeções Identificadas" in missing
    assert not validate_report(partial)
