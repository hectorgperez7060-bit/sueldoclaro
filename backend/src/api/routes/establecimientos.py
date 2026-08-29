"""Domicilios de trabajo separados por empresa."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import Principal, require_rol, require_tenant
from application.dto.schemas import EstablecimientoIn, EstablecimientoOut
from infrastructure.database.repositories import AuditRepo, EstablecimientoRepo
from infrastructure.database.session import tenant_session

router = APIRouter(prefix="/establecimientos", tags=["establecimientos"])


def _out(e) -> EstablecimientoOut:
    return EstablecimientoOut(
        id=str(e.id), nombre=e.nombre, domicilio=e.domicilio,
        localidad=e.localidad or "", provincia=e.provincia or "",
        actividad=e.actividad or "", activo=e.activo,
        art_nombre=e.art_nombre or "",
        art_alicuota_pct=e.art_alicuota_pct,
        art_suma_fija=e.art_suma_fija,
        art_vigencia_desde=e.art_vigencia_desde,
        art_vigencia_hasta=e.art_vigencia_hasta,
        art_comprobante_ref=e.art_comprobante_ref or "",
    )


@router.get("", response_model=list[EstablecimientoOut])
async def listar(incluir_inactivos: bool = False, principal: Principal = Depends(require_tenant)):
    async with tenant_session(principal.tenant_id) as s:
        return [_out(e) for e in await EstablecimientoRepo(s).listar(incluir_inactivos)]


@router.post("", response_model=EstablecimientoOut, status_code=201)
async def crear(body: EstablecimientoIn, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    tid = uuid.UUID(principal.tenant_id)
    async with tenant_session(principal.tenant_id) as s:
        datos = body.model_dump()
        if datos["art_vigencia_desde"] and datos["art_vigencia_hasta"] and datos["art_vigencia_hasta"] < datos["art_vigencia_desde"]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La vigencia final de ART no puede ser anterior a la inicial")
        e = await EstablecimientoRepo(s).crear(tid, datos)
        await AuditRepo(s).registrar(
            accion="crear", entidad="establecimiento", entidad_id=str(e.id), tenant_id=tid,
            usuario_id=uuid.UUID(principal.usuario_id),
        )
        return _out(e)


@router.put("/{establecimiento_id}", response_model=EstablecimientoOut)
async def actualizar(establecimiento_id: str, body: EstablecimientoIn,
                     principal: Principal = Depends(require_rol("admin", "liquidador"))):
    tid = uuid.UUID(principal.tenant_id)
    try:
        eid = uuid.UUID(establecimiento_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Establecimiento inválido") from exc
    async with tenant_session(principal.tenant_id) as s:
        repo = EstablecimientoRepo(s)
        e = await repo.obtener(tid, eid)
        if e is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Establecimiento no encontrado")
        datos = body.model_dump()
        if datos["art_vigencia_desde"] and datos["art_vigencia_hasta"] and datos["art_vigencia_hasta"] < datos["art_vigencia_desde"]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La vigencia final de ART no puede ser anterior a la inicial")
        for campo, valor in datos.items():
            setattr(e, campo, valor)
        await AuditRepo(s).registrar(
            accion="actualizar", entidad="establecimiento", entidad_id=str(e.id), tenant_id=tid,
            usuario_id=uuid.UUID(principal.usuario_id),
        )
        return _out(e)
