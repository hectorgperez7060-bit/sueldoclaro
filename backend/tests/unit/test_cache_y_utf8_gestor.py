from pathlib import Path

from ui_page import HTML


RAIZ = Path(__file__).parents[2]


def test_consultas_get_no_reutilizan_tablero_en_cache():
    assert "cache:metodo==='GET'?'no-store':'default'" in HTML


def test_reparacion_utf8_es_ascii_safe():
    sql = (RAIZ / "migrations" / "014_reparar_utf8_ambitos.sql").read_text()
    assert "U&'Cl\\00EDnicas" in sql
    assert "internaci\\00F3n" in sql
    assert sql.isascii()
