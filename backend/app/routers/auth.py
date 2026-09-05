from fastapi import APIRouter, Depends, Response

from app.config import settings
from app.dependencies import get_auth_service, get_current_user, get_refresh_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])

REFRESH_COOKIE_MAX_AGE = settings.jwt_refresh_token_expire_days * 86400


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        secure=False,  # Set True in production behind HTTPS
        samesite="strict",
        path="/api/auth",
        max_age=REFRESH_COOKIE_MAX_AGE,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
):
    token_response, refresh_token = await service.login(body)
    _set_refresh_cookie(response, refresh_token)
    return token_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    token: str = Depends(get_refresh_token),
    service: AuthService = Depends(get_auth_service),
):
    token_response, new_refresh_token = await service.refresh(token)
    _set_refresh_cookie(response, new_refresh_token)
    return token_response


@router.post("/logout")
async def logout(response: Response, _: User = Depends(get_current_user)):
    response.delete_cookie(key="refresh_token", path="/api/auth")
    return {"message": "Logged out"}
