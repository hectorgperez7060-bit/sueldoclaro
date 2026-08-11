"""Dependencias de autenticación/autorización.

El tenant activo se resuelve SIEMPRE del JWT (claim ``tid``), nunca del body ni
de query params (regla de multi-tenancy del prompt).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from infrastructure.security.tokens import decode

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    usuario_id: str
    tenant_id: Optional[str]
    rol: Optional[str]


async def get_principal(
    request: Request,
    cred: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Principal:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token")
    try:
        payload = decode(cred.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    if payload.get("typ") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere un access token")
    principal = Principal(payload["sub"], payload.get("tid"), payload.get("rol"))
    # Deja el tenant en el request.state para middleware/auditoría
    request.state.tenant_id = principal.tenant_id
    request.state.usuario_id = principal.usuario_id
    return principal


async def require_tenant(principal: Principal = Depends(get_principal)) -> Principal:
    if not principal.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El token no tiene empresa activa")
    return principal


def require_rol(*roles: str):
    async def _dep(principal: Principal = Depends(require_tenant)) -> Principal:
        if principal.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Permiso insuficiente")
        return principal
    return _dep
