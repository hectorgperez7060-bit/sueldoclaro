"""Emisión y validación de JWT (access 15 min) + refresh rotativo.

El access token lleva el ``tenant_id`` activo (claim ``tid``) que el middleware
usa para setear el contexto RLS. El refresh se guarda con su ``jti`` en la tabla ``refresh_token``
(ver ``infrastructure.security.refresh_store``) para poder rotarlo y revocarlo.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Optional

import jwt

from config.settings import get_settings

_settings = get_settings()


@dataclass(frozen=True)
class TokenPar:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def _encode(payload: dict, ttl: int) -> str:
    now = int(time.time())
    body = {**payload, "iat": now, "exp": now + ttl}
    return jwt.encode(body, _settings.jwt_secret, algorithm=_settings.jwt_algorithm)


def decode(token: str) -> dict:
    return jwt.decode(token, _settings.jwt_secret, algorithms=[_settings.jwt_algorithm])


def emitir_access(usuario_id: str, tenant_id: Optional[str], rol: Optional[str]) -> str:
    return _encode(
        {"sub": usuario_id, "tid": tenant_id, "rol": rol, "typ": "access"},
        _settings.access_token_ttl_seconds,
    )


def emitir_refresh(usuario_id: str, tenant_id: Optional[str] = None,
                   rol: Optional[str] = None, jti: Optional[str] = None) -> tuple[str, str]:
    jti = jti or uuid.uuid4().hex
    token = _encode(
        {"sub": usuario_id, "tid": tenant_id, "rol": rol, "jti": jti, "typ": "refresh"},
        _settings.refresh_token_ttl_seconds,
    )
    return token, jti
