from pathlib import Path


RAIZ = Path(__file__).parents[2]


def test_tablas_globales_son_legibles_pero_no_editables_por_la_app():
    sql = (RAIZ / "migrations" / "015_lectura_global_gestor_normativo.sql").read_text()
    assert "cct_categoria DISABLE ROW LEVEL SECURITY" in sql
    assert "cct_regla_estructural DISABLE ROW LEVEL SECURITY" in sql
    assert "REVOKE INSERT, UPDATE, DELETE, TRUNCATE" in sql
    assert "GRANT SELECT" in sql
    assert "GRANT INSERT" not in sql and "GRANT UPDATE" not in sql
