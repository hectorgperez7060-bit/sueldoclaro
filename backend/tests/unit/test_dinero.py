"""Reglas monetarias: Decimal siempre, ROUND_HALF_UP, prohibido float."""
from decimal import Decimal

import pytest

from domain.value_objects.dinero import Dinero


def test_redondeo_half_up():
    assert Dinero(Decimal("0.125")).redondear().monto == Decimal("0.13")
    assert Dinero(Decimal("0.124")).redondear().monto == Decimal("0.12")
    assert Dinero(Decimal("2.005")).redondear().monto == Decimal("2.01")


def test_precision_intermedia_no_se_redondea():
    # multiplicar mantiene precisión completa hasta redondear()
    parcial = Dinero(Decimal("100.005")).multiplicar(Decimal("3"))
    assert parcial.monto == Decimal("300.015")
    assert parcial.redondear().monto == Decimal("300.02")  # 300.015 -> half up


def test_porcentaje():
    base = Dinero(Decimal("568750.00"))
    assert base.porcentaje(Decimal("0.11")).redondear().monto == Decimal("62562.50")


def test_prohibido_float():
    base = Dinero(Decimal("100"))
    with pytest.raises(TypeError):
        base.multiplicar(1.5)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        base.porcentaje(0.11)  # type: ignore[arg-type]


def test_minimo_para_tope_sipa():
    base = Dinero(Decimal("10000000"))
    tope = Dinero(Decimal("9000000"))
    assert Dinero.minimo(base, tope).monto == Decimal("9000000")
