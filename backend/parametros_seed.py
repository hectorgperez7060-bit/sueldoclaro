"""Parámetros de EJEMPLO usados exclusivamente por los golden tests.

Todos los valores permanecen sin verificar y no forman parte de la carga
normativa de producción. Este módulo recompone la semilla que los tests
históricos importan desde ``backend/``.
"""
from datetime import date
from decimal import Decimal

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
    def pct(codigo: str, valor: str, ambito: str) -> ParametroLegal:
        return ParametroLegal(
            codigo, Decimal(valor), "%", ambito, VIGENCIA,
            is_verified=False, fuente=FUENTE,
        )

    return ParametroSet([
        pct("APORTE_JUBILACION", "0.11", "empleado"),
        pct("APORTE_LEY19032", "0.03", "empleado"),
        pct("APORTE_OBRA_SOCIAL", "0.03", "empleado"),
        pct("CUOTA_SINDICAL", "0.02", "empleado"),
        pct("APORTE_MODERNIZACION", "0.01", "empleado"),
        pct("CONTRIB_JUBILACION", "0.18", "empleador"),
        pct("CONTRIB_OBRA_SOCIAL", "0.06", "empleador"),
        pct("CONTRIB_INSSJP", "0.015", "empleador"),
        pct("CONTRIB_ASIG_FAM", "0.047", "empleador"),
        ParametroLegal(
            "TOPE_SIPA", Decimal("9000000.00"), "ARS", "empleado", VIGENCIA,
            is_verified=False, fuente=FUENTE,
        ),
    ])


def cct_comercio_13075() -> CctConfig:
    return CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
        aplica_presentismo=True,
        aplica_cuota_sindical=True,
    )


def escala_comercio(categoria: str, basico: str) -> EscalaSalarial:
    return EscalaSalarial(
        cct_numero="130/75", categoria=categoria,
        basico=Dinero(Decimal(basico)), valid_from=VIGENCIA,
        is_verified=False, fuente="EJEMPLO — verificar escala vigente FAECYS",
    )


def amparos_faecys() -> AmparoSet:
    return AmparoSet([
        Amparo(
            cct_numero="130/75", articulo_suspendido="L27802:131",
            concepto_afectado="APORTE_MODERNIZACION", estado="vigente",
            valid_from=VIGENCIA, juzgado="EJEMPLO — cautelar FAECYS",
            is_verified=False,
        ),
    ])


def sin_amparos() -> AmparoSet:
    return AmparoSet([])
