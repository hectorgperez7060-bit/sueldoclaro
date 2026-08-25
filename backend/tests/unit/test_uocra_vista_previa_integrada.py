from pathlib import Path

from application.dto.schemas import DetalleOut, LiquidarIn, NovedadMensualIn


ROOT = Path(__file__).resolve().parents[2]


def test_liquidacion_uocra_ya_no_depende_de_un_interruptor_de_vista_previa():
    body = LiquidarIn(periodo="2026-08")
    assert not hasattr(body, "vista_previa_uocra")
    detalle = DetalleOut(
        empleado_id="e", bruto=0, total_deducciones=0, neto=0,
        conceptos=[], vista_previa=True,
    )
    assert detalle.vista_previa is True
    codigo = (ROOT / "src/application/use_cases/liquidar_periodo.py").read_text()
    assert "VISTA_PREVIA_UOCRA_NO_CONFIRMABLE" not in codigo
    assert "replace(escala, habilitada_liquidacion=True)" not in codigo


def test_base_mes_anterior_es_auditable_y_no_negativa():
    datos = dict(
        empleado_id="12345678-1234-1234-1234-123456789012",
        periodo="2026-08",
        base_contribucion_uocra_mes_anterior=1000000,
    )
    novedad = NovedadMensualIn(**datos)
    assert novedad.base_contribucion_uocra_mes_anterior == 1000000


def test_migracion_y_ui_exponen_base_anterior_y_bloqueos():
    sql = (ROOT / "migrations/023_base_previa_y_vista_uocra.sql").read_text()
    ui = (ROOT / "src/ui_page.py").read_text()
    assert "ADD COLUMN IF NOT EXISTS base_contribucion_uocra_mes_anterior" in sql
    assert "ck_novedad_base_uocra_anterior_no_negativa" in sql
    assert "novBaseUocraAnterior" in ui
    assert "novBaseUocraAnterior" in ui
    convenios = (ROOT / "src/api/routes/convenios.py").read_text()
    assert "vista_previa_habilitada = False" in convenios
    assert "Liquidación UOCRA bloqueada" in (
        ROOT / "src/application/use_cases/liquidar_periodo.py"
    ).read_text()
