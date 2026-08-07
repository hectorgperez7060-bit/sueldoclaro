"""Rutas de liquidaciones."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.dependencies.auth import Principal, require_rol
from application.dto.schemas import LiquidacionOut, LiquidarIn
from application.use_cases.liquidar_periodo import LiquidarPeriodo

router = APIRouter(prefix="/liquidaciones", tags=["liquidaciones"])


@router.post("", response_model=LiquidacionOut, status_code=201)
async def liquidar(body: LiquidarIn, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    novedades = {
        n.empleado_id: {"horas_extra_50": n.horas_extra_50, "horas_extra_100": n.horas_extra_100}
        for n in body.novedades
    }
    res = await LiquidarPeriodo().ejecutar(
        principal.tenant_id, body.periodo, body.tipo, novedades, principal.usuario_id
    )
    return LiquidacionOut(**res)
