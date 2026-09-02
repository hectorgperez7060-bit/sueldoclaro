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
    assert "1, 50" in sql  # código técnico <= 60 caracteres aun con categorías largas


def test_api_expone_tablero_separado_por_periodo():
    rutas = {r.path for r in router.routes}
    assert "/convenios/gestor-normativo" in rutas


def test_ui_muestra_gestor_y_separacion_conceptual():
    assert "Convenios y escalas" in HTML
    assert "Estructura estable" in HTML
    assert "Valores del período" in HTML
    assert "cargarGestorNormativo" in HTML
    assert "/convenios/gestor-normativo?periodo=" in HTML


def test_tablero_distingue_escalas_fatfa_publicadas_de_verificadas():
    codigo = (RAIZ / "src" / "api" / "routes" / "convenios.py").read_text()
    assert '"escalas_publicadas": esc_publicadas' in codigo
    assert "escalas_provisorias_publicadas" in codigo
    assert "Política GENERAL" in codigo
    assert 'cct.numero == "659/13"' not in codigo
    assert "confirmación expresa" in codigo


def test_ui_informa_publicadas_sin_llamarlas_verificadas():
    assert "escalas verificadas" in HTML
    assert "escalas_publicadas" in HTML
