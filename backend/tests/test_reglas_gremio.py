"""Tests de las reglas por gremio enganchadas al motor (datos verificados en BD).

Cubre: aporte solidario UOCRA 2% (solo no afiliados), suma no remunerativa de
Sanidad (no tributa aportes) y asignación Día de la Sanidad (solo septiembre).
"""
import os
import sys
from datetime import date
from decimal import Decimal as D

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from domain.entities.empleado import Empleado
from domain.entities.parametros import ParametroLegal as P, ParametroSet, EscalaSalarial, AmparoSet
from domain.payroll_engine.engine import MotorLiquidacion
from domain.payroll_engine.config import CctConfig
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo

VF = date(2026, 1, 1)


def _params(extra):
    std = [
        P("APORTE_JUBILACION", D("0.11"), "%", "empleado", VF),
        P("APORTE_LEY19032", D("0.03"), "%", "empleado", VF),
        P("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", VF),
        P("APORTE_MODERNIZACION", D("0.00"), "%", "empleado", VF),
        P("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", VF),
        P("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", VF),
    ]
    return ParametroSet(std + extra)


def _cct(num, sind=True):
    return CctConfig(num, D("0.01"), D("12"), D("200"),
                     aplica_presentismo=True, aplica_cuota_sindical=sind,
                     cuota_sindical_pct=D("0.025"))


def _emp(num, afil, prop=D("1")):
    return Empleado("Juan", "Perez", Cuil("20111111112"), date(2020, 1, 1),
                    num, "Cat", "1", afiliado_sindicato=afil, proporcion_jornada=prop)


def _esc(num, bas):
    return EscalaSalarial(num, "Cat", Dinero(D(bas)), VF, None, True, "test")


def _find(res, cod):
    return next((c for c in res.conceptos if c.codigo == cod), None)


def test_uocra_aporte_solidario_solo_no_afiliados():
    params = _params([P("UOCRA_APORTE_SOLIDARIO_76/75", D("0.02"), "%", "empleado",
                        date(2026, 6, 1), date(2026, 8, 31))])
    m = MotorLiquidacion(params, AmparoSet())
    r = m.liquidar_mensual(_emp("76/75", False), Periodo(2026, 7),
                           _esc("76/75", "1000000"), _cct("76/75", sind=False),
                           a_fecha=date(2026, 7, 28))
    sol = _find(r, "APORTE_SOLIDARIO_UOCRA")
    assert sol is not None
    assert sol.importe.monto == (r.total_remunerativo.monto * D("0.02")).quantize(D("0.01"))
    # afiliado no lo paga
    r2 = m.liquidar_mensual(_emp("76/75", True), Periodo(2026, 7),
                            _esc("76/75", "1000000"), _cct("76/75"),
                            a_fecha=date(2026, 7, 28))
    assert _find(r2, "APORTE_SOLIDARIO_UOCRA") is None


def test_sanidad_suma_nr_no_tributa_aportes():
    params = _params([P("SANIDAD_SUMA_NR_JUN_JUL", D("90000"), "ARS", "no_rem",
                        date(2026, 6, 1), date(2026, 7, 31))])
    m = MotorLiquidacion(params, AmparoSet())
    r = m.liquidar_mensual(_emp("122/75", True), Periodo(2026, 7),
                           _esc("122/75", "1159716.53"), _cct("122/75"),
                           a_fecha=date(2026, 7, 28))
    assert _find(r, "SANIDAD_SUMA_NR_JUN_JUL").importe.monto == D("90000.00")
    jub = _find(r, "APORTE_JUBILACION")
    assert jub.importe.monto == (r.total_remunerativo.monto * D("0.11")).quantize(D("0.01"))
    assert _find(r, "SANIDAD_DIA_SANIDAD_122/75") is None  # no en julio


def test_dia_de_la_sanidad_solo_septiembre():
    params = _params([P("SANIDAD_DIA_SANIDAD_122/75", D("68925.70"), "ARS", "no_rem",
                        date(2026, 9, 1), date(2026, 9, 30))])
    m = MotorLiquidacion(params, AmparoSet())
    r = m.liquidar_mensual(_emp("122/75", True), Periodo(2026, 9),
                           _esc("122/75", "1159716.53"), _cct("122/75"),
                           a_fecha=date(2026, 9, 28))
    assert _find(r, "SANIDAD_DIA_SANIDAD_122/75").importe.monto == D("68925.70")


if __name__ == "__main__":
    test_uocra_aporte_solidario_solo_no_afiliados()
    test_sanidad_suma_nr_no_tributa_aportes()
    test_dia_de_la_sanidad_solo_septiembre()
    print("OK reglas por gremio")
