from decimal import Decimal
from pathlib import Path

import pytest

from application.dto.schemas import NovedadMensualIn
from domain.entities.novedad import DatosNovedadMensual
from infrastructure.database.models import NovedadMensual
from ui_page import HTML


ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/020_novedades_quincenales_uocra.sql").read_text(encoding="utf-8")


def test_dominio_conserva_dos_quincenas_independientes():
    datos = DatosNovedadMensual(
        periodo="2026-08", feriados_no_trabajados=1,
        horas_normales_q1=Decimal("88.5"), horas_normales_q2=Decimal("80"),
        asistencia_perfecta_q1=True, asistencia_perfecta_q2=False,
        feriados_habilitados_q1=1,
    )
    persistido = datos.para_persistir()
    assert persistido["horas_normales_q1"] == Decimal("88.5")
    assert persistido["asistencia_perfecta_q1"] is True
    assert persistido["asistencia_perfecta_q2"] is False


def test_no_permite_habilitar_mas_feriados_que_los_informados():
    with pytest.raises(ValueError, match="no pueden superar"):
        DatosNovedadMensual(
            periodo="2026-08", feriados_no_trabajados=1,
            feriados_habilitados_q1=1, feriados_habilitados_q2=1,
        )


def test_dto_y_modelo_exponen_campos_quincenales():
    dto = NovedadMensualIn(
        empleado_id="11111111-1111-1111-1111-111111111111",
        periodo="2026-08", horas_normales_q1=Decimal("80"),
        asistencia_perfecta_q1=True,
    )
    assert dto.datos_dominio().horas_normales_q1 == Decimal("80")
    for columna in (
        "horas_normales_q1", "horas_normales_q2",
        "asistencia_perfecta_q1", "asistencia_perfecta_q2",
        "feriados_habilitados_q1", "feriados_habilitados_q2",
    ):
        assert columna in NovedadMensual.__table__.columns


def test_migracion_es_idempotente_y_preserva_rls_existente():
    assert SQL.count("ADD COLUMN IF NOT EXISTS") == 6
    assert "ALTER TABLE public.novedad_mensual" in SQL
    assert "DISABLE ROW LEVEL SECURITY" not in SQL
    assert "feriados_habilitados_q1 + feriados_habilitados_q2 <= feriados_no_trabajados" in SQL


def test_ui_muestra_control_solo_al_seleccionar_uocra():
    assert 'id="novUocra"' in HTML
    assert "emp.cct_numero==='76/75'?'block':'none'" in HTML
    assert "Horas normales · 1.ª quincena" in HTML
    assert "Asistencia perfecta · 2.ª quincena" in HTML
