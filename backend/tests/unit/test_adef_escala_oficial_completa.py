from pathlib import Path


SQL = (Path(__file__).parents[2] / "migrations" /
       "034_adef_414_05_escala_oficial_julio_vigente.sql").read_text()


def test_carga_los_seis_basicos_oficiales_adef():
    esperados = {
        "Categoría Inicial A": "1341694.15",
        "Categoría Inicial B": "1435611.36",
        "Cajero, Perfumería y Administrativo": "1486864.61",
        "Empleado de Farmacia": "1538116.45",
        "Empleado Especializado de Farmacia": "1828730.75",
        "Farmacéutico": "1999675.61",
    }
    for categoria, importe in esperados.items():
        assert f"('{categoria}', {importe}::numeric)" in SQL


def test_basicos_siguen_vigentes_y_el_no_remunerativo_termina_en_julio():
    assert "valid_to = NULL" in SQL
    assert "DATE '2026-07-31'" in SQL
    assert "impedir que el motor los copie a agosto" in SQL


def test_reemplaza_la_fila_provisoria_de_agosto():
    assert "valid_from = DATE '2026-08-01'" in SQL
    assert "provisoria = true" in SQL
    assert "fuente LIKE 'Provisorio:%'" in SQL


def test_registra_fuente_oficial_y_no_un_recibo_particular():
    assert "https://www.adef.org.ar/escala-salarial/escala-salarial-2026" in SQL
    assert "Recibo real de control" not in SQL
