import json
import re
from pathlib import Path


RAIZ = Path(__file__).parents[2]
SQL = (RAIZ / "migrations" / "017_estructura_uocra_76_75.sql").read_text()


def _config(codigo: str) -> dict:
    patron = rf"\('76/75','{codigo}'.*?\n\s*'(\{{.*?\}})',"
    coincidencia = re.search(patron, SQL, re.DOTALL)
    assert coincidencia, f"No se encontro la configuracion de {codigo}"
    return json.loads(coincidencia.group(1))


def test_padron_tiene_las_cinco_categorias_y_modalidades_correctas():
    categorias = (
        "OFICIAL_ESPECIALIZADO", "OFICIAL", "MEDIO_OFICIAL", "AYUDANTE", "SERENO"
    )
    for codigo in categorias:
        assert f"('76/75','{codigo}'" in SQL
    modalidad = _config("MODALIDAD_CATEGORIA")
    assert len(modalidad["jornalizados"]) == 4
    assert modalidad["mensualizados"] == ["Sereno"]


def test_zonificacion_usa_domicilio_de_obra_y_cubre_cuatro_zonas():
    zona = _config("ZONIFICACION")
    assert zona["campo_determinante"] == "domicilio_laboral"
    assert set(zona["zonas"]) == {"A", "B", "C", "C_AUSTRAL"}
    assert zona["zonas"]["B"] == ["La Pampa", "Neuquen", "Rio Negro", "Chubut"]
    assert zona["zonas"]["C"] == ["Santa Cruz"]


def test_presentismo_es_quincenal_y_no_se_activa_sin_novedades():
    regla = _config("ASISTENCIA_PERFECTA")
    assert regla["porcentaje"] == 0.20
    assert regla["periodicidad"] == "quincenal"
    assert regla["no_automatizar_sin_novedades_quincenales"] is True
    assert "('76/75','ASISTENCIA_PERFECTA','presentismo'" in SQL
    assert "'52'" in SQL


def test_fondo_cese_respeta_ley_22250():
    fondo = _config("FONDO_CESE_LABORAL")
    assert fondo["tramos"] == [
        {"desde_mes": 1, "hasta_mes": 12, "porcentaje": 0.12},
        {"desde_mes": 13, "hasta_mes": None, "porcentaje": 0.08},
    ]
    assert fondo["vencimiento"] == "primeros_15_dias_del_mes_siguiente"
    assert fondo["base"]["excluye"] == ["SAC"]


def test_migracion_no_toca_importes_ni_motor():
    assert "escala_salarial" not in SQL
    assert "parametro_legal" not in SQL
    assert "UPDATE public.cct_categoria" in SQL
    assert "ON CONFLICT (cct_numero,codigo,version) DO UPDATE" in SQL
