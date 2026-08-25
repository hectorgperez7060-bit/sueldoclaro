from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.parametros import EscalaSalarial
from domain.payroll_engine.uocra import HechosQuincenalesUocra, calcular_base_quincenal
from domain.value_objects.dinero import Dinero


ROOT = Path(__file__).resolve().parents[2]
SQL_ESCALAS = (ROOT / "migrations/019_uocra_escalas_y_fuentes.sql").read_text(encoding="utf-8")
SQL_HABILITA = (ROOT / "migrations/027_habilitar_motor_productivo_uocra.sql").read_text(encoding="utf-8")


def _escala(categoria: str, zona: str, total: str, puro: str, unidad: str):
    return EscalaSalarial(
        "76/75", categoria, Dinero.de(total), date(2026, 8, 1), date(2026, 8, 31),
        True, "Anexo I UOCRA", zona=zona, unidad_escala=unidad,
        basico_puro=Dinero.de(puro), adicional_zona=Dinero.de(Decimal(total)-Decimal(puro)),
        habilitada_liquidacion=True,
    )


@pytest.mark.parametrize("categoria,zona,puro,total", [
    ("Oficial Especializado", "A", "7420", "7420"),
    ("Oficial Especializado", "B", "7420", "8237"),
    ("Oficial Especializado", "C", "7420", "11392"),
    ("Oficial Especializado", "C_AUSTRAL", "7420", "14841"),
    ("Oficial", "A", "6348", "6348"), ("Oficial", "B", "6348", "7049"),
    ("Oficial", "C", "6348", "10680"), ("Oficial", "C_AUSTRAL", "6348", "12695"),
    ("Medio Oficial", "A", "5866", "5866"), ("Medio Oficial", "B", "5866", "6502"),
    ("Medio Oficial", "C", "5866", "10306"), ("Medio Oficial", "C_AUSTRAL", "5866", "11732"),
    ("Ayudante", "A", "5399", "5399"), ("Ayudante", "B", "5399", "6020"),
    ("Ayudante", "C", "5399", "10007"), ("Ayudante", "C_AUSTRAL", "5399", "10798"),
])
def test_matriz_horaria_agosto_y_asistencia_sobre_basico_puro(categoria, zona, puro, total):
    literal = f"'{categoria}','{zona}',{puro},"
    assert literal in SQL_ESCALAS
    r = calcular_base_quincenal(
        _escala(categoria, zona, total, puro, "HORA"),
        HechosQuincenalesUocra(Decimal("80"), Decimal("80"), True, True),
    )
    assert r.basico_total.monto == Decimal(total) * 160
    assert r.asistencia_total.monto == (Decimal(puro) * 160 * Decimal("0.20")).quantize(Decimal("0.01"))


@pytest.mark.parametrize("zona,puro,total", [
    ("A", "980858", "980858"), ("B", "980858", "1092719"),
    ("C", "980858", "1639782"), ("C_AUSTRAL", "980858", "1961716"),
])
def test_sereno_mensual_agosto_en_las_cuatro_zonas(zona, puro, total):
    r = calcular_base_quincenal(
        _escala("Sereno", zona, total, puro, "MENSUAL"),
        HechosQuincenalesUocra(None, None, True, True),
    )
    assert r.basico_total.monto == Decimal(total)
    assert r.asistencia_total.monto == (Decimal(puro) * Decimal("0.20")).quantize(Decimal("0.01"))


def test_habilitacion_aborta_si_falta_una_de_las_20_escalas():
    assert "IF cantidad <> 20" in SQL_HABILITA
    assert "RAISE EXCEPTION 'UOCRA %: matriz verificada incompleta" in SQL_HABILITA
    assert "UPDATE public.escala_salarial" in SQL_HABILITA
    assert "SET habilitada_liquidacion=true" in SQL_HABILITA


def test_habilitacion_exige_reglas_y_aportes_versionados():
    assert "IF cantidad < 9" in SQL_HABILITA
    assert "APORTE_SOLIDARIO_UOCRA_76/75" in SQL_HABILITA
    assert "CONTRIB_EMP_UOCRA_76/75" in SQL_HABILITA
    assert "2026.08-productivo-v1" in SQL_HABILITA


def test_no_existe_atajo_de_vista_previa_en_liquidacion():
    codigo = (ROOT / "src/application/use_cases/liquidar_periodo.py").read_text(encoding="utf-8")
    assert "replace(escala" not in codigo
    assert "armar_recibo_uocra(" in codigo
    assert "vista_previa_uocra" not in codigo
