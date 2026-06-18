"""Testes do token de acesso (HMAC) e da checagem de credenciais."""

from app.security import credentials_match, issue_token, verify_token

_SECRET = "test-secret"


def test_issue_and_verify_roundtrip() -> None:
    token = issue_token("vendedor", _SECRET, ttl_seconds=3600, now=1000.0)
    assert verify_token(token, _SECRET, now=1000.0) == "vendedor"


def test_expired_token_is_invalid() -> None:
    token = issue_token("vendedor", _SECRET, ttl_seconds=10, now=1000.0)
    assert verify_token(token, _SECRET, now=2000.0) is None


def test_tampered_token_is_invalid() -> None:
    token = issue_token("vendedor", _SECRET, ttl_seconds=3600, now=1000.0)
    assert verify_token(token + "x", _SECRET, now=1000.0) is None
    assert verify_token(token, "outro-secret", now=1000.0) is None


def test_malformed_token_is_invalid() -> None:
    assert verify_token("sem-formato", _SECRET) is None


def test_credentials_match() -> None:
    assert credentials_match("u", "p", expected_user="u", expected_pass="p")
    assert not credentials_match("u", "x", expected_user="u", expected_pass="p")
    assert not credentials_match("x", "p", expected_user="u", expected_pass="p")
