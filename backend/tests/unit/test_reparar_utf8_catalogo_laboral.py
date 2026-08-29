from pathlib import Path


SQL = (Path(__file__).parents[2] / "migrations" /
       "034_reparar_utf8_catalogo_laboral.sql").read_text()


def test_repara_catalogo_escalas_y_legajos_sin_tocar_importes():
    for tabla in (
        "public.cct_categoria", "public.escala_salarial", "public.empleado",
        "public.parametro_legal", "public.cct_regla_estructural",
    ):
        assert tabla in SQL
    assert "SET basico" not in SQL
    assert "SET valor" not in SQL


def test_incluye_los_errores_visibles_reportados():
    for roto, correcto in (
        ("Ã­a", "ía"), ("Ã©", "é"), ("Ã¡", "á"), ("Ãº", "ú"), ("Ã±", "ñ"),
    ):
        assert roto in SQL
        assert correcto in SQL
