from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import httpx
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt

from app.ciip_api.schemas.users import UserContext
from app.utils.config import get_settings


security_scheme = HTTPBearer()


async def _fetch_jwks(jwks_url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        return response.json()


def _get_role_from_claims(claims: Dict[str, Any]) -> str:
    if role := claims.get("role"):
        return role
    for key in ("app_metadata", "user_metadata"):
        nested = claims.get(key) or {}
        if isinstance(nested, dict) and nested.get("role"):
            return nested["role"]
    return "user"


async def _decode_with_jwks(
    token: str, jwks_url: str, audience: Optional[str]
) -> Dict[str, Any]:
    unverified_header = jwt.get_unverified_header(token)
    jwks = await _fetch_jwks(jwks_url)
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            public_key = jwk.construct(key)
            try:
                return jwt.decode(
                    token,
                    public_key.to_pem().decode(),
                    algorithms=[unverified_header.get("alg", "RS256")],
                    audience=audience,
                    options={"verify_aud": audience is not None},
                )
            except JWTError as exc:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
                ) from exc
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )


def _decode_with_secret(
    token: str, secret: str, audience: Optional[str]
) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=audience,
            options={"verify_aud": audience is not None},
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> UserContext:
    settings = get_settings()
    token = credentials.credentials
    claims: Dict[str, Any]
    if settings.supabase_jwks_url:
        claims = await _decode_with_jwks(
            token, settings.supabase_jwks_url, settings.supabase_audience
        )
    elif settings.supabase_jwt_secret:
        claims = _decode_with_secret(
            token, settings.supabase_jwt_secret, settings.supabase_audience
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth not configured",
        )

    user_id = claims.get("sub")
    email = claims.get("email")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
    role = _get_role_from_claims(claims)
    return UserContext(id=user_id, email=email, role=role)


def require_roles(allowed: Iterable[str]):
    def dependency(user: UserContext = Depends(get_current_user)) -> UserContext:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
            )
        return user

    return dependency
