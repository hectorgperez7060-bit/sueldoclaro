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


def test_ui_muestra_obligaciones_sindicales_sin_presentarlas_como_boleta_oficial():
    assert "function resumenSindical(d)" in HTML
    assert "Obligaciones sindicales agrupadas" in HTML
    assert "No es una boleta presentable" in HTML
    assert "No se generó ningún pago por suposición" in HTML


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


def test_ui_renueva_sesion_y_reintenta_sin_pedir_clave():
    assert "async function renovarSesion()" in HTML
    assert "fetch('/auth/refresh'" in HTML
    assert "if(await renovarSesion()) return api(ruta,metodo,body,false)" in HTML
    assert "else if(localStorage.getItem('sc_refresh'))" in HTML


def test_ui_pide_convenios_del_periodo_y_bloquea_los_sin_escala():
    assert "'/convenios'+(periodo?'?periodo='" in HTML
    assert "o.disabled=!c.tiene_escala_vigente" in HTML
    assert "sin escala vigente" in HTML


def test_ui_muestra_adicionales_farmacia_solo_para_cct_414_05():
    assert 'id="novFarmacia"' in HTML
    assert "emp.cct_numero==='414/05'" in HTML
    assert "DIRECCION_TECNICA" in HTML
    assert "COMPLEMENTO_DIRECCION" in HTML
    assert "TITULO_FARMACEUTICO" in HTML
    assert "IDIOMA" in HTML
    assert "cantidades_adicionales" in HTML
    assert "NOCTURNO_VOLUNTARIO" in HTML
    assert 'id="novHorasNocturnas"' in HTML
    assert 'id="novHorasTotales"' in HTML
    assert "turno obligatorio, sereno ni vigilancia" in HTML
    assert 'id="novFaltanteCaja"' in HTML
    assert "Faltantes absorbidos por el fondo" in HTML


def test_ui_muestra_y_persiste_adicionales_sanidad_solo_para_cct_122_75():
    assert 'id="novSanidad"' in HTML
    assert "emp.cct_numero==='122/75'" in HTML
    assert 'id="novSectorSanidad"' in HTML
    assert "TERAPIA_8H" in HTML
    assert "MUCAMA_SECTOR_ESPECIAL" in HTML
    assert "MENTAL_ENFERMERIA" in HTML
    assert "ELECTRICISTA_TITULO" in HTML
    assert "LAB_AREA_CERRADA" in HTML
    assert "RAYOS_LAB_48H" in HTML
    assert "NOCTURNIDAD" in HTML
    assert 'id="novHorasNocturnasSanidad"' in HTML
    assert "datosAdicionalesConvenio()" in HTML
