from pathlib import Path


SQL = (Path(__file__).parents[2] / "migrations" / "037_adef_414_05_escala_completa_julio_2026.sql").read_text()


def test_incorpora_las_seis_categorias_adef_sin_estimar():
    categorias = (
        "Categoría Inicial A",
        "Categoría Inicial B",
        "Cajero, Perfumería y Administrativo",
        "Empleado de Farmacia",
        "Empleado Especializado de Farmacia",
        "Farmacéutico",
    )
    assert all(categoria in SQL for categoria in categorias)
    assert "1341694.15" in SQL
    assert "1435611.36" in SQL
    assert "1486864.61" in SQL
    assert "1538116.45" in SQL
    assert "1828730.75" in SQL
    assert "1999675.61" in SQL


def test_sumas_no_remunerativas_son_especificas_por_categoria():
    codigos = {
        parte.split("'", 1)[0]
        for parte in SQL.split("'FARMACIA_NR_")[1:]
    }
    assert len(codigos) == 6
    for importe in ("39692.42", "42469.57", "43986.02", "45586.01", "54100.54", "59156.96"):
        assert importe in SQL
    assert "'categoria', d.categoria" in SQL


def test_no_inventa_escala_adef_para_agosto():
    assert "No crea valores para agosto" in SQL
    assert "DATE '2026-08-01'" not in SQL
