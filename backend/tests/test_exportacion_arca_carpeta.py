from decimal import Decimal
from pathlib import Path

import pytest

from infrastructure.lsd.bases_snapshot import (
    calcular_bases_snapshot, codigo_empleador, codigo_tipo_arca,
)


def conceptos_funeraria():
    return [
        {"codigo": "BASICO", "tipo": "REMUNERATIVO", "importe": "1000000.00"},
        {"codigo": "ANTIGUEDAD", "tipo": "REMUNERATIVO", "importe": "100000.00"},
        {
            "codigo": "NO_REM_2026_08_749_A_2_ADM_POLIVALENTE_A",
            "tipo": "NO_REMUNERATIVO", "importe": "180523.81",
        },
        {"codigo": "APORTE_JUBILACION", "tipo": "DESCUENTO", "importe": "121000.00"},
        {"codigo": "APORTE_LEY19032", "tipo": "DESCUENTO", "importe": "33000.00"},
        {"codigo": "APORTE_OBRA_SOCIAL", "tipo": "DESCUENTO", "importe": "33000.00"},
    ]


def test_bases_agosto_funeraria_excluyen_suma_no_remunerativa_de_seguridad_social():
    bases, traza = calcular_bases_snapshot(
        conceptos_funeraria(), "2026-08",
        {"detraccion_confirmada": True, "detraccion_ley_27541": "17509.20"},
    )
    assert len(bases) == 10
    assert bases[:5] == [Decimal("1100000.00")] * 5
    assert bases[5:7] == [Decimal("0"), Decimal("0")]
    assert bases[7:9] == [Decimal("1100000.00"), Decimal("1100000.00")]
    assert bases[9] == Decimal("1082490.80")
    assert traza["fuente_tope"].startswith("ANSES Resolución 232/2026")


def test_codigos_funeraria_son_estables_y_catalogados():
    codigo = "NO_REM_2026_08_749_A_2_ADM_POLIVALENTE_A"
    assert codigo_empleador(codigo) == "NR749AGO"
    assert codigo_tipo_arca(codigo) == "540000"


def test_sin_confirmar_detraccion_no_hay_bases():
    with pytest.raises(ValueError, match="detracción"):
        calcular_bases_snapshot(conceptos_funeraria(), "2026-08", {})


def test_periodo_sin_tope_oficial_no_se_estima():
    with pytest.raises(ValueError, match="topes oficiales"):
        calcular_bases_snapshot(
            conceptos_funeraria(), "2026-09",
            {"detraccion_confirmada": True, "detraccion_ley_27541": 0},
        )


def test_ruta_exportaciones_no_contiene_salto_literal_que_rompe_python():
    fuente = (
        Path(__file__).resolve().parents[1] / "src" / "api" / "routes" / "exportaciones.py"
    ).read_text(encoding="utf-8")
    assert 'upper()\\n' not in fuente
