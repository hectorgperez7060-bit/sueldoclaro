from pathlib import Path

from api.routes.convenios import router
from ui_page import HTML


RAIZ = Path(__file__).parents[2]


def test_migracion_separa_estructura_de_valores_temporales():
    sql = (RAIZ / "migrations" / "011_gestor_normativo_cct.sql").read_text()
    assert "CREATE TABLE IF NOT EXISTS public.cct_categoria" in sql
    assert "CREATE TABLE IF NOT EXISTS public.cct_regla_estructural" in sql
    assert "escala_salarial" in sql
    assert "CREATE TABLE IF NOT EXISTS public.parametro_legal" not in sql
    assert "ON CONFLICT" in sql and "NOT EXISTS" in sql


def test_api_expone_tablero_separado_por_periodo():
    rutas = {r.path for r in router.routes}
    assert "/convenios/gestor-normativo" in rutas


def test_ui_muestra_gestor_y_separacion_conceptual():
    assert "Convenios y escalas" in HTML
    assert "Estructura estable" in HTML
    assert "Valores del período" in HTML
    assert "cargarGestorNormativo" in HTML
    assert "/convenios/gestor-normativo?periodo=" in HTML
