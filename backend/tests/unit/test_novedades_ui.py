from ui_page import HTML


def test_ui_muestra_seccion_sin_overlay_ni_demo_excel():
    assert "Novedades mensuales" in HTML
    assert "Plantilla de empleados" in HTML
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


def test_ui_muestra_historial_de_carpetas_mensuales_solo_lectura():
    assert "Carpeta mensual" in HTML
    assert 'id="tablaCarpetas"' in HTML
    assert "api('/carpetas-mensuales?periodo='" in HTML
    assert "v${c.version}" in HTML
    assert "(c.hash_sha256||'').slice(0,12)" in HTML


def test_ui_incluye_identidad_visual_propia_en_app_y_recibo():
    assert 'aria-label="Logo Sueldo Claro"' in HTML
    assert 'class="marca-recibo"' in HTML
    assert "Google" not in HTML


def test_ui_adapta_tablas_y_acciones_a_celular():
    assert 'class="tabla-movil"' in HTML
    assert 'data-label="Empleado"' in HTML
    assert 'class="acciones-tabla"' in HTML
    assert "table.tabla-movil thead{display:none}" in HTML


def test_ui_muestra_bloqueo_real_sin_confundir_calculo_con_confirmacion():
    assert "n.bloqueada" in HTML
    assert "Cerrada por liquidación confirmada" in HTML
    assert "Editable: la liquidación está calculada, no confirmada" in HTML


def test_ui_formatea_fecha_en_hora_argentina_24_horas():
    assert "America/Argentina/Buenos_Aires" in HTML
    assert "hourCycle:'h23'" in HTML
