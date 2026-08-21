from pathlib import Path

from domain.entities.zonificacion_salarial import resolver_zona


RAIZ = Path(__file__).parents[2]
MIGRACION = (RAIZ / "migrations" / "018_zona_escala_salarial.sql").read_text()

ZONAS = {
    "zonas": {
        "A": ["CABA", "Buenos Aires", "Cordoba"],
        "B": ["La Pampa", "Neuquen", "Rio Negro", "Chubut"],
        "C": ["Santa Cruz"],
        "C_AUSTRAL": ["Tierra del Fuego"],
    }
}


def test_resuelve_provincia_normalizando_acentos_y_alias_caba():
    assert resolver_zona(ZONAS, "Neuquén") == "B"
    assert resolver_zona(ZONAS, "Ciudad Autónoma de Buenos Aires") == "A"
    assert resolver_zona(ZONAS, "Santa Cruz") == "C"


def test_no_inventa_zona_si_falta_o_no_esta_contemplada():
    assert resolver_zona(ZONAS, "") is None
    assert resolver_zona(ZONAS, "Provincia inexistente") is None


def test_migracion_agrega_dimension_sin_modificar_historicos():
    assert "ADD COLUMN IF NOT EXISTS zona varchar(20) NOT NULL DEFAULT ''" in MIGRACION
    assert "UPDATE public.escala_salarial" not in MIGRACION
    assert "ix_escala_cct_categoria_zona_vigencia" in MIGRACION


def test_tablero_muestra_categorias_por_cantidad_de_zonas():
    from ui_page import HTML

    codigo_api = (RAIZ / "src" / "api" / "routes" / "convenios.py").read_text()
    assert '"escalas_esperadas": escalas_esperadas' in codigo_api
    assert "periodo_actual.escalas_esperadas" in HTML
