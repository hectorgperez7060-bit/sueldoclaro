"""La autogestión no depende de una aprobación contable universal."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from application.dto.schemas import DetalleOut
from api.routes.recibos import DatosCargasPdf, ReciboPdfIn


ROOT = Path(__file__).resolve().parents[2]


def test_salida_de_liquidacion_no_publica_un_bloqueo_contable():
    assert "pendiente_aprobacion_contador" not in DetalleOut.model_fields


def test_recibo_no_acepta_un_estado_contable_declarado_por_el_navegador():
    assert "pendiente_aprobacion_contador" not in ReciboPdfIn.model_fields


def test_ultimo_deposito_exige_fecha_periodo_y_banco():
    with pytest.raises(ValidationError):
        DatosCargasPdf(fecha="2026-08-10", periodo="", banco="")
    cargas = DatosCargasPdf(
        fecha="2026-08-10", periodo="2026-07", banco="Banco Nación"
    )
    assert cargas.periodo == "2026-07"


def test_interfaz_explica_autogestion_firma_y_art_sin_volver_obligatorio_al_contador():
    ui = (ROOT / "src/ui_page.py").read_text(encoding="utf-8")
    for texto in (
        "AUTOGESTIÓN DEL EMPLEADOR",
        "Emitir recibo para firma",
        "no necesita aprobación previa de un contador",
        "ART de este trabajador *",
        "importe individual exacto de la póliza",
        "Revisión profesional no solicitada · opcional",
    ):
        assert texto in ui
    assert "PENDIENTE APROBACIÓN CONTADOR" not in ui
    assert "PENDIENTE DE REVISIÓN Y APROBACIÓN POR CONTADOR PÚBLICO" not in ui
