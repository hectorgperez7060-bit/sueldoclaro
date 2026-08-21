from pathlib import Path


RAIZ = Path(__file__).parents[2]


def test_reparacion_agrega_adef_y_reconstruye_categorias():
    sql = (RAIZ / "migrations" / "012_reparar_padron_normativo.sql").read_text()
    assert "'414/05', 'Empleados de Farmacia (ADEF)'" in sql
    assert "FROM public.escala_salarial" in sql
    assert sql.count("Empleado Especializado de Farmacia") == 1
    assert "ON CONFLICT" in sql and "NOT EXISTS" in sql


def test_tablero_tiene_respaldo_historico_sin_declararlo_completo():
    fuente = (RAIZ / "src" / "api" / "routes" / "convenios.py").read_text()
    assert "escalas_historicas" in fuente
    assert "estructura_registrada" in fuente
    assert '"registrada": estructura_registrada' in fuente
