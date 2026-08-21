from pathlib import Path


RAIZ = Path(__file__).parents[2]
SQL = (RAIZ / "migrations" / "016_reglas_estructurales_comercio_sanidad.sql").read_text()


def test_migracion_solo_completa_el_padron_permanente():
    assert "INSERT INTO public.cct_regla_estructural" in SQL
    assert "escala_salarial" not in SQL
    assert "parametro_legal" not in SQL
    assert "UPDATE public.cct " not in SQL
    assert "ON CONFLICT (cct_numero,codigo,version) DO UPDATE" in SQL


def test_comercio_registra_reglas_base_verificadas():
    for codigo in ("ANTIGUEDAD", "PRESENTISMO", "JORNADA"):
        assert f"('130/75','{codigo}'" in SQL
    assert '"porcentaje_por_anio":0.01' in SQL
    assert '"divisor":12' in SQL
    assert '"completa_horas_semanales":48' in SQL


def test_sanidad_refleja_todo_el_catalogo_del_dominio():
    from domain.entities.sanidad_122_75 import REGLAS_ESTRUCTURALES_SANIDAD

    assert "('122/75','ANTIGUEDAD'" in SQL
    for regla in REGLAS_ESTRUCTURALES_SANIDAD:
        assert f"('122/75','{regla.codigo}'" in SQL
        assert f'"automatizable":{str(regla.automatizable).lower()}' in SQL


def test_reglas_conservan_fuente_y_estado_verificado():
    assert SQL.count("https://www.argentina.gob.ar/normativa/nacional/") >= 22
    assert SQL.count("true,1,true)") >= 23
