"""Calculador dinámico de las 10 Bases Imponibles del Libro de Sueldos Digital (LSD / ARCA).

Implementa estrictamente las reglas normativas de la AFIP/ARCA:
- Guía N.º 18: Armado de bases imponibles 1 a 10 y evaluación de topes por sub-bolsas independientes.
- Guía N.º 14: Incremento de base imponible a jornada completa de Obra Social (base diferencial).
- Guía N.º 28: Sueldo Anual Complementario (SAC) y prorrateo de topes.
- Guía N.º 31: Vacaciones y prorrateo de topes licencias.
- Ley 27.541: Detracción de contribuciones patronales en Base 10.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional

from domain.entities.concepto import TipoConcepto
from domain.entities.empleado import Empleado
from domain.entities.liquidacion import ResultadoLiquidacion
from domain.payroll_engine.config import CctConfig
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from infrastructure.lsd.catalogo_afip import (
    CATALOGO,
    ClaseTopeARCA,
    ConceptoARCA,
    GrupoARCA,
)


@dataclass(frozen=True)
class ParametrosPeriodoLSD:
    """Parámetros y límites normativos vigentes para la liquidación del período."""
    periodo: Periodo
    tope_min_sipa: Dinero                       # Tope Mínimo Previsional SIPA (Bases 1, 2, 3, 4, 5)
    tope_max_sipa_mensual: Dinero               # Tope Máximo Previsional SIPA Mensual (Bases 1, 4, 5)
    tope_max_sipa_sac: Dinero                   # 50% de tope_max_sipa_mensual (para SAC)
    piso_obra_social: Dinero                    # Piso mínimo imponible Obra Social (Base 4 y 8)
    detraccion_ley27541_mensual: Dinero         # Detracción patronal mensual computable (Base 10)
    detraccion_ley27541_sac: Dinero             # 50% de detracción mensual (para SAC en Base 10)


def _max(a: Dinero, b: Dinero) -> Dinero:
    return a if a.monto >= b.monto else b


def calcular_bases_lsd(
    resultado: ResultadoLiquidacion,
    empleado: Empleado,
    cct: CctConfig,
    parametros: ParametrosPeriodoLSD,
    periodo: Periodo,
    overrides_empleador: Optional[Dict[str, ConceptoARCA]] = None,
) -> List[Decimal]:
    """Calcula dinámicamente las 10 Bases Imponibles del Registro 04 (LSD / ARCA)."""
    catalogo = dict(CATALOGO)
    if overrides_empleador:
        catalogo.update(overrides_empleador)

    # 1. Acumuladores de Sub-bolsas de topes independientes (Aportes Bases 1, 4, 5)
    sub_sipa_mensual = Dinero.cero()
    sub_sipa_sac_estandar = Dinero.cero()
    sub_sipa_sac_prop = Dinero.cero()
    sub_sipa_vac = Dinero.cero()

    sub_os_mensual = Dinero.cero()
    sub_os_sac_estandar = Dinero.cero()
    sub_os_sac_prop = Dinero.cero()
    sub_os_vac = Dinero.cero()

    dias_sac_prop = 0
    dias_vac = 0

    # 2. Acumuladores de Contribuciones Patronales (SIN TOPE MÁXIMO PREVISIONAL)
    remun_sipa_contrib = Dinero.cero()
    remun_aaff_fne_contrib = Dinero.cero()
    no_remun_aaff_fne_contrib = Dinero.cero()
    remun_os_contrib = Dinero.cero()
    no_remun_os_contrib = Dinero.cero()
    base_lrt_contrib = Dinero.cero()

    remun_diferencial_aporte = Dinero.cero()
    remun_diferencial_contrib = Dinero.cero()

    for c in resultado.conceptos:
        info = catalogo.get(c.codigo)
        if not info or info.grupo == GrupoARCA.DESCUENTO:
            continue

        # A) Clasificación por Sub-bolsas de Topes SIPA (Aportes Trabajador)
        if info.incidencias.integra_sipa:
            if info.clase_tope in (ClaseTopeARCA.MENSUAL, ClaseTopeARCA.SIN_TOPE):
                sub_sipa_mensual = sub_sipa_mensual + c.importe
            elif info.clase_tope == ClaseTopeARCA.SAC:
                sub_sipa_sac_estandar = sub_sipa_sac_estandar + c.importe
            elif info.clase_tope == ClaseTopeARCA.SAC_PROPORCIONAL:
                sub_sipa_sac_prop = sub_sipa_sac_prop + c.importe
                dias_sac_prop += int(c.cantidad or 0)
            elif info.clase_tope == ClaseTopeARCA.VACACIONES:
                sub_sipa_vac = sub_sipa_vac + c.importe
                dias_vac += int(c.cantidad or 0)

        # B) Clasificación por Sub-bolsas Obra Social (Aportes Trabajador)
        if info.incidencias.integra_obra_social:
            if info.clase_tope in (ClaseTopeARCA.MENSUAL, ClaseTopeARCA.SIN_TOPE):
                sub_os_mensual = sub_os_mensual + c.importe
            elif info.clase_tope == ClaseTopeARCA.SAC:
                sub_os_sac_estandar = sub_os_sac_estandar + c.importe
            elif info.clase_tope == ClaseTopeARCA.SAC_PROPORCIONAL:
                sub_os_sac_prop = sub_os_sac_prop + c.importe
            elif info.clase_tope == ClaseTopeARCA.VACACIONES:
                sub_os_vac = sub_os_vac + c.importe

        # C) Contribuciones Patronales (SIN TOPE MÁXIMO PREVISIONAL)
        if info.incidencias.integra_sipa and c.tipo == TipoConcepto.REMUNERATIVO:
            remun_sipa_contrib = remun_sipa_contrib + c.importe
        if info.incidencias.integra_aaff_fne:
            if c.tipo == TipoConcepto.REMUNERATIVO:
                remun_aaff_fne_contrib = remun_aaff_fne_contrib + c.importe
            elif c.tipo == TipoConcepto.NO_REMUNERATIVO:
                no_remun_aaff_fne_contrib = no_remun_aaff_fne_contrib + c.importe
        if info.incidencias.integra_obra_social:
            if c.tipo == TipoConcepto.REMUNERATIVO:
                remun_os_contrib = remun_os_contrib + c.importe
            elif c.tipo == TipoConcepto.NO_REMUNERATIVO:
                no_remun_os_contrib = no_remun_os_contrib + c.importe
        if info.incidencias.integra_lrt:
            base_lrt_contrib = base_lrt_contrib + c.importe
        if info.admite_regimen_diferencial and getattr(empleado, "es_regimen_diferencial", False):
            remun_diferencial_aporte = remun_diferencial_aporte + c.importe
            remun_diferencial_contrib = remun_diferencial_contrib + c.importe

    # 3. Evaluación de Sub-bolsas de Topes Aportes (Bases 1, 4, 5)
    g1_sipa = Dinero.minimo(sub_sipa_mensual, parametros.tope_max_sipa_mensual)
    g2_sipa = Dinero.minimo(sub_sipa_sac_estandar, parametros.tope_max_sipa_sac)
    tope_sac_prop = (parametros.tope_max_sipa_mensual.dividir(Decimal("30"))).multiplicar(Decimal(dias_sac_prop))
    g3_sipa = Dinero.minimo(sub_sipa_sac_prop, tope_sac_prop)
    tope_vac = (parametros.tope_max_sipa_mensual.dividir(Decimal("30"))).multiplicar(Decimal(dias_vac))
    g4_sipa = Dinero.minimo(sub_sipa_vac, tope_vac)

    g1_os = Dinero.minimo(sub_os_mensual, parametros.tope_max_sipa_mensual)
    g2_os = Dinero.minimo(sub_os_sac_estandar, parametros.tope_max_sipa_sac)
    g3_os = Dinero.minimo(sub_os_sac_prop, tope_sac_prop)
    g4_os = Dinero.minimo(sub_os_vac, tope_vac)

    base_sipa_aportes_total = g1_sipa + g2_sipa + g3_sipa + g4_sipa
    base_os_aportes_devengada = g1_os + g2_os + g3_os + g4_os

    # Guía N.º 14: Base Diferencial Obra Social para Aportes y Contribuciones
    piso_os_exigible = parametros.piso_obra_social
    devengado_os_total = remun_os_contrib + no_remun_os_contrib
    base_diferencial_os = _max(Dinero.cero(), piso_os_exigible - devengado_os_total)
    base_diferencial_ss = Dinero.cero()

    # 4. Construcción Final de las 10 Bases Imponibles (Guía N.º 18)
    base1 = _max(base_sipa_aportes_total, parametros.tope_min_sipa)
    base2 = _max(remun_sipa_contrib, parametros.tope_min_sipa)
    base3 = remun_aaff_fne_contrib + no_remun_aaff_fne_contrib + base_diferencial_ss
    base4 = Dinero.minimo(base_os_aportes_devengada + base_diferencial_os, parametros.tope_max_sipa_mensual)
    base5 = base1
    es_dif = getattr(empleado, "es_regimen_diferencial", False)
    base6 = remun_diferencial_aporte if es_dif else Dinero.cero()
    base7 = remun_diferencial_contrib if es_dif else Dinero.cero()
    base8 = remun_os_contrib + no_remun_os_contrib + base_diferencial_os
    base9 = base_lrt_contrib

    detraccion_efectiva = (parametros.detraccion_ley27541_mensual.multiplicar(empleado.proporcion_jornada)).redondear()
    if sub_sipa_sac_estandar > Dinero.cero():
        detraccion_efectiva = detraccion_efectiva + (parametros.detraccion_ley27541_sac.multiplicar(empleado.proporcion_jornada)).redondear()

    base10 = _max(base2 - detraccion_efectiva, parametros.tope_min_sipa)

    return [
        base1.redondear().monto,
        base2.redondear().monto,
        base3.redondear().monto,
        base4.redondear().monto,
        base5.redondear().monto,
        base6.redondear().monto,
        base7.redondear().monto,
        base8.redondear().monto,
        base9.redondear().monto,
        base10.redondear().monto,
    ]
