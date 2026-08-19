from pathlib import Path

from main import create_app
from ui_page import HTML


def test_api_registra_establecimientos():
    rutas = create_app().openapi()["paths"]
    assert "/establecimientos" in rutas
    assert "/establecimientos/{establecimiento_id}" in rutas


def test_ui_permite_grupos_sociedades_y_domicilios():
    assert 'id="nuevaEmpresaGrupo"' in HTML
    assert 'id="seccionEstablecimientos"' in HTML
    assert 'id="eEstablecimiento"' in HTML
    assert 'id="eLugarDesde"' in HTML


def test_migracion_aplica_rls_a_lugares_e_historial():
    sql = (Path(__file__).parents[2] / "migrations" / "008_establecimientos_y_grupos.sql").read_text()
    assert "CREATE TABLE IF NOT EXISTS establecimiento" in sql
    assert "CREATE TABLE IF NOT EXISTS empleado_establecimiento_historial" in sql
    assert "ALTER TABLE establecimiento FORCE ROW LEVEL SECURITY" in sql
    assert "ALTER TABLE empleado_establecimiento_historial FORCE ROW LEVEL SECURITY" in sql
    assert "grupo_cliente" in sql
