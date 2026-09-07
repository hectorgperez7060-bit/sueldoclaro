"""La cuota de ART sale del contrato, no de una cuenta a mano del empleador.

El contrato trae alícuota y suma fija, y las dos ya se cargan en el
establecimiento. Pedirle además el importe mensual por persona al imprimir el
recibo es pedirle que multiplique a ojo justo el número que define el costo
laboral.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal as D

import pytest

from domain.entities.art import ContratoArt, calcular_cuota_art


AGOSTO = date(2026, 8, 31)


def _contrato(**cambios):
    base = dict(
        nombre="Provincia ART", alicuota_pct=D("1.443"), suma_fija=D("0"),
        vigencia_desde=date(2026, 1, 1), vigencia_hasta=None, comprobante="POL-1",
    )
    base.update(cambios)
    return ContratoArt(**base)


def test_alicuota_sobre_la_remuneracion():
    cuota = calcular_cuota_art(_contrato(), D("1495872.00"), AGOSTO)
    # 1,443% de 1.495.872 = 21.585,43
    assert cuota.importe == D("21585.43")
    assert "Provincia ART" in cuota.descripcion


def test_suma_fija_por_trabajador_se_agrega():
    cuota = calcular_cuota_art(_contrato(suma_fija=D("1200")), D("1495872.00"), AGOSTO)
    assert cuota.importe == D("22785.43")
    assert "suma fija" in cuota.detalle


def test_sin_contrato_no_se_estima_nada():
    assert calcular_cuota_art(None, D("1495872.00"), AGOSTO) is None


def test_sin_alicuota_no_se_estima_nada():
    """Con suma fija sola no alcanza: la cuota necesita la alícuota del contrato."""
    assert calcular_cuota_art(
        _contrato(alicuota_pct=None, suma_fija=D("1200")), D("1495872.00"), AGOSTO
    ) is None


def test_un_contrato_vencido_no_cubre_el_periodo():
    vencido = _contrato(vigencia_hasta=date(2026, 7, 31))
    assert calcular_cuota_art(vencido, D("1495872.00"), AGOSTO) is None


def test_un_contrato_que_empieza_despues_tampoco():
    futuro = _contrato(vigencia_desde=date(2026, 9, 1))
    assert calcular_cuota_art(futuro, D("1495872.00"), AGOSTO) is None


def test_una_alicuota_negativa_se_rechaza():
    with pytest.raises(ValueError, match="negativa"):
        calcular_cuota_art(_contrato(alicuota_pct=D("-1")), D("1000"), AGOSTO)
