from decimal import Decimal
from pathlib import Path

import pytest

from application.dto.schemas import NovedadMensualIn
from domain.entities.novedad import DatosNovedadMensual
from infrastructure.database.models import NovedadMensual
from ui_page import HTML


ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/020_novedades_quincenales_uocra.sql").read_text(encoding="utf-8")
SQL_DETALLE = (ROOT / "migrations/022_detalle_feriados_y_criterio_fcl.sql").read_text(encoding="utf-8")


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


def test_detalle_feriados_y_criterio_profesional_se_persisten():
    datos = DatosNovedadMensual(
        periodo="2026-08", feriados_no_trabajados=1,
        feriados_habilitados_q2=1,
        feriados_uocra_detalle=({
            "fecha": "2026-08-17", "trabajado": False,
            "cumple_requisito_art168": True,
            "horas_jornada_anterior": "8",
            "remuneraciones_accesorias": "10000",
        },),
        fcl_criterio_aniversario="MES_COMPLETO_12",
        fcl_aprobado_por="CPN Ana · MP 123",
        fcl_fundamento="Criterio profesional documentado",
    )
    persistido = datos.para_persistir()
    assert persistido["feriados_uocra_detalle"][0]["fecha"] == "2026-08-17"
    assert persistido["fcl_criterio_aniversario"] == "MES_COMPLETO_12"


def test_detalle_feriados_debe_coincidir_con_totales_y_periodo():
    detalle = ({
        "fecha": "2026-07-09", "trabajado": False,
        "cumple_requisito_art168": True, "horas_jornada_anterior": "8",
    },)
    with pytest.raises(ValueError, match="pertenecer al período"):
        DatosNovedadMensual(
            periodo="2026-08", feriados_no_trabajados=1,
            feriados_uocra_detalle=detalle,
        )
    with pytest.raises(ValueError, match="coincidir"):
        DatosNovedadMensual(
            periodo="2026-08", feriados_no_trabajados=0,
            feriados_uocra_detalle=({**detalle[0], "fecha": "2026-08-17"},),
        )


def test_migracion_022_preserva_rls_y_restringe_json_y_criterio():
    assert SQL_DETALLE.count("ADD COLUMN IF NOT EXISTS") == 4
    assert "jsonb_typeof(feriados_uocra_detalle)='array'" in SQL_DETALLE
    assert "MES_COMPLETO_12" in SQL_DETALLE and "PRORRATEO_DIAS" in SQL_DETALLE
    assert "DISABLE ROW LEVEL SECURITY" not in SQL_DETALLE


def test_ui_agrega_feriados_individuales_y_decision_profesional():
    assert 'id="novFeriadosUocraLista"' in HTML
    assert "function agregarFeriadoUocra" in HTML
    assert "function sincronizarFeriadosUocra" in HTML
    assert 'id="novFclCriterio"' in HTML
    assert "feriados_uocra_detalle:detalleFeriadosUocra()" in HTML
