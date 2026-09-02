"""La autogestión no depende de una aprobación contable universal."""
from pathlib import Path

from application.dto.schemas import DetalleOut
from api.routes.recibos import ReciboPdfIn


ROOT = Path(__file__).resolve().parents[2]


def test_salida_de_liquidacion_no_publica_un_bloqueo_contable():
    assert "pendiente_aprobacion_contador" not in DetalleOut.model_fields


def test_recibo_no_acepta_un_estado_contable_declarado_por_el_navegador():
    assert "pendiente_aprobacion_contador" not in ReciboPdfIn.model_fields


def test_interfaz_explica_autogestion_firma_y_art_sin_volver_obligatorio_al_contador():
    ui = (ROOT / "src/ui_page.py").read_text(encoding="utf-8")
    for texto in (
        "AUTOGESTIÓN DEL EMPLEADOR",
        "Emitir recibo para firma",
        "no necesita aprobación previa de un contador",
        "¿Qué hago si aparece ART pendiente?",
        "porcentaje sobre la masa salarial",
        "Revisión profesional no solicitada · opcional",
    ):
        assert texto in ui
    assert "PENDIENTE APROBACIÓN CONTADOR" not in ui
    assert "PENDIENTE DE REVISIÓN Y APROBACIÓN POR CONTADOR PÚBLICO" not in ui
