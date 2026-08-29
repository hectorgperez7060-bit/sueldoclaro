from datetime import date
from decimal import Decimal
from pathlib import Path


def test_migracion_desactiva_la_retencion_sin_borrar_historial():
    sql = (
        Path(__file__).parents[2]
        / "migrations" / "035_desactivar_aporte_modernizacion_sin_respaldo.sql"
    ).read_text(encoding="utf-8")

    assert "SET valor = 0" in sql
    assert "DELETE FROM" not in sql.upper()
    assert "art. 131" in sql


def test_motor_omite_el_concepto_cuando_la_tasa_es_cero():
    source = (
        Path(__file__).parents[2]
        / "src" / "domain" / "payroll_engine" / "engine.py"
    ).read_text(encoding="utf-8")

    assert 'if porcentaje == Decimal("0"):' in source
    assert "if aporte_modernizacion is not None:" in source
