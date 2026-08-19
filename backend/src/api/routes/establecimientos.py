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
    )


@router.get("", response_model=list[EstablecimientoOut])
async def listar(incluir_inactivos: bool = False, principal: Principal = Depends(require_tenant)):
    async with tenant_session(principal.tenant_id) as s:
        return [_out(e) for e in await EstablecimientoRepo(s).listar(incluir_inactivos)]


@router.post("", response_model=EstablecimientoOut, status_code=201)
async def crear(body: EstablecimientoIn, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    tid = uuid.UUID(principal.tenant_id)
    async with tenant_session(principal.tenant_id) as s:
        e = await EstablecimientoRepo(s).crear(tid, body.model_dump())
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
        for campo, valor in body.model_dump().items():
            setattr(e, campo, valor)
        await AuditRepo(s).registrar(
            accion="actualizar", entidad="establecimiento", entidad_id=str(e.id), tenant_id=tid,
            usuario_id=uuid.UUID(principal.usuario_id),
        )
        return _out(e)
