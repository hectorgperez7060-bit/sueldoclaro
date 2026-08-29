from ui_page import HTML


def test_formulario_incluye_asistente_explicable():
    assert 'id="eTareaPrincipal"' in HTML
    assert 'onclick="analizarEncuadramiento()"' in HTML
    assert "/convenios/asistente-encuadramiento" in HTML
    assert "Usar esta propuesta" in HTML


def test_asistente_no_guarda_ni_liquida_automaticamente():
    inicio = HTML.index("async function analizarEncuadramiento()")
    fin = HTML.index("async function cargarEmpleados()", inicio)
    bloque = HTML[inicio:fin]
    assert "'/empleados'" not in bloque
    assert "'/liquidaciones'" not in bloque
