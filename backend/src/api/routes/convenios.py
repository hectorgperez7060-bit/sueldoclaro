"""Rutas de convenios (CCT): listado con categorías vigentes para la UI."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select

from api.dependencies.auth import Principal, require_tenant
from infrastructure.database import models as m
from infrastructure.database.session import plain_session

router = APIRouter(prefix="/convenios", tags=["convenios"])


@router.get("")
async def listar(_: Principal = Depends(require_tenant)):
    """Convenios activos con sus categorías (datos globales, sin tenant)."""
    async with plain_session() as s:
        ccts = (await s.execute(
            select(m.Cct).where(m.Cct.activo.is_(True)).order_by(m.Cct.numero)
        )).scalars().all()
        filas = (await s.execute(
            select(m.EscalaSalarial.cct_numero, m.EscalaSalarial.categoria).distinct()
        )).all()
    cats: dict[str, list[str]] = {}
    for numero, categoria in filas:
        cats.setdefault(numero, []).append(categoria)
    return [
        {
            "numero": c.numero,
            "nombre": c.nombre,
            "sindicato": c.sindicato,
            "categorias": sorted(cats.get(c.numero, [])),
        }
        for c in ccts
    ]
