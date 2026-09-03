"""Store de refresh tokens en la base.

Antes esto vivia en un diccionario en memoria. En Vercel cada request puede
caer en una instancia distinta y cada instancia tiene su propia memoria: al
renovar la sesion el jti no aparecia, la API devolvia 401 y la aplicacion
echaba al usuario en medio de la carga, borrandole lo que estaba escribiendo.
La base es la unica memoria que comparten todas las instancias.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, text

from config.settings import get_settings
from infrastructure.database import models as m
from infrastructure.database.session import plain_session

_settings = get_settings()


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


async def guardar(jti: str, usuario_id: str) -> None:
    """Registra un refresh recien emitido y limpia los vencidos del usuario."""
    uid = uuid.UUID(str(usuario_id))
    expira = _ahora() + timedelta(seconds=_settings.refresh_token_ttl_seconds)
    async with plain_session() as s:
        await s.execute(
            delete(m.RefreshToken).where(
                m.RefreshToken.usuario_id == uid,
                m.RefreshToken.expira_en < _ahora(),
            )
        )
        s.add(m.RefreshToken(jti=jti, usuario_id=uid, expira_en=expira))


async def consumir(jti: str | None, usuario_id: str | None) -> bool:
    """Valida y quema el refresh en un solo paso (rotacion sin carrera).

    Devuelve True solo si el jti existia, era de ese usuario y no habia
    vencido. El DELETE ... RETURNING garantiza que dos pedidos simultaneos con
    el mismo refresh no puedan renovarse los dos.
    """
    if not jti or not usuario_id:
        return False
    try:
        uid = uuid.UUID(str(usuario_id))
    except (ValueError, AttributeError):
        return False
    async with plain_session() as s:
        fila = await s.execute(
            text(
                "DELETE FROM refresh_token "
                "WHERE jti = :jti AND usuario_id = :uid AND expira_en > now() "
                "RETURNING jti"
            ),
            {"jti": jti, "uid": str(uid)},
        )
        return fila.first() is not None


async def revocar_todos(usuario_id: str) -> None:
    """Cierra todas las sesiones abiertas de un usuario."""
    async with plain_session() as s:
        await s.execute(
            delete(m.RefreshToken).where(
                m.RefreshToken.usuario_id == uuid.UUID(str(usuario_id))
            )
        )
