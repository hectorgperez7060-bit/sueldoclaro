from ui_page import HTML


def test_la_ui_envia_confirmacion_explicita_y_ofrece_reintento():
    assert "async function liquidar(confirmarProvisorios=false)" in HTML
    assert "confirmar_provisorios:confirmarProvisorios" in HTML
    assert "onclick=\"liquidar(true)\"" in HTML
    assert "Aceptar escala provisoria y calcular" in HTML
    assert "esto no exige aprobación de un contador" in HTML


def test_el_recibo_visible_marca_autogestion_y_escala_provisoria():
    assert "ESCALA PROVISORIA CONFIRMADA" in HTML
    assert "AUTOGESTIÓN DEL EMPLEADOR" in HTML
