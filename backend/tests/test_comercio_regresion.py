"""Regresión determinística de Comercio (CCT 130/75) — tratamiento SINDICAL correcto.

Fuente oficial: CCT 130/75 arts. 100 y 101 + comunicado FAECYS 07/2026 (Disp. 839/26).
- Art. 100: 2% al sindicato de 1er grado + 0,5% a FAECYS, sobre TODO comprendido
  (afiliado o no), mientras rija la cautelar (SEC San Martín, Exp. FSM 14867/2026).
- Art. 101: cuota sindical, SOLO afiliados, % por localidad. Concepto SEPARADO
  (el afiliado paga art.100 + art.101, no uno en reemplazo del otro).

Se verifica concepto por concepto contra el motor por incidencias.
"""
import os
import sys
from datetime import date
from decimal import Decimal as D

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from domain.entities.empleado import Empleado
from domain.entities.parametros import ParametroLegal as P, ParametroSet, EscalaSalarial, AmparoSet, Amparo
from domain.payroll_engine.engine import MotorLiquidacion
from domain.payroll_engine.config import CctConfig
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo

VF = date(2026, 1, 1)
INC_NR = {"integra_antiguedad": True, "integra_presentismo": True, "aporte_jubilacion": False,
          "aporte_obra_social": True, "aporte_sindicato": True}
INC_BONO = {"integra_antiguedad": False, "integra_presentismo": False, "aporte_jubilacion": False,
            "aporte_obra_social": False, "aporte_sindicato": False}


def _motor():
    params = [
        P("APORTE_JUBILACION", D("0.11"), "%", "empleado", VF),
        P("APORTE_LEY19032", D("0.03"), "%", "empleado", VF),
        P("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", VF),
        P("APORTE_MODERNIZACION", D("0.01"), "%", "empleado", VF),
        P("TOPE_SIPA", D("9000000"), "ARS", "empleado", VF),
        P("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", VF),
        P("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", VF),
        # NR del acuerdo (ARS + incidencias)
        P("COMERCIO_NR1_130/75", D("100000"), "ARS", "no_rem", date(2026,7,1), date(2026,11,30), True, "", "130/75", INC_NR),
        P("COMERCIO_NR2_130/75", D("20000"), "ARS", "no_rem", date(2026,7,1), date(2026,11,30), True, "", "130/75", INC_NR),
        P("COMERCIO_BONO_130/75", D("25000"), "ARS", "no_rem", date(2026,7,1), date(2026,8,31), True, "", "130/75", INC_BONO),
        # deducciones sindicales (%, con condición en 'ambito')
        P("APORTE_SINDICAL_ART100_130/75", D("0.02"), "%", "ded_todos", date(2026,3,1), None, True, "", "130/75"),
        P("APORTE_FAECYS_ART100_130/75", D("0.005"), "%", "ded_todos", date(2026,3,1), None, True, "", "130/75"),
        P("CUOTA_SINDICAL_ART101_130/75", D("0.02"), "%", "ded_afil", date(2026,1,1), None, False, "", "130/75"),
    ]
    amp = AmparoSet([Amparo("130/75", "L27802:131", "APORTE_MODERNIZACION", "vigente", date(2026,3,1), date(2026,9,30))])
    return MotorLiquidacion(ParametroSet(params), amp)


# aplica_cuota_sindical=False: la cuota vieja queda apagada; el sindical va por los conceptos ded_*
CCT = CctConfig("130/75", D("0.01"), D("12"), D("200"), aplica_presentismo=True,
                aplica_cuota_sindical=False, cuota_sindical_pct=None)
ESC = EscalaSalarial("130/75", "Maestranza A", Dinero(D("1137023")), VF, None, True, "FAECYS 22/07/2026")
BASE_SIND = D("1429863.66")   # remunerativo 1.309.863,66 + $120.000 NR (incidencia sindical)


def _emp(afil):
    return Empleado("Juan", "Perez", Cuil("20111111112"), date(2021, 7, 1),
                    "130/75", "Maestranza A", "1", afiliado_sindicato=afil)


def _c(r, cod):
    x = next((k for k in r.conceptos if k.codigo == cod), None)
    return x.importe.monto if x else None


def _pc(p):
    return Dinero(BASE_SIND).porcentaje(D(p)).redondear().monto


def test_comercio_no_afiliado_art100_mas_faecys_sin_cuota():
    r = _motor().liquidar_mensual(_emp(False), Periodo(2026, 7), ESC, CCT, a_fecha=date(2026, 7, 28))
    assert _c(r, "APORTE_SINDICAL_ART100_130/75") == _pc("0.02")   # 2% a TODO comprendido
    assert _c(r, "APORTE_FAECYS_ART100_130/75") == _pc("0.005")    # 0,5% FAECYS a todos
    assert _c(r, "CUOTA_SINDICAL_ART101_130/75") is None           # no afiliado: no art.101
    assert _c(r, "CUOTA_SINDICAL") is None                         # la cuota vieja quedó apagada


def test_comercio_afiliado_paga_art100_faecys_y_cuota_art101():
    r = _motor().liquidar_mensual(_emp(True), Periodo(2026, 7), ESC, CCT, a_fecha=date(2026, 7, 28))
    assert _c(r, "APORTE_SINDICAL_ART100_130/75") == _pc("0.02")   # sigue pagando el art.100
    assert _c(r, "APORTE_FAECYS_ART100_130/75") == _pc("0.005")
    assert _c(r, "CUOTA_SINDICAL_ART101_130/75") == _pc("0.02")    # + cuota art.101 (afiliado)


if __name__ == "__main__":
    test_comercio_no_afiliado_art100_mas_faecys_sin_cuota()
    test_comercio_afiliado_paga_art100_faecys_y_cuota_art101()
    print("OK regresión Comercio sindical (art.100 todos + FAECYS + art.101 afiliados)")
