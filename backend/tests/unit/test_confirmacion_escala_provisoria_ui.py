from ui_page import HTML


def test_la_ui_envia_confirmacion_explicita_y_ofrece_reintento():
    assert "async function liquidar(confirmarProvisorios=false)" in HTML
    assert "confirmar_provisorios:confirmarProvisorios" in HTML
    assert "onclick=\"liquidar(true)\"" in HTML
    assert "Confirmar y calcular provisoriamente" in HTML


def test_el_recibo_visible_marca_la_escala_provisoria():
    assert "ESCALA PROVISORIA CONFIRMADA" in HTML
    assert "No equivale a una escala nueva ni a una aprobación profesional" in HTML
