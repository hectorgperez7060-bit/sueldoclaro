"""Regla GENERAL de escala verificada + migración de datos 414/05.

- La lógica de bloqueo/provisorio es general (cualquier CCT/categoría/período).
- Los importes viven en la migración (tablas de escalas/parámetros), no en el
  código del dominio ni del motor.
"""
import re
from datetime import date
from decimal import Decimal as D
from pathlib import Path

from domain.entities.parametros import EscalaSalarial
from domain.entities.escala_verificada import (
    MENSAJE_SIN_ESCALA, NOTA_PROVISORIA, evaluar_escala,
)
from domain.entities.farmacia_414_05 import CATEGORIAS_FARMACIA
from domain.value_objects.dinero import Dinero

RAIZ = Path(__file__).parents[2]
MIG_010 = RAIZ / "migrations" / "010_escala_verificada_farmacia_414_05.sql"


def _escala(basico, desde, hasta, verificada=True):
    return EscalaSalarial("414/05", "Empleado Especializado de Farmacia",
                          Dinero(D(basico)), desde, hasta, verificada, "fuente")


# ------------------------------------------------------------- regla general
def test_vigente_se_liquida():
    ev = evaluar_escala(_escala("100", date(2026, 7, 1), date(2026, 7, 31)), None)
    assert ev.estado == "vigente" and ev.puede_liquidar is True
    assert ev.provisorio is False and ev.escala is not None


def test_sin_vigente_con_previa_es_provisoria_y_pide_confirmacion():
    previa = _escala("100", date(2026, 7, 1), date(2026, 7, 31))
    ev = evaluar_escala(None, previa, confirmado=False)
    assert ev.estado == "provisoria" and ev.provisorio is True
    assert ev.requiere_confirmacion is True and ev.puede_liquidar is False
    assert ev.nota == NOTA_PROVISORIA


def test_provisoria_confirmada_liquida_con_la_previa():
    previa = _escala("100", date(2026, 7, 1), date(2026, 7, 31))
    ev = evaluar_escala(None, previa, confirmado=True)
    assert ev.puede_liquidar is True and ev.escala is previa


def test_sin_vigente_ni_previa_bloquea_con_mensaje():
    ev = evaluar_escala(None, None)
    assert ev.estado == "bloqueada" and ev.puede_liquidar is False
    assert ev.motivo == "Sin escala salarial verificada para el período"
    assert MENSAJE_SIN_ESCALA == "Sin escala salarial verificada para el período"


def test_regla_no_esta_escrita_para_414_05():
    # La regla general no menciona ningún convenio específico.
    fuente = (RAIZ / "src" / "domain" / "entities" / "escala_verificada.py").read_text()
    assert "414" not in fuente and "farmacia" not in fuente.lower()


# ------------------------------------------------------------- catálogo
def test_catalogo_seis_categorias_oficiales():
    assert len(CATEGORIAS_FARMACIA) == 6
    assert "Empleado Especializado de Farmacia" in CATEGORIAS_FARMACIA


# -------------------------------------------- importes SOLO en la migración
def test_importes_no_estan_en_dominio_ni_motor():
    for sub in ("domain",):
        base = RAIZ / "src" / sub
        for archivo in base.rglob("*.py"):
            texto = archivo.read_text()
            assert "1828730.75" not in texto, f"importe en {archivo}"
            assert "54100.54" not in texto, f"importe en {archivo}"
    motor = RAIZ / "src" / "domain" / "payroll_engine"
    for archivo in motor.rglob("*.py"):
        assert "1828730" not in archivo.read_text()
    # No debe existir el viejo módulo con importes.
    assert not (RAIZ / "src" / "domain" / "entities" / "farmacia_escala_414_05.py").exists()


def test_migracion_010_tiene_importes_verificados_e_idempotente():
    sql = MIG_010.read_text()
    assert "1828730.75" in sql and "54100.54" in sql
    assert "Empleado Especializado de Farmacia" in sql
    assert "escala_salarial" in sql and "parametro_legal" in sql
    # Idempotencia (patrón del repo).
    assert "IF NOT FOUND" in sql and "WHERE NOT EXISTS" in sql
    # NR acotado a julio 2026 (no se traslada a agosto).
    assert "DATE '2026-07-31'" in sql
    assert "'no_rem'" in sql


def test_migracion_010_solo_carga_especializado():
    sql = MIG_010.read_text()
    otras = [
        "Categoría Inicial A", "Categoría Inicial B",
        "Cajero, Perfumería y Administrativo", "Empleado de Farmacia", "Farmacéutico",
    ]
    for categoria in otras:
        assert categoria not in sql, f"no debe cargar {categoria}"
