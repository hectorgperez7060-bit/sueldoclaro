from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/051_completar_adef_414_05_agosto_2026.sql").read_text(
    encoding="utf-8"
)


def test_migracion_adef_carga_las_seis_categorias_oficiales():
    categorias = (
        "Categoría Inicial A",
        "Categoría Inicial B",
        "Cajero, Perfumería y Administrativo",
        "Empleado de Farmacia",
        "Empleado Especializado de Farmacia",
        "Farmacéutico",
    )
    for categoria in categorias:
        assert categoria in SQL
    assert "escalas_habilitadas <> 6" in SQL


def test_migracion_adef_conserva_basicos_julio_por_ultraactividad():
    for valor in (
        "1341694.15", "1435611.36", "1486864.61",
        "1538116.45", "1828730.75", "1999675.61",
    ):
        assert valor in SQL
    assert "ultraactividad CCT 414/05 art. 2" in SQL


def test_migracion_adef_no_prorroga_asignaciones_unicas():
    assert "asignaciones \"por única vez\" finalizan en julio" in SQL
    assert "'414/05','FARMACIA_NR" not in SQL
