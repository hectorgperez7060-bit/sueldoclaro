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


def test_ui_ofrece_navegacion_y_cambio_de_empresa_sin_mezclar_contextos():
    assert 'class="lateral"' in HTML
    assert 'id="empresaActiva" onchange="cambiarEmpresa(this.value)"' in HTML
    assert 'id="nuevaEmpresa"' in HTML
    assert "async function cargarEmpresas()" in HTML
    assert "api('/auth/empresas')" in HTML
    assert "api('/auth/seleccionar-empresa','POST'" in HTML
    assert "Los empleados y liquidaciones visibles pertenecen únicamente" in HTML


def test_recibo_imprime_antiguedad_singular_y_evitar_enlaces_azules_ios():
    assert "a===1?'año':'años'" in HTML
    assert "a[x-apple-data-detectors]" in HTML


def test_recibo_compacta_impresion_para_una_hoja_a4():
    assert "@page{size:A4 portrait;margin:5mm}" in HTML
    assert ".resumen svg{display:none}" in HTML
    assert "width:200mm;max-width:200mm" in HTML
    assert "page-break-inside:avoid" in HTML


def test_recibo_se_descarga_desde_backend_sin_repaginar_en_safari():
    assert "async function descargarReciboPdf" in HTML
    assert "fetch('/recibos/pdf'" in HTML
    assert "Descargar recibo PDF — una hoja A4" in HTML


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


def test_ui_pide_convenios_del_periodo_y_avisa_los_sin_escala_sin_bloquear_legajo():
    assert "'/convenios'+(periodo?'?periodo='" in HTML
    assert "o.disabled=!c.tiene_escala_vigente" not in HTML
    assert "sin escala vigente" in HTML
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


def test_edicion_empleado_permite_fecha_manual_y_separa_convenio_de_obra_social():
    assert 'id="eNacimiento" type="text" inputmode="numeric"' in HTML
    assert 'oninput="formatearFecha(this)"' in HTML
    assert "function formatearFecha(campo)" in HTML
    assert "15081974 se transforma en 15/08/1974" in HTML
    assert "Revisá la fecha: escribí los 8 números" in HTML
    assert "function fechaIso(valor,nombre)" in HTML
    assert "'414/05':{actividad:'Farmacia',sindicato:'ADEF'" in HTML
    assert 'id="eActividad" onchange="llenarConvenios()"' in HTML
    assert 'id="eSindicato" readonly' in HTML
    assert "function actividadConvenio(c)" in HTML
    assert "function llenarConvenios(preseleccion=null)" in HTML
    assert "o.textContent=`CCT ${c.numero} — ${sindicato}`" in HTML
    assert "OSADEF - Obra Social de las Asociaciones de Empleados de Farmacia" in HTML
    assert "Obra social (independiente del sindicato)" in HTML
    assert "o.disabled=!c.tiene_escala_vigente" not in HTML
