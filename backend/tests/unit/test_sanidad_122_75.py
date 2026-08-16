from datetime import date
from decimal import Decimal as D
from pathlib import Path

import pytest

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.entities.sanidad_122_75 import (
    CATEGORIAS_SANIDAD,
    antiguedad_sanidad,
    categoria_sanidad_canonica,
)
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


def _concepto(resultado, codigo):
    return next((c for c in resultado.conceptos if c.codigo == codigo), None)


def _resultado(mes: int):
    desde = date(2026, 1, 1)
    std = [
        ParametroLegal("APORTE_JUBILACION", D("0"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0"), "%", "empleador", desde),
    ]
    sindical = {
        "destino_pago": "FATSA", "codigo_boleta": "FATSA_122_APORTES",
        "canal_pago": "Sistema de Aportes FATSA",
        "url_pago": "https://www.sanidad.org.ar/aportesconvenios/",
    }
    propios = [
        ParametroLegal(
            "SANIDAD_SUMA_NR_AGO", D("80000"), "ARS", "no_rem", desde,
            cct_numero="122/75", incidencias={"aporte_sindicato": True},
        ),
        ParametroLegal(
            "APORTE_SOLIDARIO_FATSA_122/75", D("0.01"), "%", "ded_todos", desde,
            cct_numero="122/75", incidencias={"base_deduccion": "sindical", **sindical},
        ),
        ParametroLegal(
            "CONTRIB_EXTRAORDINARIA_FATSA_122/75", D("15000"), "ARS", "contrib_emp", desde,
            cct_numero="122/75", incidencias={
                "meses_excluidos": [6, 12], **sindical,
            },
        ),
        ParametroLegal(
            "CONTRIB_CAPACITACION_FATSA_122/75", D("0.01"), "%", "contrib_emp", desde,
            cct_numero="122/75", incidencias={
                "base_contribucion": "remunerativa", **sindical,
            },
        ),
    ]
    empleado = Empleado(
        "Ana", "Sanidad", Cuil("27307324666"), date(2021, 1, 1),
        "122/75", "Administrativo de Primera", "1",
    )
    escala = EscalaSalarial(
        "122/75", empleado.categoria, Dinero("1000000"), desde,
        is_verified=True, fuente="Acuerdo FATSA 19/06/2026",
    )
    config = CctConfig(
        "122/75", D("0.02"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
    )
    return MotorLiquidacion(ParametroSet(std + propios), AmparoSet()).liquidar_mensual(
        empleado, Periodo(2026, mes), escala, config, a_fecha=date(2026, mes, 28),
    )


def test_catalogo_oficial_tiene_las_34_categorias_y_cabe_en_la_bd():
    assert len(CATEGORIAS_SANIDAD) == 34
    assert max(map(len, CATEGORIAS_SANIDAD)) <= 120
    assert categoria_sanidad_canonica("administrativo de primera") == "Administrativo de Primera"
    with pytest.raises(ValueError):
        categoria_sanidad_canonica("Maestranza A")


def test_antiguedad_es_dos_por_ciento_por_ano_sin_presentismo_generico():
    assert antiguedad_sanidad(5) == 10
    resultado = _resultado(8)
    assert _concepto(resultado, "ANTIGUEDAD").importe.monto == D("100000.00")
    assert _concepto(resultado, "PRESENTISMO") is None


def test_solidaridad_incluye_suma_nr_y_conserva_boleta_fatsa():
    concepto = _concepto(_resultado(8), "APORTE_SOLIDARIO_FATSA_122/75")
    assert concepto.importe.monto == D("11800.00")
    assert concepto.destino_pago == "FATSA"
    assert concepto.canal_pago == "Sistema de Aportes FATSA"


def test_contribuciones_patronales_no_afectan_neto_y_respetan_exclusiones():
    agosto = _resultado(8)
    extraordinaria = _concepto(agosto, "CONTRIB_EXTRAORDINARIA_FATSA_122/75")
    capacitacion = _concepto(agosto, "CONTRIB_CAPACITACION_FATSA_122/75")
    assert extraordinaria.importe.monto == D("15000.00")
    assert capacitacion.importe.monto == D("11000.00")
    assert _concepto(_resultado(6), "CONTRIB_EXTRAORDINARIA_FATSA_122/75") is None
    assert agosto.neto.monto == D("1168200.00")


def test_migracion_no_extrapola_escala_despues_de_agosto():
    sql = Path("backend/migrations/005_sanidad_122_75_junio_agosto_2026.sql").read_text()
    assert "DATE '2026-08-31'" in sql
    assert "DATE '2026-09-01', DATE '2026-09-30', agosto" not in sql
    assert "APORTE_SOLIDARIO_FATSA_122/75" in sql
    assert "CONTRIB_EXTRAORDINARIA_FATSA_122/75" in sql


def test_migracion_informa_todos_los_campos_obligatorios_del_cct():
    sql = Path("backend/migrations/005_sanidad_122_75_junio_agosto_2026.sql").read_text()
    bloque_cct = sql.split("ON CONFLICT (numero)", 1)[0]
    assert "cuota_sindical_pct" in bloque_cct
    assert "presentismo_divisor" in bloque_cct
    assert "divisor_horas" in bloque_cct
