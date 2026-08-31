from datetime import date
from decimal import Decimal
from pathlib import Path

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/052_fatfa_659_13_agosto_2026.sql").read_text(encoding="utf-8")


def _p(codigo, valor, unidad="%", ambito="empleado", cct=None, incidencias=None):
    return ParametroLegal(
        codigo, Decimal(valor), unidad, ambito, date(2026, 8, 1),
        None, True, "fuente verificada", cct, incidencias or {},
    )


def test_migracion_contiene_escala_y_sumas_nr_oficiales():
    for valor in (
        "1403185.39", "1486139.03", "1580289.30", "1933355.60", "2134953.36",
        "36288.86", "38434.19", "40869.08", "50000.00", "55213.68",
    ):
        assert valor in SQL
    assert "cant_escalas <> 7 OR cant_nr <> 7" in SQL
    assert "'PROVISORIA',false,1,true,true" in SQL


def test_migracion_incorpora_aportes_homologados_sin_inventar_base():
    assert "'FATFA_SOLIDARIO',0.01,'%','ded_todos'" in SQL
    assert '"base_deduccion":"sindical"' in SQL
    assert "'FATFA_CAPACITACION',0.01,'%','contrib_emp'" in SQL
    assert '"base_contribucion":"basico"' in SQL


def test_motor_fatfa_usa_antiguedad_escalonada_y_base_basico_para_capacitacion():
    parametros = ParametroSet([
        _p("APORTE_JUBILACION", "0.11"),
        _p("APORTE_LEY19032", "0.03"),
        _p("APORTE_OBRA_SOCIAL", "0.03"),
        _p("CONTRIB_JUBILACION", "0.18", ambito="empleador"),
        _p("CONTRIB_OBRA_SOCIAL", "0.05", ambito="empleador"),
        _p("APORTE_MODERNIZACION", "0"),
        _p(
            "FATFA_NR_CADETE", "36288.86", "ARS", "no_rem", "659/13",
            {
                "categoria": "Cadetes", "aporte_sindicato": True,
                "aporte_jubilacion": False, "aporte_obra_social": False,
            },
        ),
        _p(
            "FATFA_SOLIDARIO", "0.01", "%", "ded_todos", "659/13",
            {"base_deduccion": "sindical"},
        ),
        _p(
            "FATFA_CAPACITACION", "0.01", "%", "contrib_emp", "659/13",
            {"base_contribucion": "basico"},
        ),
    ])
    escalones = tuple(
        (anios, Decimal(pct)) for anios, pct in (
            (1, "0.07"), (2, "0.09"), (3, "0.11"), (4, "0.13"),
            (5, "0.15"), (6, "0.17"), (7, "0.19"), (8, "0.21"),
            (9, "0.23"), (10, "0.25"), (11, "0.27"), (12, "0.29"),
            (13, "0.31"), (14, "0.33"), (15, "0.35"), (16, "0.37"),
            (17, "0.39"), (18, "0.41"), (19, "0.43"), (20, "0.45"),
            (25, "0.50"),
        )
    )
    config = CctConfig(
        "659/13", Decimal("0"), Decimal("12"), Decimal("195"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
        antiguedad_escalones=escalones,
    )
    empleado = Empleado(
        nombre="Prueba", apellido="FATFA", cuil=Cuil("27240320520"),
        fecha_ingreso=date(2018, 5, 7), cct_numero="659/13",
        categoria="Cadetes", legajo="1", afiliado_sindicato=False,
    )
    escala = EscalaSalarial(
        "659/13", "Cadetes", Dinero(Decimal("1403185.39")),
        date(2026, 8, 1), date(2026, 8, 31), True, "FATFA",
    )

    resultado = MotorLiquidacion(parametros, AmparoSet()).liquidar_mensual(
        empleado, Periodo.desde_texto("2026-08"), escala, config,
    )

    assert resultado.concepto("ANTIGUEDAD").importe.monto == Decimal("294668.93")
    assert resultado.concepto("FATFA_NR_CADETE").importe.monto == Decimal("36288.86")
    assert resultado.concepto("FATFA_SOLIDARIO").importe.monto == Decimal("17341.43")
    contrib = resultado.concepto("FATFA_CAPACITACION")
    assert contrib.base_calculo.monto == Decimal("1403185.39")
    assert contrib.importe.monto == Decimal("14031.85")
