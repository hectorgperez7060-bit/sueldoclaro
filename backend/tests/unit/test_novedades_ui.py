from ui_page import HTML


def test_ui_muestra_seccion_sin_overlay_ni_demo_excel():
    assert "Novedades mensuales" in HTML
    assert 'id="formNovedad"' in HTML
    assert 'id="tablaNovedades"' in HTML
    assert "Probar demo Excel" not in HTML
    assert "overlay" not in HTML.lower()


def test_ui_usa_crud_de_novedades():
    assert "api('/novedades?periodo='" in HTML
    assert "'/novedades/'+editandoNovedadId" in HTML
    assert "api('/novedades/'+id,'DELETE')" in HTML
    assert 'id="novTipoPremio"' in HTML
    assert "Pendiente de definir (no calcular)" in HTML


def test_ui_liquida_sin_duplicar_novedades_en_el_body():
    assert "tipo:'mensual', novedades:[]" in HTML


def test_ui_muestra_semaforo_normativo():
    assert 'id="estadoNormativo"' in HTML
    assert "Convenio en revisión: usar sólo para pruebas" in HTML
