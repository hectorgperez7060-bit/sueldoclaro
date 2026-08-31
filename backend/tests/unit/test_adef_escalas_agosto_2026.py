from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/051_adef_414_05_escalas_agosto_2026.sql").read_text(encoding="utf-8")

CATEGORIAS = (
    "Categoría Inicial A",
    "Categoría Inicial B",
    "Cajero, Perfumería y Administrativo",
    "Empleado de Farmacia",
    "Empleado Especializado de Farmacia",
    "Farmacéutico",
)


def test_migracion_carga_las_seis_categorias_en_julio_y_agosto():
    for categoria in CATEGORIAS:
        assert SQL.count(f"('{categoria}',") == 3
    assert "julio %, agosto provisorio %" in SQL


def test_agosto_es_ultraactivo_confirmable_y_no_arrastra_no_remunerativos():
    assert "DATE '2026-08-01', DATE '2026-08-31'" in SQL
    assert "true, 2, true, true" in SQL
    assert "requiere confirmación" in SQL
    assert "FARMACIA_NR_" not in SQL
