"""Estructura de la reorganización de interfaz (rama mejora/interfaz-profesional).

Pruebas UI estáticas sobre el HTML servido. No tocan motor, fórmulas, migraciones
ni base de datos: solo verifican que la reorganización mantiene las funciones y
suma el tablero, la sección Empresas, el menú de 7 entradas y el flujo visual.
"""
from collections import Counter
import re

from main import create_app
from ui_page import HTML


def test_cada_control_tiene_una_funcion_existente_y_no_hay_funciones_duplicadas():
    manejadores = re.findall(r'on(?:click|change|input|blur)="([^"]+)"', HTML)
    llamadas = {
        nombre
        for manejador in manejadores
        for nombre in re.findall(r'(?:^|[;{])\s*([A-Za-z_$][\w$]*)\s*\(', manejador)
    }
    funciones = re.findall(r'(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(', HTML)
    faltantes = llamadas - set(funciones) - {"$"}
    duplicadas = [nombre for nombre, cantidad in Counter(funciones).items() if cantidad > 1]
    assert not faltantes
    assert not duplicadas


def test_menu_lateral_siete_entradas():
    for destino in ('seccionInicio', 'seccionEmpresas', 'seccionEstablecimientos',
                    'seccionEmpleados', 'seccionNovedades', 'seccionLiquidar',
                    'seccionHistorial'):
        assert f"irA('{destino}',this)" in HTML, destino
    assert 'Recibos e historial' in HTML


def test_tablero_inicio_con_kpis_y_accesos():
    assert 'id="seccionInicio"' in HTML
    for kpi in ('kpiEmpresa', 'kpiEmpleados', 'kpiEstablecimientos', 'kpiPendientes'):
        assert f'id="{kpi}"' in HTML, kpi
    assert 'Accesos rápidos' in HTML
    assert 'function cargarInicio' in HTML
    assert 'await cargarInicio();' in HTML


def test_seccion_empresas():
    assert 'id="seccionEmpresas"' in HTML
    assert 'id="tablaEmpresas"' in HTML
    assert 'function cargarEmpresasSeccion' in HTML


def test_flujo_visual_completo():
    for etapa in ('Cliente / grupo', 'Sociedad / CUIT', 'Establecimiento',
                  'Empleado', 'Novedades', 'Liquidación', 'Recibo'):
        assert etapa in HTML, etapa


def test_logo_visible_en_la_app():
    # El logo (SVG con su título accesible) sigue presente en cabecera y lateral.
    assert HTML.count('Logo Sueldo Claro') >= 2


def test_establecimientos_conserva_abm_ui():
    for fn in ('editarEstablecimiento', 'guardarEstablecimiento',
               'cambiarActivoEstablecimiento'):
        assert f'function {fn}' in HTML, fn
    assert 'id="verInactivosEst"' in HTML


def test_no_inventa_estado_confirmada():
    assert "'presentada','aceptada','pagada'" in HTML
    assert "'confirmada'" not in HTML


def test_funciones_existentes_intactas():
    # No se eliminaron flujos previos.
    for fn in ('function ingresar', 'function cambiarEmpresa', 'function cargarEmpleados',
               'function liquidar', 'function cargarNovedades', 'function crearEmpleado'):
        assert fn in HTML, fn
    rutas = create_app().openapi()["paths"]
    for r in ('/auth/login', '/empleados', '/establecimientos', '/liquidaciones', '/novedades'):
        assert r in rutas, r
