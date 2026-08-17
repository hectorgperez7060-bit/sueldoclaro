from decimal import Decimal

import pytest
from pydantic import ValidationError

from api.routes.liquidaciones import _totales
from application.dto.schemas import AjusteManualLiquidacionIn


def test_totales_ajuste_manual_separan_aportes_patronales():
    conceptos = [
        {"tipo": "remunerativo", "importe": "100000.005"},
        {"tipo": "no_remunerativo", "importe": "20000"},
        {"tipo": "deduccion", "importe": "15000.004"},
        {"tipo": "contribucion", "importe": "18000"},
    ]

    assert _totales(conceptos) == (
        Decimal("120000.01"),
        Decimal("15000.00"),
        Decimal("105000.01"),
    )


def test_ajuste_manual_exige_motivo_y_un_concepto():
    with pytest.raises(ValidationError):
        AjusteManualLiquidacionIn(motivo="no", conceptos=[])


def test_ajuste_manual_acepta_eliminar_aporte_sindical():
    ajuste = AjusteManualLiquidacionIn(
        motivo="Trabajadora fuera de convenio",
        conceptos=[{
            "codigo": "SUELDO_MANUAL",
            "descripcion": "Sueldo pactado",
            "tipo": "remunerativo",
            "importe": "900000",
        }],
    )

    assert ajuste.conceptos[0].importe == Decimal("900000")
    assert all(c.tipo != "deduccion" for c in ajuste.conceptos)
