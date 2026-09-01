from ui_page import HTML


def test_la_ui_envia_confirmacion_explicita_y_ofrece_reintento():
    assert "async function liquidar(confirmarProvisorios=false)" in HTML
    assert "confirmar_provisorios:confirmarProvisorios" in HTML
    assert "onclick=\"liquidar(true)\"" in HTML
    assert "Confirmar escala y calcular" in HTML
    assert "AUTOGESTIÓN SIN FIRMA" in HTML


def test_el_recibo_visible_marca_la_escala_provisoria():
    assert "ESCALA PROVISORIA CONFIRMADA" in HTML
    assert "AUTOGESTIÓN · ESCALA PROVISORIA CONFIRMADA · SIN FIRMA" in HTML
