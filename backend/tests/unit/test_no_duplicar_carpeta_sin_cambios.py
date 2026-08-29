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


def test_ui_no_publica_como_total_un_f931_sin_art():
    ui = (
        Path(__file__).parents[2] / "src" / "ui_page.py"
    ).read_text(encoding="utf-8")

    assert "Subtotal calculado — falta ART" in ui
    assert "Total a depositar (F.931)" not in ui
