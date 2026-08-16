from datetime import date
from decimal import Decimal as D

import pytest

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.entities.sanidad_122_75 import (
    configurar_adicionales_sanidad,
    reglas_pendientes_revision_sanidad,
)
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


def _caso():
    desde = date(2026, 1, 1)
    parametros = ParametroSet([
        ParametroLegal("APORTE_JUBILACION", D("0.11"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", desde),
    ])
    motor = MotorLiquidacion(parametros, AmparoSet())
    empleado = Empleado("Ana", "Sanidad", Cuil("27307324666"), date(2025, 1, 1), "122/75", "Administrativo de Primera", "1")
    escala = EscalaSalarial("122/75", empleado.categoria, Dinero(D("1000000")), date(2026, 8, 1), date(2026, 8, 31), True, "prueba")
    config = CctConfig("122/75", D("0.02"), D("12"), D("200"), aplica_presentismo=False, aplica_cuota_sindical=False, adicionales=configurar_adicionales_sanidad())
    return motor, empleado, escala, config


def test_sector_especial_calcula_porcentaje_sobre_basico():
    motor, empleado, escala, config = _caso()
    resultado = motor.liquidar_mensual(empleado, Periodo(2026, 8), escala, config, Novedades(adicionales_convencionales=("TERAPIA_8H",)), a_fecha=date(2026, 8, 28))
    adicional = next(c for c in resultado.conceptos if c.codigo == "TERAPIA_8H")
    assert adicional.importe.monto == D("200000.00")


def test_nocturnidad_prorratea_solo_horas_nocturnas():
    motor, empleado, escala, config = _caso()
    novedades = Novedades(adicionales_convencionales=("NOCTURNIDAD",), cantidades_adicionales=(("NOCTURNIDAD", D("40")), ("HORAS_TOTALES_PERIODO", D("160"))))
    resultado = motor.liquidar_mensual(empleado, Periodo(2026, 8), escala, config, novedades, a_fecha=date(2026, 8, 28))
    adicional = next(c for c in resultado.conceptos if c.codigo == "NOCTURNIDAD")
    assert adicional.importe.monto == D("25000.00")


def test_rechaza_dos_regimenes_incompatibles_del_mismo_sector():
    motor, empleado, escala, config = _caso()
    with pytest.raises(ValueError, match="incompatibles"):
        motor.liquidar_mensual(empleado, Periodo(2026, 8), escala, config, Novedades(adicionales_convencionales=("TERAPIA_8H", "MUCAMA_SECTOR_ESPECIAL")), a_fecha=date(2026, 8, 28))


def test_reglas_no_automatizables_quedan_catalogadas_y_no_se_ofrecen_como_formula():
    pendientes = {r.codigo for r in reglas_pendientes_revision_sanidad()}
    calculables = {r.codigo for r in configurar_adicionales_sanidad()}
    assert {"FONDO_CIRUGIA_PARTO", "ZONA_DESFAVORABLE", "CAMAS_PACIENTES_EXCEDENTES", "LICENCIA_ESPECIAL"} <= pendientes
    assert not pendientes & calculables
