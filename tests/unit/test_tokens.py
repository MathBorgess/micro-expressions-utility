"""Testes da estimativa de tokens."""

from app.core.tokens import estimate_tokens


def test_empty_is_zero() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("   ") == 0


def test_minimum_is_one() -> None:
    assert estimate_tokens("a") == 1
    assert estimate_tokens("abcd") == 1


def test_monotonic() -> None:
    assert estimate_tokens("x" * 100) > estimate_tokens("x" * 10)
