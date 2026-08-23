from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.parametros import EscalaSalarial
from domain.payroll_engine.uocra import calcular_adicionales_tarea_uocra
from domain.value_objects.dinero import Dinero


ROOT = Path(__file__).resolve().parents[2]


def escala():
    return EscalaSalarial(
        "76/75", "Oficial", Dinero.de("1200"), date(2026, 8, 1), date(2026, 8, 31),
        True, "Anexo I", False, "B", "HORA", False,
        "PUBLICADA_POR_PARTE_SIGNATARIA", Dinero.de("1000"), Dinero.de("200"),
    )


def test_hormigon_15_sobre_basico_puro_y_horas_efectivas():
    r = calcular_adicionales_tarea_uocra(escala(), Decimal("10"))[0]
    assert r.codigo == "ADIC_HORMIGON_ART56"
    assert r.base_horaria.monto == Decimal("1000.00")
    assert r.importe.monto == Decimal("1500.00")


@pytest.mark.parametrize("metros,porcentaje,importe", [
    ("4", "0.15", "1200.00"), ("25.99", "0.15", "1200.00"),
    ("26.01", "0.20", "1600.00"), ("40", "0.20", "1600.00"),
    ("40.01", "0.25", "2000.00"),
])
def test_altura_aplica_tramos_verificados(metros, porcentaje, importe):
    r = calcular_adicionales_tarea_uocra(
        escala(), horas_altura=Decimal("8"), altura_metros=Decimal(metros)
    )[0]
    assert r.porcentaje == Decimal(porcentaje)
    assert r.importe.monto == Decimal(importe)


def test_altura_26_exacto_bloquea_ambiguedad_del_texto():
    with pytest.raises(ValueError, match="superpone los tramos"):
        calcular_adicionales_tarea_uocra(
            escala(), horas_altura=Decimal("8"), altura_metros=Decimal("26")
        )


def test_no_inventa_tarifas_para_tunel_ni_martillo():
    ui = (ROOT / "src/ui_page.py").read_text()
    assert "Túneles y martillo neumático" in ui
    assert "sin tarifa independiente verificada" in ui


def test_migracion_registra_reglas_y_campos_auditables():
    sql = (ROOT / "migrations/025_adicionales_tarea_uocra.sql").read_text()
    assert "ADIC_HORMIGON_ART56" in sql and "ADIC_ALTURA_ART57" in sql
    assert "horas_hormigon_manual_uocra" in sql
    assert "altura_metros_uocra" in sql
