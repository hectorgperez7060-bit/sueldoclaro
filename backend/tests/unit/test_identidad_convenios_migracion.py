from pathlib import Path


def test_migracion_corrige_identidad_sin_tocar_empleados():
    sql = Path("backend/migrations/006_identidad_convenios_obra_social.sql").read_text()
    assert "'414/05'" in sql and "sindicato = 'ADEF'" in sql
    assert "'122/75'" in sql and "sindicato = 'FATSA'" in sql
    assert "UPDATE public.empleado" not in sql
