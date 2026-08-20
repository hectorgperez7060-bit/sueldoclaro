"""Correcciones pedidas por la revisión de Codex sobre mejora/interfaz-profesional.

Pruebas de estructura estáticas (mismo estilo que el resto de la suite). El
comportamiento en DOM real se verifica aparte con jsdom; acá se fija que la
lógica corregida esté presente en el HTML servido, para que no pueda regresar.
"""
from ui_page import HTML


def test_caso1_establecimiento_inactivo_en_select():
    # La opción se agrega siempre (ya no solo si activo) y las inactivas quedan
    # deshabilitadas e identificadas como "(Inactivo)".
    assert "if(!e.activo) o.disabled=true;" in HTML
    assert "(e.activo?'':' (Inactivo)')" in HTML
    # El select se arma con incluir_inactivos para tener el actual aunque esté inactivo.
    assert "incluir_inactivos=true" in HTML
    # Al editar, el establecimiento asignado se carga desde el empleado.
    assert "$('eEstablecimiento').value = e.establecimiento_id || '';" in HTML


def test_caso2_ira_marca_entrada_sin_boton():
    assert "if(!boton){ boton=[...document.querySelectorAll('.navegacion button')]" in HTML
    assert "getAttribute('onclick')" in HTML
    assert 'includes("irA(\'"+id+"\'")' in HTML


def test_caso3_esc_definida_y_usada():
    assert "function esc(t){" in HTML
    # Empresas: grupo y razón social escapados.
    assert "esc(e.grupo_cliente||'—')" in HTML
    assert "esc(e.razon_social||'')" in HTML
    # Establecimientos: nombre, domicilio, localidad, provincia, actividad escapados.
    assert "esc(e.nombre)" in HTML
    assert "esc(e.domicilio)" in HTML
    assert "esc(e.localidad||'')" in HTML
    assert "esc(e.provincia||'')" in HTML
    assert "esc(e.actividad||'')" in HTML


def test_no_se_tocaron_otras_tablas():
    # La tabla de empleados (ajena a este bloque) sigue sin esc(): no debe cambiarse todavía.
    assert "<td data-label=\"Empleado\">${e.apellido}, ${e.nombre}</td>" in HTML
