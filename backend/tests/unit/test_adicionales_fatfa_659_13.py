from datetime import date
from decimal import Decimal
from pathlib import Path

from domain.entities.concepto import TipoConcepto
from domain.entities.empleado import Empleado
from domain.entities.fatfa_659_13 import configurar_adicionales_fatfa
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


ROOT = Path(__file__).resolve().parents[2]
UI = (ROOT / "src/ui_page.py").read_text(encoding="utf-8")
SQL = (ROOT / "migrations/053_adicionales_fatfa_659_13.sql").read_text(encoding="utf-8")


def _param(codigo, valor, unidad="%", ambito="empleado", cct=None, incidencias=None):
    return ParametroLegal(
        codigo, Decimal(valor), unidad, ambito, date(2026, 8, 1), None,
        True, "fuente", cct, incidencias or {},
    )


def _config():
    referencias = {
        "BLOQUEO_DT": Decimal("1650389.40"),
        "BLOQUEO_DT_NR": Decimal("42681.99"),
        "AUX_BLOQUEO": Decimal("1320311.52"),
        "AUX_BLOQUEO_NR": Decimal("34145.59"),
        "TITULO_60": Decimal("990233.64"),
        "TITULO_60_NR": Decimal("25609.20"),
    }
    adicionales, bases = configurar_adicionales_fatfa(
        Decimal("1403185.39"), referencias,
    )
    return CctConfig(
        "659/13", Decimal("0"), Decimal("12"), Decimal("195"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
        antiguedad_escalones=((1, Decimal("0.07")), (8, Decimal("0.21"))),
        adicionales=adicionales, bases_referencia=bases,
    )


def _parametros():
    return ParametroSet([
        _param("APORTE_JUBILACION", "0.11"),
        _param("APORTE_LEY19032", "0.03"),
        _param("APORTE_OBRA_SOCIAL", "0.03"),
        _param("CONTRIB_JUBILACION", "0.18", ambito="empleador"),
        _param("CONTRIB_OBRA_SOCIAL", "0.05", ambito="empleador"),
        _param("APORTE_MODERNIZACION", "0"),
        _param(
            "FATFA_NR_FARMACEUTICO", "55213.68", "ARS", "no_rem", "659/13",
            {"categoria": "Farmacéutico", "aporte_sindicato": True},
        ),
        _param(
            "FATFA_SOLIDARIO", "0.01", "%", "ded_todos", "659/13",
            {"base_deduccion": "sindical"},
        ),
        _param(
            "FATFA_CAPACITACION", "0.01", "%", "contrib_emp", "659/13",
            {"base_contribucion": "basico"},
        ),
    ])


def test_panel_fatfa_solicita_hechos_sin_aplicar_adicionales_automaticos():
    assert 'id="novFatfa"' in UI
    assert "Director Técnico con bloqueo" in UI
    assert "FATFA_BLOQUEO_DT_NR" in UI
    assert "FATFA_FALLA_CAJA" in UI
    assert "FATFA_IDIOMA" in UI


def test_referencias_titulo_quedan_versionadas_y_provisorias():
    for valor in ("1650389.40", "42681.99", "1320311.52", "34145.59", "990233.64", "25609.20"):
        assert valor in SQL
    assert "'PROVISORIA',false,1,true" in SQL


def test_titulo_y_falla_caja_son_no_remunerativos_y_exactos():
    empleado = Empleado(
        nombre="Prueba", apellido="FATFA", cuil=Cuil("27240320520"),
        fecha_ingreso=date(2018, 5, 7), cct_numero="659/13",
        categoria="Farmacéutico", legajo="1", afiliado_sindicato=False,
    )
    escala = EscalaSalarial(
        "659/13", "Farmacéutico", Dinero(Decimal("2134953.36")),
        date(2026, 8, 1), date(2026, 8, 31), False, "FATFA",
        provisoria=True,
    )
    novedades = Novedades(adicionales_convencionales=(
        "FATFA_BLOQUEO_DT", "FATFA_BLOQUEO_DT_NR", "FATFA_FALLA_CAJA",
    ))
    resultado = MotorLiquidacion(_parametros(), AmparoSet()).liquidar_mensual(
        empleado, Periodo.desde_texto("2026-08"), escala, _config(), novedades,
    )

    esperado = {
        "FATFA_BLOQUEO_DT": Decimal("1650389.40"),
        "FATFA_BLOQUEO_DT_NR": Decimal("42681.99"),
        "FATFA_FALLA_CAJA": Decimal("426990.67"),
    }
    for codigo, importe in esperado.items():
        concepto = resultado.concepto(codigo)
        assert concepto.tipo == TipoConcepto.NO_REMUNERATIVO
        assert concepto.importe.monto == importe
