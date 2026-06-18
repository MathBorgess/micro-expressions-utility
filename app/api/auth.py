"""Endpoint de autenticação básica (`/api/v1/auth`)."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.schemas import LoginRequest, TokenResponse
from app.security import credentials_match, issue_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Login do vendedor (acesso básico)")
def login(payload: LoginRequest, settings: Settings = Depends(get_settings)) -> TokenResponse:
    if not credentials_match(
        payload.username,
        payload.password,
        expected_user=settings.auth_username,
        expected_pass=settings.auth_password,
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="credenciais inválidas")
    token = issue_token(
        payload.username, settings.auth_secret, ttl_seconds=settings.auth_token_ttl_seconds
    )
    return TokenResponse(access_token=token)
