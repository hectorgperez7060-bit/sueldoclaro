from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.parametros import EscalaSalarial
from domain.payroll_engine.uocra import HoraExtraDetalladaUocra, calcular_horas_extra_detalladas
from domain.value_objects.dinero import Dinero


ROOT = Path(__file__).resolve().parents[2]


def escala():
    return EscalaSalarial(
        "76/75", "Oficial", Dinero.de("1000"), date(2026, 8, 1),
        date(2026, 8, 31), True, "Anexo I", False, "A", "HORA", False,
        "PUBLICADA_POR_PARTE_SIGNATARIA", Dinero.de("1000"),
    )


def test_dia_comun_50_y_domingo_100_separan_normal_de_recargo():
    r = calcular_horas_extra_detalladas(escala(), (
        HoraExtraDetalladaUocra(date(2026, 8, 3), Decimal("18"), Decimal("2")),
        HoraExtraDetalladaUocra(date(2026, 8, 9), Decimal("9"), Decimal("2")),
    ))
    assert r.horas_50 == 2
    assert r.horas_100 == 2
    assert r.valor_normal.monto == Decimal("4000.00")
    assert r.recargo_legal.monto == Decimal("3000.00")
    assert r.total.monto == Decimal("7000.00")


def test_sabado_que_cruza_las_13_se_divide_automaticamente():
    r = calcular_horas_extra_detalladas(escala(), (
        HoraExtraDetalladaUocra(date(2026, 8, 8), Decimal("12"), Decimal("2")),
    ))
    assert r.horas_50 == 1
    assert r.horas_100 == 1


@pytest.mark.parametrize("detalles,acumulado,mensaje", [
    ((HoraExtraDetalladaUocra(date(2026, 8, 3), Decimal("18"), Decimal("3.25")),), 0, "3 horas diarias"),
    (tuple(HoraExtraDetalladaUocra(date(2026, 8, d), Decimal("18"), Decimal("3")) for d in range(1, 12)), 0, "30 horas mensuales"),
    ((HoraExtraDetalladaUocra(date(2026, 8, 3), Decimal("18"), Decimal("2")),), 199, "200 horas anuales"),
])
def test_topes_reglamentarios_bloquean(detalles, acumulado, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        calcular_horas_extra_detalladas(escala(), detalles, Decimal(acumulado))


def test_migracion_y_ui_guardan_detalle_no_solo_totales():
    sql = (ROOT / "migrations/024_horas_extra_detalladas_uocra.sql").read_text()
    ui = (ROOT / "src/ui_page.py").read_text()
    assert "horas_extra_uocra_detalle jsonb" in sql
    assert "horas_extra_uocra_acumuladas_anio" in sql
    assert "detalleHorasExtraUocra" in ui
    assert "divide automáticamente el sábado a las 13" in ui
