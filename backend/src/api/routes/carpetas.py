"""Consulta de carpetas mensuales versionadas. Sin edición directa."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies.auth import Principal, require_tenant
from domain.value_objects.periodo import Periodo
from infrastructure.database import models as m
from infrastructure.database.repositories import CarpetaMensualRepo
from infrastructure.database.session import tenant_session

router = APIRouter(prefix="/carpetas-mensuales", tags=["carpetas mensuales"])


def _out(c: m.CarpetaMensual) -> dict:
    return {
        "id": str(c.id), "periodo": c.periodo, "version": c.version,
        "estado": c.estado, "hash_sha256": c.hash_sha256,
        "liquidacion_id": str(c.liquidacion_id) if c.liquidacion_id else None,
        "contenido": c.contenido,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get("")
async def listar(
    periodo: str = Query(..., description="Período AAAA-MM"),
    principal: Principal = Depends(require_tenant),
):
    try:
        if str(Periodo.desde_texto(periodo)) != periodo:
            raise ValueError
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "El período debe tener formato AAAA-MM"
        ) from exc
    tid = uuid.UUID(principal.tenant_id)
    async with tenant_session(principal.tenant_id) as s:
        return [_out(c) for c in await CarpetaMensualRepo(s).listar_periodo(tid, periodo)]


@router.get("/{carpeta_id}")
async def obtener(
    carpeta_id: str,
    principal: Principal = Depends(require_tenant),
):
    try:
        cid = uuid.UUID(carpeta_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Identificador inválido") from exc
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await s.get(m.CarpetaMensual, cid)
        if carpeta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Carpeta mensual no encontrada")
        return _out(carpeta)
