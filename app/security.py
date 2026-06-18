"""Token de acesso simples (HMAC) para a auth básica do MVP.

Formato opaco: ``username:expiry:assinatura``. Sem dependências externas (stdlib).
Não é JWT — é suficiente para o controle de acesso básico do MVP (PRD).
"""

import hashlib
import hmac
import time


def _sign(message: str, secret: str) -> str:
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def issue_token(username: str, secret: str, *, ttl_seconds: int, now: float | None = None) -> str:
    expiry = int((now if now is not None else time.time()) + ttl_seconds)
    message = f"{username}:{expiry}"
    return f"{message}:{_sign(message, secret)}"


def verify_token(token: str, secret: str, *, now: float | None = None) -> str | None:
    """Retorna o username se o token é válido e não expirou; senão ``None``."""
    try:
        username, expiry, signature = token.rsplit(":", 2)
    except ValueError:
        return None
    expected = _sign(f"{username}:{expiry}", secret)
    if not hmac.compare_digest(signature, expected):
        return None
    current = now if now is not None else time.time()
    if int(expiry) < current:
        return None
    return username


def credentials_match(
    username: str, password: str, *, expected_user: str, expected_pass: str
) -> bool:
    user_ok = hmac.compare_digest(username, expected_user)
    pass_ok = hmac.compare_digest(password, expected_pass)
    return user_ok and pass_ok
