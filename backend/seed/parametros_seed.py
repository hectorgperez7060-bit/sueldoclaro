"""Seed de EJEMPLO para desarrollo (sección 12 del prompt maestro).

TODOS los valores están marcados is_verified=False. Son placeholders de
referencia histórica: antes de producción, un contador matriculado debe cargar
los valores vigentes verificados. NO usar para liquidaciones reales.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List

# Imports absolutos desde src/ (pytest agrega src al pythonpath)
from domain.entities.parametros import (
    Amparo,
    AmparoSet,
    EscalaSalarial,
    ParametroLegal,
    ParametroSet,
)
from domain.payroll_engine.config import CctConfig
from domain.value_objects.dinero import Dinero

VIGENCIA = date(2026, 6, 1)
FUENTE = "EJEMPLO — verificar valor vigente antes de producción"


def parametros_ejemplo() -> ParametroSet:
    def pct(codigo, valor, ambito):
        return ParametroLegal(codigo, Decimal(valor), "%", ambito, VIGENCIA,
                              is_verified=False, fuente=FUENTE)

    params: List[ParametroLegal] = [
        # --- aportes del trabajador ---
        pct("APORTE_JUBILACION", "0.11", "empleado"),
        pct("APORTE_LEY19032", "0.03", "empleado"),
        pct("APORTE_OBRA_SOCIAL", "0.03", "empleado"),
        pct("CUOTA_SINDICAL", "0.02", "empleado"),      # Comercio/FAECYS
        pct("APORTE_MODERNIZACION", "0.01", "empleado"),  # Ley 27.802 art. 131 (dual)
        # --- contribuciones patronales (desglose Anexo III) ---
        pct("CONTRIB_JUBILACION", "0.18", "empleador"),
        pct("CONTRIB_OBRA_SOCIAL", "0.06", "empleador"),
        pct("CONTRIB_INSSJP", "0.015", "empleador"),
        pct("CONTRIB_ASIG_FAM", "0.047", "empleador"),
        # --- topes ---
        ParametroLegal("TOPE_SIPA", Decimal("9000000.00"), "ARS", "empleado",
                       VIGENCIA, is_verified=False, fuente=FUENTE),
    ]
    return ParametroSet(params)


def cct_comercio_13075() -> CctConfig:
    return CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),  # 1% por año
        presentismo_divisor=Decimal("12"),        # 1/12 = 8,33%
        divisor_horas=Decimal("200"),             # Comercio: 200 hs
        aplica_presentismo=True,
        aplica_cuota_sindical=True,
    )


def escala_comercio(categoria: str, basico: str) -> EscalaSalarial:
    return EscalaSalarial(
        cct_numero="130/75",
        categoria=categoria,
        basico=Dinero(Decimal(basico)),
        valid_from=VIGENCIA,
        is_verified=False,
        fuente="EJEMPLO — verificar escala vigente FAECYS",
    )


def amparos_faecys() -> AmparoSet:
    """FAECYS/Comercio: arts. 131 y 133 de la Ley 27.802 suspendidos."""
    return AmparoSet([
        Amparo(
            cct_numero="130/75",
            articulo_suspendido="L27802:131",
            concepto_afectado="APORTE_MODERNIZACION",
            estado="vigente",
            valid_from=VIGENCIA,
            juzgado="EJEMPLO — cautelar FAECYS",
            is_verified=False,
        ),
    ])


def sin_amparos() -> AmparoSet:
    return AmparoSet([])
