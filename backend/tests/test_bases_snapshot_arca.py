from decimal import Decimal

from infrastructure.lsd.bases_snapshot import (
    calcular_bases_snapshot, codigo_empleador, codigo_tipo_arca,
)


def test_bases_funeraria_excluyen_suma_no_remunerativa_y_contribuciones():
    conceptos = [
        {"codigo": "BASICO", "tipo": "remunerativo", "importe": "1000000.00"},
        {"codigo": "ANTIGUEDAD", "tipo": "remunerativo", "importe": "100000.00"},
        {
            "codigo": "NO_REM_2026_08_749_A_2_ADM_POLIVALENTE_A",
            "tipo": "no_remunerativo", "importe": "20000.00",
        },
        {"codigo": "CONTRIB_JUBILACION", "tipo": "contribucion", "importe": "198000.00"},
        {"codigo": "APORTE_JUBILACION", "tipo": "deduccion", "importe": "121000.00"},
    ]
    bases, traza = calcular_bases_snapshot(
        conceptos, "2026-08",
        {"detraccion_confirmada": True, "detraccion_ley_27541": "17509.20"},
    )

    assert bases == [
        Decimal("1100000"), Decimal("1100000"), Decimal("1100000"),
        Decimal("1100000"), Decimal("1100000"), Decimal("0"), Decimal("0"),
        Decimal("1100000"), Decimal("1100000"), Decimal("1082490.80"),
    ]
    assert traza["fuente_tope"].startswith("ANSES Resolución 232/2026")


def test_codigos_soecra_son_estables_y_entran_en_diez_posiciones():
    assert codigo_empleador("NO_REM_2026_08_749_A_2_ADM_POLIVALENTE_A") == "NR749AGO"
    assert codigo_tipo_arca("NO_REM_2026_08_749_A_2_ADM_POLIVALENTE_A") == "540000"
    assert codigo_empleador("CUOTA_SINDICAL_SOECRA_761/19") == "CUOTASOE"
    assert codigo_tipo_arca("CUOTA_SINDICAL_SOECRA_761/19") == "820000"


def test_sin_confirmar_detraccion_no_publica_bases():
    try:
        calcular_bases_snapshot(
            [{"codigo": "BASICO", "tipo": "remunerativo", "importe": "1000"}],
            "2026-08", {},
        )
    except ValueError as exc:
        assert "detracción" in str(exc)
    else:
        raise AssertionError("Debió bloquear una base 10 no confirmada")
