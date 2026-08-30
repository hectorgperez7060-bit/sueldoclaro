from datetime import date
from decimal import Decimal as D
from pathlib import Path

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.payroll_engine.config import CctConfig, ReglaAdicionalConfig
from domain.payroll_engine.engine import MotorLiquidacion
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


SQL = (Path(__file__).parents[2] / "migrations" / "039_uthgra_389_04_agosto_2026.sql").read_text()


def _motor():
    desde = date(2026, 1, 1)
    parametros = ParametroSet([
        ParametroLegal("APORTE_JUBILACION", D("0.11"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0.05"), "%", "empleador", desde),
        ParametroLegal(
            "UTHGRA_ACUERDO_2026_SEGUNDA_N1_D", D("68000"), "ARS", "no_rem",
            date(2026, 8, 1), date(2026, 8, 31), False, "acuerdo presentado", "389/04",
            {"categoria": "Nivel 1 · Categoría D", "regla_jornada": "proporcional"},
        ),
    ])
    return MotorLiquidacion(parametros, AmparoSet())


def test_matriz_oficial_tiene_33_combinaciones_y_no_fabrica_homologacion():
    assert SQL.count("('D',") == 6
    assert SQL.count("('C',") == 6
    assert SQL.count("('B',") == 7
    assert SQL.count("('A',") == 7
    assert SQL.count("('ESP',") == 7
    assert "PROVISORIA" in SQL
    assert "is_verified=false" in SQL


def test_agosto_conserva_basico_y_segunda_cuota_exactos_del_anexo():
    assert "('D',1, 990555, 68000)" in SQL
    assert "('B',7,1538297,105000)" in SQL
    assert "('A',7,1840959,126000)" in SQL
    assert "('ESP',7,1970475,134000)" in SQL


def test_motor_aplica_antiguedad_asistencia_y_servicio_sobre_basico():
    config = CctConfig(
        "389/04", D("0"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
        antiguedad_escalones=((1, D("0.01")), (7, D("0.05")), (9, D("0.06"))),
        adicionales=(
            ReglaAdicionalConfig(
                "ASISTENCIA_PERFECTA", "Asistencia perfecta", D("0.10"),
                "basico_categoria", "11.5", aplica_automaticamente=True,
            ),
            ReglaAdicionalConfig(
                "COMPLEMENTO_SERVICIO", "Complemento de servicio", D("0.12"),
                "basico_categoria", "11.6", aplica_automaticamente=True,
            ),
        ),
    )
    empleado = Empleado(
        "Ana", "Prueba", Cuil("27307324666"), date(2018, 4, 9),
        "389/04", "Nivel 1 · Categoría D", "1",
    )
    escala = EscalaSalarial(
        "389/04", empleado.categoria, Dinero(D("990555")),
        date(2026, 8, 1), date(2026, 8, 31), False, "acuerdo presentado",
        provisoria=True,
    )
    resultado = _motor().liquidar_mensual(
        empleado, Periodo(2026, 8), escala, config, a_fecha=date(2026, 8, 28)
    )
    assert resultado.concepto("ANTIGUEDAD").importe.monto == D("49527.75")
    assert resultado.concepto("ASISTENCIA_PERFECTA").importe.monto == D("99055.50")
    assert resultado.concepto("COMPLEMENTO_SERVICIO").importe.monto == D("118866.60")
    assert resultado.concepto("UTHGRA_ACUERDO_2026_SEGUNDA_N1_D").importe.monto == D("68000.00")