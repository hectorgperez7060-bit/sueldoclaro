"""Rutas de liquidaciones."""
from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import Principal, require_rol
from application.dto.schemas import AjusteManualLiquidacionIn, DetalleOut, LiquidacionOut, LiquidarIn
from application.use_cases.liquidar_periodo import LiquidarPeriodo
from infrastructure.database.repositories import AuditRepo, LiquidacionRepo
from infrastructure.database.session import tenant_session

router = APIRouter(prefix="/liquidaciones", tags=["liquidaciones"])


@router.post("", response_model=LiquidacionOut, status_code=201)
async def liquidar(body: LiquidarIn, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    novedades = {
        n.empleado_id: {"horas_extra_50": n.horas_extra_50, "horas_extra_100": n.horas_extra_100}
        for n in body.novedades
    }
    res = await LiquidarPeriodo().ejecutar(
        principal.tenant_id, body.periodo, body.tipo, novedades, principal.usuario_id,
        confirmar_provisorios=body.confirmar_provisorios,
    )
    return LiquidacionOut(**res)


def _id(valor: str, nombre: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"{nombre} inválido") from exc


def _totales(conceptos: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
    dos = Decimal("0.01")
    bruto = sum(
        (Decimal(str(c["importe"])) for c in conceptos
         if c["tipo"] in ("remunerativo", "no_remunerativo")),
        Decimal("0"),
    ).quantize(dos, ROUND_HALF_UP)
    deducciones = sum(
        (Decimal(str(c["importe"])) for c in conceptos if c["tipo"] == "deduccion"),
        Decimal("0"),
    ).quantize(dos, ROUND_HALF_UP)
    return bruto, deducciones, (bruto - deducciones).quantize(dos, ROUND_HALF_UP)


@router.patch(
    "/{liquidacion_id}/empleados/{empleado_id}/ajuste-manual",
    response_model=DetalleOut,
)
async def ajustar_manualmente(
    liquidacion_id: str,
    empleado_id: str,
    body: AjusteManualLiquidacionIn,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    """Corrige el borrador antes de imprimir y conserva la trazabilidad."""
    liq_id = _id(liquidacion_id, "Liquidación")
    emp_id = _id(empleado_id, "Empleado")
    tenant_id = _id(principal.tenant_id, "Empresa")
    usuario_id = _id(principal.usuario_id, "Usuario")
    async with tenant_session(principal.tenant_id) as s:
        repo = LiquidacionRepo(s)
        liq = await repo.obtener(liq_id)
        detalle = await repo.obtener_detalle(liq_id, emp_id) if liq else None
        if not liq or not detalle:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Liquidación o empleado no encontrado")
        if liq.estado != "borrador":
            raise HTTPException(status.HTTP_409_CONFLICT, "Solo se puede ajustar una liquidación en borrador")

        anteriores = list(detalle.conceptos or [])
        conceptos = []
        for item in body.conceptos:
            c = item.model_dump(mode="json")
            c["importe"] = str(item.importe.quantize(Decimal("0.01"), ROUND_HALF_UP))
            c["cantidad"] = str(item.cantidad)
            c["base_calculo"] = str(item.base_calculo) if item.base_calculo is not None else None
            c["ajuste_manual"] = True
            conceptos.append(c)
        bruto, deducciones, neto = _totales(conceptos)
        await repo.ajustar_detalle(detalle, conceptos, bruto, deducciones, neto)

        snapshot = dict(liq.snapshot_parametros or {})
        ajustes = dict(snapshot.get("ajustes_manuales") or {})
        previo = dict(ajustes.get(empleado_id) or {})
        ajustes[empleado_id] = {
            "original": previo.get("original", anteriores),
            "motivo_ultimo_ajuste": body.motivo,
            "usuario_id": principal.usuario_id,
        }
        snapshot["ajustes_manuales"] = ajustes
        liq.snapshot_parametros = snapshot
        await AuditRepo(s).registrar(
            accion="ajuste_manual",
            entidad="liquidacion_detalle",
            entidad_id=str(detalle.id),
            tenant_id=tenant_id,
            usuario_id=usuario_id,
            payload_diff={
                "liquidacion_id": liquidacion_id,
                "empleado_id": empleado_id,
                "motivo": body.motivo,
                "antes": anteriores,
                "despues": conceptos,
            },
        )
        return DetalleOut(
            empleado_id=empleado_id,
            bruto=bruto,
            total_deducciones=deducciones,
            neto=neto,
            conceptos=conceptos,
        )
