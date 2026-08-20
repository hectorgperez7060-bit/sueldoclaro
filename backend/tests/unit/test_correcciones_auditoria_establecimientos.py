from pathlib import Path


def test_migracion_correctiva_otorga_permisos_al_rol_aplicacion():
    sql = (Path(__file__).parents[2] / "migrations" / "009_grant_establecimientos.sql").read_text()
    assert "GRANT SELECT, INSERT, UPDATE, DELETE ON establecimiento TO sueldoclaro" in sql
    assert "empleado_establecimiento_historial TO sueldoclaro" in sql


def test_api_rechaza_nuevas_asignaciones_a_establecimientos_inactivos():
    ruta = Path(__file__).parents[2] / "src" / "api" / "routes" / "empleados.py"
    codigo = ruta.read_text()
    assert codigo.count('"El establecimiento está inactivo"') == 2
    assert "establecimiento.id != establecimiento_actual_id" in codigo


def test_fixture_integracion_usa_codigo_arca_de_forma_pago():
    ruta = Path(__file__).parents[1] / "integration" / "test_isolation.py"
    assert '"forma_pago": "1"' in ruta.read_text()
