"""Navegación por secciones, historial de carpetas y recibos desde snapshot.

Las pruebas leen la fuente de la interfaz (una sola página embebida) igual que
el resto de la suite: verifican el contrato de la UI sin necesitar un navegador.
"""
from pathlib import Path

SRC = Path(__file__).parents[2] / "src"
UI = (SRC / "ui_page.py").read_text(encoding="utf-8")
LIQUIDAR = (SRC / "application" / "use_cases" / "liquidar_periodo.py").read_text(encoding="utf-8")

SECCIONES = (
    ("inicio", "seccionInicio"),
    ("empresas", "seccionEmpresas"),
    ("convenios", "seccionConvenios"),
    ("establecimientos", "seccionEstablecimientos"),
    ("empleados", "seccionEmpleados"),
    ("novedades", "seccionNovedades"),
    ("liquidar", "seccionLiquidar"),
    ("historial", "seccionHistorial"),
)


# --------------------------------------------------------------------------- #
# 1. Navegación real: una sección por vez, con hash y menú móvil.
# --------------------------------------------------------------------------- #
def test_las_ocho_secciones_existen_y_estan_declaradas_con_su_hash():
    for hash_, seccion_id in SECCIONES:
        assert f'class="tarjeta seccion-app" id="{seccion_id}"' in UI, seccion_id
        assert f"['{hash_}','{seccion_id}']" in UI, hash_


def test_al_elegir_una_seccion_se_ocultan_las_demas():
    assert "el.classList.toggle('visible', secId===id)" in UI
    assert ".seccion-app{display:none}" in UI
    assert ".seccion-app.visible{display:block}" in UI


def test_la_navegacion_ya_no_depende_del_desplazamiento_a_anclas():
    inicio = UI.index("function irA(")
    fin = UI.index("function seccionDelHash(")
    assert "scrollIntoView" not in UI[inicio:fin]


def test_inicio_es_la_seccion_predeterminada():
    assert "return SECCION_POR_HASH[clave] || 'seccionInicio'" in UI
    assert "if(!HASH_POR_SECCION[id]) id='seccionInicio'" in UI


def test_la_url_conserva_la_seccion_y_se_respeta_al_recargar():
    assert "history.replaceState(null,''," in UI
    assert "window.addEventListener('hashchange'" in UI
    assert "aplicarHash();" in UI
    # aplicarHash se llama al entrar, después de cargar los datos de la empresa.
    entrar = UI[UI.index("async function entrar()"):]
    assert "aplicarHash();" in entrar[:entrar.index("\nfunction toggleAlta")]


def test_en_telefono_el_menu_lateral_se_abre_y_se_cierra():
    assert 'id="botonMenu"' in UI and "onclick=\"alternarMenu()\"" in UI
    assert "function alternarMenu()" in UI and "function cerrarMenu()" in UI
    assert ".app-layout.menu-abierto .lateral{display:block}" in UI
    assert "@media(max-width:900px)" in UI
    # Al cambiar de sección el menú se cierra solo (si no, tapa el contenido).
    ira = UI[UI.index("function irA("):UI.index("function seccionDelHash(")]
    assert "cerrarMenu();" in ira


def test_en_telefono_el_menu_arranca_abierto_y_muestra_sus_accesos():
    assert "function abrirMenuInicialEnTelefono()" in UI
    assert "window.matchMedia('(max-width: 900px)').matches" in UI
    entrar = UI[UI.index("async function entrar()"):]
    assert "abrirMenuInicialEnTelefono();" in entrar[:entrar.index("\nfunction toggleAlta")]
    assert entrar.index("abrirMenuInicialEnTelefono();") < entrar.index("await recargarEmpresaActiva();")
    assert "✕ Cerrar menú" in UI


def test_el_ingreso_agrupa_las_consultas_en_dos_tandas():
    bloque = UI[UI.index("async function recargarEmpresaActiva()"):
                UI.index("async function entrar()")]
    assert bloque.count("Promise.all(") == 2
    for llamada in (
        "cargarEmpresas()", "api('/empresa')", "cargarConvenios()",
        "cargarEstablecimientos()", "cargarEmpleados()", "cargarCarpetas()",
        "cargarEmpresasSeccion()", "cargarNovedades()",
        "mostrarEstadoNormativo()", "cargarInicio()", "cargarGestorNormativo()",
    ):
        assert llamada in bloque


def test_cambiar_de_seccion_no_destruye_lo_ya_cargado():
    # Sólo se alterna la visibilidad de las secciones: no se vacían ni se
    # sacan del DOM, así que los formularios conservan lo que el usuario cargó.
    ira = UI[UI.index("function irA("):UI.index("function seccionDelHash(")]
    assert "innerHTML" not in ira
    assert "removeChild" not in ira
    assert "el.remove()" not in ira


# --------------------------------------------------------------------------- #
# 2. Historial de liquidaciones.
# --------------------------------------------------------------------------- #
def test_al_entrar_al_historial_se_cargan_las_carpetas_del_periodo_elegido():
    assert "seccionHistorial: ()=>cargarCarpetas()" in UI
    assert "'/carpetas-mensuales?periodo='+encodeURIComponent(periodo)" in UI


def test_la_version_mas_reciente_queda_marcada():
    assert "const ultima=lista.reduce((max,c)=>Math.max(max,Number(c.version)||0),0)" in UI
    assert "más reciente" in UI


def test_cada_version_muestra_estado_fecha_y_huella():
    ver = UI[UI.index("async function verVersion("):UI.index("function cerrarPanelVersion(")]
    assert "carpeta.estado" in ver
    assert "fechaHora(carpeta.created_at)" in ver
    assert "Huella SHA-256" in ver
    assert "carpeta.hash_sha256" in ver


def test_el_detalle_sale_de_contenido_detalles_y_no_se_recalcula():
    ver = UI[UI.index("async function verVersion("):UI.index("function cerrarPanelVersion(")]
    assert "(carpeta.contenido&&carpeta.contenido.detalles)||[]" in ver
    for campo in ("d.bruto", "d.total_deducciones", "d.neto"):
        assert campo in ver, campo
    assert "liquidar" not in ver.lower().replace("liquidación", "").replace("liquidacion", "")


def test_se_pueden_ver_los_conceptos_conservados_de_cada_empleado():
    assert "function verConceptosVersion(" in UI
    conceptos = UI[UI.index("function verConceptosVersion("):UI.index("// ----- Recibo histórico")]
    assert "detalle.conceptos" in conceptos
    assert "c.base_calculo" in conceptos and "c.unidad" in conceptos


# --------------------------------------------------------------------------- #
# 3. Recibos históricos reconstruidos desde el snapshot.
# --------------------------------------------------------------------------- #
def _cuerpo_historico() -> str:
    return UI[UI.index("function cuerpoReciboHistorico("):UI.index("async function pedirPdf(")]


def test_el_recibo_historico_no_usa_la_ultima_liquidacion_ni_el_motor():
    cuerpo = _cuerpo_historico()
    assert "ultimaLiq" not in cuerpo
    descarga = UI[UI.index("async function descargarReciboHistorico("):UI.index("async function descargarRecibosDeVersion(")]
    assert "ultimaLiq" not in descarga
    assert "/liquidaciones" not in descarga


def test_el_recibo_historico_se_arma_con_los_conceptos_guardados_en_la_carpeta():
    cuerpo = _cuerpo_historico()
    assert "(detalle.conceptos||[]).map" in cuerpo
    for campo in ("bruto:detalle.bruto", "total_deducciones:detalle.total_deducciones",
                  "neto:detalle.neto"):
        assert campo in cuerpo, campo
    # Los metadatos de boleta viajan para clasificar los aportes sindicales.
    assert "destino_pago:c.destino_pago" in cuerpo


def test_los_datos_del_trabajador_salen_primero_de_la_carpeta():
    cuerpo = _cuerpo_historico()
    for campo in ("doc.nombre||", "doc.apellido||", "doc.cuil||", "doc.fecha_ingreso||"):
        assert campo in cuerpo, campo


def test_una_carpeta_vieja_exige_confirmar_la_identidad_y_no_la_copia_silenciosamente():
    inicio = UI.index("function pedirDatosEmpleadoHistorico(")
    fin = UI.index("function cuerpoReciboHistorico(")
    pedir = UI[inicio:fin]
    assert "confirmá el dato histórico" in pedir
    cuerpo = _cuerpo_historico()
    assert "empleadosCache" not in cuerpo
    assert "ficha." not in cuerpo


def test_hay_boton_por_empleado_y_descarga_de_todos_los_recibos():
    assert "descargarReciboHistorico('" in UI
    assert "async function descargarRecibosDeVersion(" in UI
    assert "onclick=\"descargarRecibosDeVersion()\"" in UI


def test_una_carpeta_incompleta_declara_exactamente_que_falta():
    assert "function faltantesDeCarpeta(" in UI
    faltantes = UI[UI.index("function faltantesDeCarpeta("):UI.index("async function verVersion(")]
    for texto in ("razón social del empleador", "CUIT del empleador",
                  "domicilio legal del empleador", "datos personales de",
                  "fecha, forma y lugar de pago"):
        assert texto in faltantes, texto
    assert "falta información documental" in UI


def test_los_metadatos_documentales_no_alteran_importes_ni_conceptos():
    pedir = UI[UI.index("function pedirMetadatosRecibo("):UI.index("function cuerpoReciboHistorico(")]
    for prohibido in ("importe", "bruto", "neto", "concepto"):
        assert prohibido not in pedir.lower(), prohibido


# --------------------------------------------------------------------------- #
# 4. Fotografía documental en las carpetas nuevas.
# --------------------------------------------------------------------------- #
def test_la_carpeta_nueva_guarda_la_identificacion_del_empleador():
    empresa = LIQUIDAR[LIQUIDAR.index('"empresa": {'):LIQUIDAR.index('"empleados": {}')]
    assert '"razon_social": empresa.razon_social' in empresa
    assert '"cuit": empresa.cuit' in empresa


def test_la_carpeta_nueva_guarda_la_ficha_documental_del_trabajador():
    bloque = LIQUIDAR[LIQUIDAR.index('"documental": {'):]
    bloque = bloque[:bloque.index('"cct": emp.cct_numero')]
    for campo in ("nombre", "apellido", "cuil", "legajo", "fecha_ingreso",
                  "categoria", "cct_numero", "modalidad_contrato", "lugar_trabajo"):
        assert f'"{campo}":' in bloque, campo


def test_la_ficha_documental_no_participa_del_calculo():
    # Va en el snapshot, no en los conceptos ni en las bases del motor.
    bloque = LIQUIDAR[LIQUIDAR.index('"documental": {'):]
    bloque = bloque[:bloque.index('"cct": emp.cct_numero')]
    for prohibido in ("importe", "base_calculo"):
        assert prohibido not in bloque
