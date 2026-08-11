"""Motor data-driven por INCIDENCIAS (sin hardcodear convenios).

Cada concepto no remunerativo declara qué bases integra (antigüedad, presentismo)
y qué aportes dispara (jubilación, obra social, sindicato). El motor sólo lee esas
incidencias. Casos: Comercio 130/75 (NR que integra antig/presentismo y aporta
OS/sindical pero NO jubilación; bono sin incidencia) y Sanidad 122/75 (NR neutro).
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
INC_120 = {"integra_antiguedad": True, "integra_presentismo": True,
           "aporte_jubilacion": False, "aporte_obra_social": True, "aporte_sindicato": True}
INC_OFF = {"integra_antiguedad": False, "integra_presentismo": False,
           "aporte_jubilacion": False, "aporte_obra_social": False, "aporte_sindicato": False}


def _params(extra):
    std = [P("APORTE_JUBILACION", D("0.11"), "%", "empleado", VF),
           P("APORTE_LEY19032", D("0.03"), "%", "empleado", VF),
           P("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", VF),
           P("APORTE_MODERNIZACION", D("0.01"), "%", "empleado", VF),
           P("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", VF),
           P("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", VF)]
    return ParametroSet(std + extra)


def _cct(num, pres=True):
    return CctConfig(num, D("0.01"), D("12"), D("200"), aplica_presentismo=pres,
                     aplica_cuota_sindical=True, cuota_sindical_pct=D("0.02"))


def _emp(num, afil=True):
    return Empleado("Ana", "Diaz", Cuil("20111111112"), date(2021, 1, 1),
                    num, "Maestranza A", "1", afiliado_sindicato=afil)


def _esc(num, b):
    return EscalaSalarial(num, "Maestranza A", Dinero(D(b)), VF, None, True, "t")


def _f(r, c):
    return next((x for x in r.conceptos if x.codigo == c), None)


def _pct(base_dec, p):
    return Dinero(base_dec).porcentaje(D(p)).redondear().monto


def test_comercio_incidencias_por_concepto():
    extra = [
        P("COMERCIO_NR1_130/75", D("100000"), "ARS", "no_rem", date(2026,7,1), date(2026,11,30), True, "", "130/75", INC_120),
        P("COMERCIO_NR2_130/75", D("20000"), "ARS", "no_rem", date(2026,7,1), date(2026,11,30), True, "", "130/75", INC_120),
        P("COMERCIO_BONO_130/75", D("25000"), "ARS", "no_rem", date(2026,7,1), date(2026,8,31), True, "", "130/75", INC_OFF),
    ]
    r = MotorLiquidacion(_params(extra), AmparoSet()).liquidar_mensual(
        _emp("130/75"), Periodo(2026,7), _esc("130/75","1137023"), _cct("130/75"), a_fecha=date(2026,7,28))
    basico = D("1137023")
    antig = Dinero(basico + 120000).porcentaje(D("0.05")).redondear().monto
    assert _f(r, "ANTIGUEDAD").importe.monto == antig                    # base incluye NR
    pres = Dinero(basico + 120000 + antig).dividir(D("12")).redondear().monto
    assert _f(r, "PRESENTISMO").importe.monto == pres
    base_rem = basico + antig + pres
    assert _f(r, "APORTE_JUBILACION").importe.monto == _pct(base_rem, "0.11")           # NR NO tributa jubilación
    assert _f(r, "APORTE_OBRA_SOCIAL").importe.monto == _pct(base_rem + 120000, "0.03") # NR sí OS
    assert _f(r, "CUOTA_SINDICAL").importe.monto == _pct(base_rem + 120000, "0.02")     # NR sí sindical
    assert r.total_no_remunerativo.monto == D("145000.00")              # 100k+20k+25k bono
    # el bono no integró antigüedad/presentismo (si lo hubiera hecho, antig sería mayor)
    assert _f(r, "COMERCIO_BONO_130/75") is not None


def test_sanidad_nr_neutro_no_afecta_bases():
    extra = [P("SANIDAD_SUMA_NR_AGO", D("80000"), "ARS", "no_rem", date(2026,8,1), date(2026,8,31), True, "", "122/75", INC_OFF)]
    r = MotorLiquidacion(_params(extra), AmparoSet()).liquidar_mensual(
        _emp("122/75"), Periodo(2026,8), _esc("122/75","1194974.90"), _cct("122/75"), a_fecha=date(2026,8,28))
    b = _f(r, "BASICO").importe.monto
    assert _f(r, "ANTIGUEDAD").importe.monto == Dinero(b).porcentaje(D("0.05")).redondear().monto  # NR no integra
    base_rem = b + _f(r, "ANTIGUEDAD").importe.monto + _f(r, "PRESENTISMO").importe.monto
    assert _f(r, "APORTE_JUBILACION").importe.monto == _pct(base_rem, "0.11")            # NR no suma
    assert _f(r, "SANIDAD_SUMA_NR_AGO").importe.monto == D("80000.00")


def test_aporte_solidario_solo_no_afiliado():
    extra = [P("APORTE_SOLIDARIO_76/75", D("0.02"), "%", "ded_noafil", date(2026,6,1), date(2026,8,31), True, "", "76/75")]
    m = MotorLiquidacion(_params(extra), AmparoSet())
    r = m.liquidar_mensual(_emp("76/75", afil=False), Periodo(2026,7), _esc("76/75","1000000"), _cct("76/75"), a_fecha=date(2026,7,28))
    assert _f(r, "APORTE_SOLIDARIO_76/75") is not None
    r2 = m.liquidar_mensual(_emp("76/75", afil=True), Periodo(2026,7), _esc("76/75","1000000"), _cct("76/75"), a_fecha=date(2026,7,28))
    assert _f(r2, "APORTE_SOLIDARIO_76/75") is None


if __name__ == "__main__":
    test_comercio_incidencias_por_concepto()
    test_sanidad_nr_neutro_no_afecta_bases()
    test_aporte_solidario_solo_no_afiliado()
    print("OK motor por incidencias (Comercio + Sanidad + solidario)")
