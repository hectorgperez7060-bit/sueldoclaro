"""Bootstrap de esquema y seed de BD (dev/tests).

Aplica el MISMO RLS que la migración Alembic (vía infrastructure.database.rls),
así los tests validan exactamente lo que corre en producción.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from . import models as m
from .base import Base
from .rls import enable_rls_sql

VIGENCIA = date(2026, 6, 1)
FUENTE = "EJEMPLO — verificar antes de producción"


async def crear_esquema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in enable_rls_sql():
            await conn.execute(text(stmt))


async def borrar_esquema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def sembrar_parametros(session: AsyncSession) -> None:
    """Carga CCT 130/75, parámetros, escala y amparos de EJEMPLO (is_verified=False)."""
    session.add(m.Cct(
        numero="130/75", nombre="Empleados de Comercio", sindicato="FAECYS",
        cuota_sindical_pct=Decimal("0.02"),
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"), divisor_horas=Decimal("200"),
    ))

    def pl(codigo, valor, unidad, ambito):
        return m.ParametroLegal(codigo=codigo, valor=Decimal(valor), unidad=unidad,
                                ambito=ambito, valid_from=VIGENCIA, is_verified=False, fuente=FUENTE)

    session.add_all([
        pl("APORTE_JUBILACION", "0.11", "%", "empleado"),
        pl("APORTE_LEY19032", "0.03", "%", "empleado"),
        pl("APORTE_OBRA_SOCIAL", "0.03", "%", "empleado"),
        pl("CUOTA_SINDICAL", "0.02", "%", "empleado"),
        pl("APORTE_MODERNIZACION", "0.01", "%", "empleado"),
        pl("CONTRIB_JUBILACION", "0.18", "%", "empleador"),
        pl("CONTRIB_OBRA_SOCIAL", "0.06", "%", "empleador"),
        pl("CONTRIB_INSSJP", "0.015", "%", "empleador"),
        pl("CONTRIB_ASIG_FAM", "0.047", "%", "empleador"),
        pl("TOPE_SIPA", "9000000.00", "ARS", "empleado"),
    ])

    session.add(m.EscalaSalarial(
        cct_numero="130/75", categoria="Administrativo A", basico=Decimal("500000.00"),
        valid_from=VIGENCIA, is_verified=False, fuente="EJEMPLO — verificar escala FAECYS",
    ))

    session.add(m.AmparoCct(
        cct_numero="130/75", articulo_suspendido="L27802:131",
        concepto_afectado="APORTE_MODERNIZACION", estado="vigente",
        valid_from=VIGENCIA, juzgado="EJEMPLO — cautelar FAECYS", is_verified=False,
    ))
    await session.flush()
