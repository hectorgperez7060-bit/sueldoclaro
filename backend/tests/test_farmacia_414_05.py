"""Regresión del recibo real de Farmacia/ADEF, julio de 2026.

Fuente normativa del escalafón: CCT 414/05, art. 13. El recibo aportado como
caso de control informa 8 años, básico $1.828.730,75 y antigüedad $365.746,15.
"""
import os
import sys
from datetime import date
from decimal import Decimal as D

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


def _parametros_minimos() -> ParametroSet:
    desde = date(2026, 1, 1)
    return ParametroSet([
        ParametroLegal("APORTE_JUBILACION", D("0.11"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0.01"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", desde),
    ])


def test_recibo_real_farmacia_aplica_escalon_20_por_ciento_a_ocho_anios():
    empleado = Empleado(
        "Rosalía", "Ocampos", Cuil("27240320520"), date(2018, 4, 9),
        "414/05", "Empleado especializado de farmacia", "138",
        afiliado_sindicato=True,
    )
    escala = EscalaSalarial(
        "414/05", "Empleado especializado de farmacia",
        Dinero(D("1828730.75")), date(2026, 7, 1), date(2026, 7, 31),
        True, "Recibo real de control + CCT 414/05 art. 13",
    )
    config = CctConfig(
        "414/05", D("0"), D("12"), D("200"),
        aplica_presentismo=False,
        aplica_cuota_sindical=False,
        antiguedad_escalones=(
            (1, D("0.05")), (2, D("0.10")), (5, D("0.20")),
            (10, D("0.30")), (15, D("0.35")), (20, D("0.40")),
            (25, D("0.50")),
        ),
    )

    resultado = MotorLiquidacion(_parametros_minimos(), AmparoSet()).liquidar_mensual(
        empleado, Periodo(2026, 7), escala, config, a_fecha=date(2026, 7, 28),
    )

    antiguedad = next(c for c in resultado.conceptos if c.codigo == "ANTIGUEDAD")
    assert antiguedad.importe.monto == D("365746.15")
    assert antiguedad.cantidad == D("8")


def test_escalones_farmacia_respetan_todos_los_umbrales_del_articulo_13():
    config = CctConfig(
        "414/05", D("0"), D("12"), D("200"),
        antiguedad_escalones=(
            (1, D("0.05")), (2, D("0.10")), (5, D("0.20")),
            (10, D("0.30")), (15, D("0.35")), (20, D("0.40")),
            (25, D("0.50")),
        ),
    )
    esperados = {
        0: "0", 1: "0.05", 2: "0.10", 4: "0.10", 5: "0.20",
        9: "0.20", 10: "0.30", 15: "0.35", 20: "0.40", 25: "0.50",
        30: "0.50",
    }
    for anios, porcentaje in esperados.items():
        assert config.antiguedad_fraccion(anios) == D(porcentaje)


def test_recibo_real_separa_aporte_adef_remunerativo_y_no_remunerativo():
    desde = date(2026, 7, 1)
    incidencia_nr = {
        "integra_antiguedad": False,
        "integra_presentismo": False,
        "aporte_jubilacion": False,
        "aporte_obra_social": False,
        "aporte_sindicato": True,
    }
    parametros = _parametros_minimos().con_extra(ParametroLegal(
        "FARMACIA_NR_414/05", D("54100.54"), "ARS", "no_rem", desde,
        date(2026, 7, 31), True, "Recibo real de control", "414/05", incidencia_nr,
    )).con_extra(ParametroLegal(
        "APORTE_ADEF_REM_414/05", D("0.02"), "%", "ded_todos", desde,
        date(2026, 7, 31), True, "CCT 414/05 art. 46", "414/05",
        {"base_deduccion": "remunerativa", "destino_pago": "ADEF",
         "codigo_boleta": "ADEF_APORTES"},
    )).con_extra(ParametroLegal(
        "APORTE_ADEF_NR_414/05", D("0.02"), "%", "ded_todos", desde,
        date(2026, 7, 31), True, "Recibo real de control", "414/05",
        {"base_deduccion": "no_remunerativa_sindical", "destino_pago": "ADEF",
         "codigo_boleta": "ADEF_APORTES"},
    ))
    empleado = Empleado(
        "Rosalía", "Ocampos", Cuil("27240320520"), date(2018, 4, 9),
        "414/05", "Empleado especializado de farmacia", "138",
        afiliado_sindicato=True,
    )
    escala = EscalaSalarial(
        "414/05", "Empleado especializado de farmacia",
        Dinero(D("1828730.75")), desde, date(2026, 7, 31), True,
        "Recibo real de control",
    )
    config = CctConfig(
        "414/05", D("0"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
        antiguedad_escalones=((1, D("0.05")), (2, D("0.10")),
                              (5, D("0.20")), (10, D("0.30"))),
    )
    # El recibo suma $81.276,92 por el feriado trabajado. Se incorpora como
    # remunerativo para validar aquí las bases; su fórmula se modelará en la
    # siguiente etapa y no se presume en este test.
    resultado = MotorLiquidacion(parametros, AmparoSet()).liquidar_mensual(
        empleado, Periodo(2026, 7), escala, config,
        Novedades(premio=D("81276.92"), tipo_premio="remunerativo"),
        a_fecha=date(2026, 7, 28),
    )

    aporte_rem = next(c for c in resultado.conceptos
                      if c.codigo == "APORTE_ADEF_REM_414/05")
    aporte_nr = next(c for c in resultado.conceptos
                     if c.codigo == "APORTE_ADEF_NR_414/05")
    assert resultado.total_remunerativo.monto == D("2275753.82")
    assert aporte_rem.importe.monto == D("45515.08")
    assert aporte_nr.importe.monto == D("1082.01")
    assert aporte_rem.destino_pago == "ADEF"
    assert aporte_rem.codigo_boleta == "ADEF_APORTES"


def test_agosto_2026_adef_liquida_rosalia_sin_sumas_unicas_vencidas():
    desde = date(2026, 8, 1)
    parametros = ParametroSet([
        ParametroLegal("APORTE_JUBILACION", D("0.11"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0.05"), "%", "empleador", desde),
        ParametroLegal(
            "APORTE_ADEF_REM_414/05", D("0.02"), "%", "ded_todos", desde,
            cct_numero="414/05", incidencias={
                "base_deduccion": "remunerativa",
                "destino_pago": "ADEF",
                "codigo_boleta": "ADEF_APORTES",
            },
        ),
    ])
    empleado = Empleado(
        "Rosalía", "Ocampos", Cuil("27240320520"), date(2018, 4, 9),
        "414/05", "Empleado Especializado de Farmacia", "138",
    )
    escala = EscalaSalarial(
        "414/05", empleado.categoria, Dinero(D("1828730.75")),
        desde, date(2026, 8, 31), True,
        "ADEF escala oficial julio 2026 + ultraactividad art. 2",
    )
    config = CctConfig(
        "414/05", D("0"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
        antiguedad_escalones=(
            (1, D("0.05")), (2, D("0.10")), (5, D("0.20")),
            (10, D("0.30")), (15, D("0.35")), (20, D("0.40")),
            (25, D("0.50")),
        ),
    )

    resultado = MotorLiquidacion(parametros, AmparoSet()).liquidar_mensual(
        empleado, Periodo(2026, 8), escala, config,
        a_fecha=date(2026, 8, 31),
    )

    codigos = {concepto.codigo for concepto in resultado.conceptos}
    assert resultado.concepto("BASICO").importe.monto == D("1828730.75")
    assert resultado.concepto("ANTIGUEDAD").importe.monto == D("365746.15")
    assert resultado.concepto("APORTE_ADEF_REM_414/05").importe.monto == D("43889.54")
    assert resultado.bruto.monto == D("2194476.90")
    assert resultado.total_deducciones.monto == D("416950.62")
    assert resultado.neto.monto == D("1777526.28")
    assert not any(codigo.startswith("FARMACIA_NR") for codigo in codigos)
