from pathlib import Path


SQL = (Path(__file__).parents[2] / "migrations" / "038_reglas_estructurales_uthgra_389_04.sql").read_text()


def test_ambito_actual_excluye_tucuman_y_no_inventa_importes_mensuales():
    assert '"territorio":"ARGENTINA","exclusiones":["TUCUMAN"]' in SQL
    assert "Acuerdo UTHGRA-FEHGRA 24/07/2026" in SQL
    assert "INSERT INTO public.escala_salarial" not in SQL
    assert "INSERT INTO public.parametro_legal" not in SQL


def test_reglas_economicas_permanentes_quedan_trazadas():
    for codigo in (
        "BASE_ADICIONALES", "ANTIGUEDAD_ESCALONADA", "ALIMENTACION",
        "ASISTENCIA_PERFECTA", "COMPLEMENTO_SERVICIO", "ZONA_FRIA",
        "FALLECIMIENTO_SEPELIO", "CUOTA_SINDICAL_AFILIADO",
    ):
        assert f"'{codigo}'" in SQL
    assert '"aporte_trabajador_pct":0.01' in SQL
    assert '"contribucion_empleador_pct":0.01' in SQL


def test_encuadramiento_exige_tarea_y_clase_del_establecimiento():
    assert '"entradas_obligatorias":["nivel_profesional","clase_establecimiento"]' in SQL
    assert '"bloquea_sin_tarea":true' in SQL
    assert '"bloquea_sin_clasificacion":true' in SQL