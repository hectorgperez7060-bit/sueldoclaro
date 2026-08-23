"""CRUD de novedades mensuales, aislado por empresa mediante JWT + RLS."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies.auth import Principal, require_rol, require_tenant
from application.dto.schemas import (
    NovedadMensualIn,
    NovedadMensualOut,
    NovedadMensualUpdate,
)
from domain.entities.novedad import DatosNovedadMensual
from infrastructure.database.repositories import AuditRepo, NovedadMensualRepo
from infrastructure.database.session import tenant_session

router = APIRouter(prefix="/novedades", tags=["novedades"])


def _uuid(valor: str, nombre: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Identificador de {nombre} inválido",
        ) from exc


def _to_out(novedad, bloqueada: bool = False) -> NovedadMensualOut:
    return NovedadMensualOut(
        id=str(novedad.id),
        empleado_id=str(novedad.empleado_id),
        periodo=novedad.periodo,
        dias_trabajados=novedad.dias_trabajados,
        faltas_justificadas=novedad.faltas_justificadas,
        faltas_injustificadas=novedad.faltas_injustificadas,
        horas_extra_50=novedad.horas_extra_50,
        horas_extra_100=novedad.horas_extra_100,
        feriados_trabajados=novedad.feriados_trabajados,
        feriados_no_trabajados=novedad.feriados_no_trabajados,
        licencias=novedad.licencias,
        vacaciones=novedad.vacaciones,
        premios=novedad.premios,
        tipo_premio=novedad.tipo_premio,
        descuentos_adicionales=novedad.descuentos_adicionales,
        observaciones=novedad.observaciones,
        adicionales_convencionales=novedad.adicionales_convencionales or [],
        cantidades_adicionales=novedad.cantidades_adicionales or {},
        horas_normales_q1=novedad.horas_normales_q1,
        horas_normales_q2=novedad.horas_normales_q2,
        asistencia_perfecta_q1=novedad.asistencia_perfecta_q1,
        asistencia_perfecta_q2=novedad.asistencia_perfecta_q2,
        feriados_habilitados_q1=novedad.feriados_habilitados_q1,
        feriados_habilitados_q2=novedad.feriados_habilitados_q2,
        feriados_uocra_detalle=novedad.feriados_uocra_detalle or [],
        fcl_criterio_aniversario=novedad.fcl_criterio_aniversario,
        fcl_aprobado_por=novedad.fcl_aprobado_por,
        fcl_fundamento=novedad.fcl_fundamento,
        bloqueada=bloqueada,
    )


@router.post("", response_model=NovedadMensualOut, status_code=201)
async def crear(
    body: NovedadMensualIn,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    tid = _uuid(principal.tenant_id, "empresa")
    empleado_id = _uuid(body.empleado_id, "empleado")
    async with tenant_session(principal.tenant_id) as s:
        try:
            novedad = await NovedadMensualRepo(s).crear(
                tid, empleado_id, body.datos_dominio()
            )
        except LookupError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        await AuditRepo(s).registrar(
            accion="crear", entidad="novedad_mensual", entidad_id=str(novedad.id),
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
            payload_diff={"empleado_id": body.empleado_id, "periodo": body.periodo},
        )
        return _to_out(novedad)


@router.get("", response_model=list[NovedadMensualOut])
async def listar(
    periodo: str = Query(..., description="Período AAAA-MM"),
    principal: Principal = Depends(require_tenant),
):
    # Valida período antes de abrir la consulta.
    DatosNovedadMensual(periodo=periodo)
    tid = _uuid(principal.tenant_id, "empresa")
    async with tenant_session(principal.tenant_id) as s:
        repo = NovedadMensualRepo(s)
        novedades = await repo.listar_periodo(tid, periodo)
        return [
            _to_out(
                n,
                await repo.esta_bloqueada(tid, n.empleado_id, n.periodo),
            )
            for n in novedades
        ]


@router.get("/{novedad_id}", response_model=NovedadMensualOut)
async def obtener(
    novedad_id: str,
    principal: Principal = Depends(require_tenant),
):
    tid = _uuid(principal.tenant_id, "empresa")
    async with tenant_session(principal.tenant_id) as s:
        novedad = await NovedadMensualRepo(s).obtener(
            tid, _uuid(novedad_id, "novedad")
        )
        if not novedad:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Novedad no encontrada")
        return _to_out(novedad)


@router.put("/{novedad_id}", response_model=NovedadMensualOut)
async def editar(
    novedad_id: str,
    body: NovedadMensualUpdate,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    tid = _uuid(principal.tenant_id, "empresa")
    nid = _uuid(novedad_id, "novedad")
    async with tenant_session(principal.tenant_id) as s:
        try:
            novedad = await NovedadMensualRepo(s).editar(tid, nid, body.datos_dominio())
        except LookupError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        await AuditRepo(s).registrar(
            accion="actualizar", entidad="novedad_mensual", entidad_id=novedad_id,
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
            payload_diff={"periodo": body.periodo},
        )
        return _to_out(novedad)


@router.delete("/{novedad_id}", status_code=204)
async def eliminar(
    novedad_id: str,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    tid = _uuid(principal.tenant_id, "empresa")
    nid = _uuid(novedad_id, "novedad")
    async with tenant_session(principal.tenant_id) as s:
        try:
            eliminado = await NovedadMensualRepo(s).eliminar(tid, nid)
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        if not eliminado:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Novedad no encontrada")
        await AuditRepo(s).registrar(
            accion="eliminar", entidad="novedad_mensual", entidad_id=novedad_id,
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
        )
    return None
