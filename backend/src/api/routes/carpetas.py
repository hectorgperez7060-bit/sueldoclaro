"""Consulta de carpetas mensuales versionadas. Sin edición directa."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from api.dependencies.auth import Principal, require_rol, require_tenant
from domain.entities.carpeta_mensual import (
    faltantes_para_revision, huella_carpeta, obligaciones_desde_contenido,
    validar_transicion_obligacion,
)
from domain.value_objects.periodo import Periodo
from infrastructure.database import models as m
from infrastructure.database.base import now_utc
from infrastructure.database.repositories import AuditRepo, CarpetaMensualRepo
from infrastructure.database.session import tenant_session

router = APIRouter(prefix="/carpetas-mensuales", tags=["carpetas mensuales"])


class EstadoObligacionIn(BaseModel):
    estado: str = Field(pattern=r"^(pendiente|generada|pagada|verificada)$")
    comprobante: str = ""
    importe: Decimal | None = Field(default=None, ge=0)
    vencimiento: date | None = None


class AprobarCarpetaIn(BaseModel):
    alcance: str = "Revisión mensual integral: liquidación, ARCA y obligaciones sindicales"
    observaciones: str = ""


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


def _obligacion_out(o: m.ObligacionPagoMensual) -> dict:
    return {
        "id": str(o.id), "tipo": o.tipo, "cct_numero": o.cct_numero,
        "destino_pago": o.destino_pago, "codigo_boleta": o.codigo_boleta,
        "importe": str(o.importe) if o.importe is not None else None,
        "vencimiento": o.vencimiento.isoformat() if o.vencimiento else None,
        "canal_pago": o.canal_pago, "url_pago": o.url_pago,
        "fuente_pago": o.fuente_pago, "estado": o.estado,
        "comprobante": o.comprobante,
    }


@router.get("/{carpeta_id}/cierre")
async def obtener_cierre(
    carpeta_id: str, principal: Principal = Depends(require_tenant),
):
    try:
        cid, tid = uuid.UUID(carpeta_id), uuid.UUID(principal.tenant_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Identificador inválido") from exc
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await s.get(m.CarpetaMensual, cid)
        if carpeta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Carpeta mensual no encontrada")
        repo = CarpetaMensualRepo(s)
        obligaciones = await repo.listar_obligaciones(tid, cid)
        # Las carpetas creadas antes del cierre profesional no tienen filas en
        # obligacion_pago_mensual. Las generamos desde su fotografia inmutable
        # para que las versiones historicas tambien puedan revisarse.
        if not obligaciones:
            obligaciones = await repo.crear_obligaciones(
                tid, cid, obligaciones_desde_contenido(carpeta.contenido or {})
            )
        revisiones = list((await s.execute(
            select(m.RevisionProfesional).where(
                m.RevisionProfesional.tenant_id == tid,
                m.RevisionProfesional.carpeta_id == cid,
            ).order_by(m.RevisionProfesional.firmado_at.desc())
        )).scalars().all())
        return {
            "carpeta": _out(carpeta),
            "obligaciones": [_obligacion_out(o) for o in obligaciones],
            "faltantes": faltantes_para_revision(
                carpeta.contenido, [_obligacion_out(o) for o in obligaciones]
            ),
            "revisiones": [{
                "nombre_apellido": r.nombre_apellido, "matricula": r.matricula,
                "jurisdiccion": r.jurisdiccion, "alcance": r.alcance,
                "observaciones": r.observaciones,
                "firmado_at": r.firmado_at.isoformat() if r.firmado_at else None,
                "hash_revisado": r.hash_revisado,
            } for r in revisiones],
        }


@router.patch("/{carpeta_id}/obligaciones/{obligacion_id}")
async def actualizar_obligacion(
    carpeta_id: str, obligacion_id: str, body: EstadoObligacionIn,
    principal: Principal = Depends(require_rol("admin", "liquidador", "contador_revisor")),
):
    try:
        cid, oid = uuid.UUID(carpeta_id), uuid.UUID(obligacion_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Identificador inválido") from exc
    async with tenant_session(principal.tenant_id) as s:
        obligacion = await s.get(m.ObligacionPagoMensual, oid)
        if obligacion is None or obligacion.carpeta_id != cid:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Obligación no encontrada")
        carpeta = await s.get(m.CarpetaMensual, cid)
        if carpeta is None or carpeta.estado != "calculada":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Las obligaciones sólo pueden modificarse antes de la revisión profesional",
            )
        comprobante = body.comprobante.strip() or obligacion.comprobante
        try:
            validar_transicion_obligacion(obligacion.estado, body.estado, comprobante)
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        if body.estado == "generada" and body.importe is None and obligacion.importe is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Ingresá el importe real antes de marcar la obligación como generada",
            )
        obligacion.estado = body.estado
        obligacion.comprobante = comprobante
        if body.importe is not None:
            obligacion.importe = body.importe
        if body.vencimiento is not None:
            obligacion.vencimiento = body.vencimiento
        if body.estado == "pagada":
            obligacion.pagada_at = now_utc()
        if body.estado == "verificada":
            obligacion.verificada_at = now_utc()
        await AuditRepo(s).registrar(
            accion="actualizar_pago", entidad="obligacion_pago_mensual",
            entidad_id=str(oid), tenant_id=uuid.UUID(principal.tenant_id),
            usuario_id=uuid.UUID(principal.usuario_id),
            payload_diff={"estado": body.estado, "comprobante": bool(body.comprobante)},
        )
        return _obligacion_out(obligacion)


@router.post("/{carpeta_id}/aprobar")
async def aprobar_carpeta(
    carpeta_id: str, body: AprobarCarpetaIn,
    principal: Principal = Depends(require_rol("admin", "contador_revisor")),
):
    try:
        cid, tid, uid = (
            uuid.UUID(carpeta_id), uuid.UUID(principal.tenant_id), uuid.UUID(principal.usuario_id)
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Identificador inválido") from exc
    async with tenant_session(principal.tenant_id) as s:
        carpeta = await s.get(m.CarpetaMensual, cid)
        if carpeta is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Carpeta mensual no encontrada")
        if carpeta.estado != "calculada":
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"La carpeta está en estado {carpeta.estado} y no puede volver a aprobarse",
            )
        perfil = (await s.execute(select(m.ContadorProfesional).where(
            m.ContadorProfesional.usuario_id == uid
        ))).scalar_one_or_none()
        if perfil is None or not perfil.matricula_vigente or not perfil.constancia_url.strip():
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "El usuario debe tener perfil de contador, matrícula vigente y constancia",
            )
        obligaciones = await CarpetaMensualRepo(s).listar_obligaciones(tid, cid)
        faltantes = faltantes_para_revision(
            carpeta.contenido, [_obligacion_out(o) for o in obligaciones]
        )
        if faltantes:
            raise HTTPException(status.HTTP_409_CONFLICT, {"mensaje": "La carpeta no puede aprobarse", "faltantes": faltantes})
        hash_actual = huella_carpeta(carpeta.contenido)
        if hash_actual != carpeta.hash_sha256:
            raise HTTPException(status.HTTP_409_CONFLICT, "La carpeta cambió después de calcularse")
        revision = m.RevisionProfesional(
            tenant_id=tid, carpeta_id=cid, contador_id=perfil.id, usuario_id=uid,
            nombre_apellido=perfil.nombre_apellido, matricula=perfil.matricula,
            jurisdiccion=perfil.jurisdiccion, consejo_profesional=perfil.consejo_profesional,
            hash_revisado=hash_actual, alcance=body.alcance,
            observaciones=body.observaciones,
        )
        s.add(revision)
        carpeta.estado = "revisada"
        await AuditRepo(s).registrar(
            accion="aprobar", entidad="carpeta_mensual", entidad_id=str(cid),
            tenant_id=tid, usuario_id=uid,
            payload_diff={"hash_revisado": hash_actual, "matricula": perfil.matricula},
        )
        await s.flush()
        return {"estado": carpeta.estado, "hash_revisado": hash_actual,
                "contador": perfil.nombre_apellido, "matricula": perfil.matricula}
