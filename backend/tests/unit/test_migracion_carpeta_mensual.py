from pathlib import Path


SQL = (
    Path(__file__).parents[2] / "migrations" / "002_carpeta_mensual.sql"
).read_text(encoding="utf-8")


def test_migracion_carpeta_es_acotada_y_transaccional():
    assert "BEGIN;" in SQL
    assert "COMMIT;" in SQL
    assert "CREATE TABLE public.carpeta_mensual" in SQL
    assert "CREATE TABLE contador_profesional" not in SQL
    assert "CREATE TABLE revision_profesional" not in SQL


def test_migracion_carpeta_aplica_rls_y_permiso_de_aplicacion():
    assert "ENABLE ROW LEVEL SECURITY" in SQL
    assert "FORCE ROW LEVEL SECURITY" in SQL
    assert "carpeta_mensual_tenant_isolation" in SQL
    assert "GRANT SELECT, INSERT, UPDATE, DELETE" in SQL
    assert "TO sueldoclaro" in SQL
