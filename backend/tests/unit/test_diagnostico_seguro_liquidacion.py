from pathlib import Path


FUENTE = (Path(__file__).parents[2] / "src" / "api" / "routes" /
          "liquidaciones.py").read_text()


def test_clasifica_errores_sin_incluir_el_mensaje_original():
    assert '"MultipleResultsFound": "Hay registros normativos duplicados' in FUENTE
    assert 'return f"{mensaje} (diagnóstico: {codigo})"' in FUENTE
    assert "Falta el campo interno" in FUENTE
    assert "coincidencia.group(1)" in FUENTE


def test_la_ruta_convierte_el_fallo_en_respuesta_visible():
    assert "except Exception as exc:" in FUENTE
    assert "_diagnostico_seguro(exc)" in FUENTE
    assert "logger.exception" in FUENTE
