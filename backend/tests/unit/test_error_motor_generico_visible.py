from pathlib import Path


FUENTE = (Path(__file__).parents[2] / "src" / "application" / "use_cases" /
          "liquidar_periodo.py").read_text()


def test_motor_generico_convierte_errores_de_datos_en_bloqueo_visible():
    inicio = FUENTE.index("else:\n                    try:\n                        motor = MotorLiquidacion")
    fin = FUENTE.index("                conceptos = [", inicio)
    bloque = FUENTE[inicio:fin]
    assert "except (KeyError, TypeError, ValueError) as exc:" in bloque
    assert '"motivo": f"Liquidación bloqueada: {exc}"' in bloque
    assert "continue" in bloque
