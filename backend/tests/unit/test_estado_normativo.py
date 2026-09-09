import pytest
from fastapi import HTTPException

from api.routes.convenios import _estado_item, _fecha_periodo


def test_periodo_normativo_estricto():
    assert _fecha_periodo("2026-08").isoformat() == "2026-08-28"
    for invalido in ("2026-8", "2026-13", "texto"):
        with pytest.raises(HTTPException):
            _fecha_periodo(invalido)


def test_regla_no_confirmada_y_sin_fuente_informa_ambos_problemas():
    item = _estado_item("parametro", "APORTE_X", False, "")
    assert not item["verificado"]
    assert "dato pendiente de confirmar contra la fuente publicada" in item["problemas"]
    assert "fuente legal faltante" in item["problemas"]


def test_regla_aprobada_con_fuente_no_tiene_problemas():
    item = _estado_item("escala", "Maestranza A", True, "Circular oficial")
    assert item["problemas"] == []
