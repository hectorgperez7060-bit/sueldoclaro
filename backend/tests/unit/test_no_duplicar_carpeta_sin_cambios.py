from pathlib import Path


def test_comparacion_ignora_solo_el_id_de_liquidacion():
    source = (
        Path(__file__).parents[2]
        / "src" / "application" / "use_cases" / "liquidar_periodo.py"
    ).read_text(encoding="utf-8")

    assert 'actual_comparable.pop("liquidacion_id", None)' in source
    assert 'anterior_comparable.pop("liquidacion_id", None)' in source
    assert '"sin_cambios": True' in source
    assert "await liq_repo.descartar(liq)" in source


def test_ui_suma_la_art_contractual_y_aclara_el_ffep_de_arca():
    ui = (
        Path(__file__).parents[2] / "src" / "ui_page.py"
    ).read_text(encoding="utf-8")

    assert "ART_CONTRATO:'ART según contrato del establecimiento'" in ui
    assert "Total calculado para F.931 (ARCA agrega FFEP)" in ui
    assert "Total sin ART: cargá el contrato del establecimiento" in ui
    assert "Subtotal calculado — falta ART" not in ui
