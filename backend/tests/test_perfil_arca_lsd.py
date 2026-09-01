from decimal import Decimal

import pytest

from infrastructure.lsd.perfil_arca import construir_atributos_suss, faltantes_perfil


def perfil_completo():
    return {
        "tipo_empleador": "1",
        "tipo_operacion": "0",
        "situacion_revista": "01",
        "condicion": "01",
        "actividad": "049",
        "modalidad_contratacion": "008",
        "siniestrado": "00",
        "localidad": "01",
        "codigo_obra_social": "123456",
        "dias_trabajados": 30,
        "horas_trabajadas": 176,
        "scvo": True,
        "aporte_adicional_ss_pct": Decimal("1.25"),
        "aporte_adicional_os": Decimal("123.45"),
    }


def test_atributos_suss_tienen_147_posiciones_oficiales():
    attrs = construir_atributos_suss(
        perfil_completo(), conyuge=True, hijos=2, tiene_cct=True,
    )
    assert len(attrs) == 147
    assert attrs[0:1] == "1"       # cónyuge, posición 14
    assert attrs[1:3] == "02"      # hijos, posiciones 15-16
    assert attrs[3:4] == "1"       # CCT, posición 17
    assert attrs[8:10] == "01"     # situación, posiciones 22-23
    assert attrs[12:15] == "049"   # actividad, posiciones 26-28
    assert attrs[39:44] == "00125" # aporte adicional, posiciones 53-57
    assert attrs[49:55] == "123456"
    assert attrs[57:72] == "000000000012345"


def test_no_completa_codigos_por_defecto():
    faltantes = faltantes_perfil({})
    assert "actividad" in faltantes
    assert "modalidad_contratacion" in faltantes
    with pytest.raises(ValueError, match="Faltan datos registrales"):
        construir_atributos_suss({})


def test_codigo_de_longitud_incorrecta_bloquea():
    p = perfil_completo()
    p["actividad"] = "49"
    with pytest.raises(ValueError, match="actividad"):
        construir_atributos_suss(p)
