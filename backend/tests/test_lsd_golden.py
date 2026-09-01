"""Contrato de ancho fijo ARCA vigente desde 15/05/2026."""
import os
import sys
from decimal import Decimal

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from infrastructure.lsd.generator import (
    ConceptoLSD, EmpleadorLSD, TrabajadorLSD, build_lsd, build_lsd_bytes,
    registro_01, registro_02, registro_03, registro_04,
)


def _trabajador():
    return TrabajadorLSD(
        cuil="27-24032052-0",
        legajo="138",
        dependencia_revista="Casa velatoria",
        forma_pago="3",
        cbu="0170099920000001234567",
        dias_tope=30,
        fecha_pago="20260904",
        fecha_rubrica="20260904",
        conceptos=[
            ConceptoLSD("SUELDO", Decimal("1184999.99"), "C", Decimal("1"), "M"),
            ConceptoLSD("JUBILAC", Decimal("130349.99"), "D", Decimal("11"), "%"),
        ],
        attrs_suss="0" * 147,
        remun_total=Decimal("1184999.99"),
        bases=[Decimal("1184999.99")] * 10 + [Decimal("0")] * 3,
    )


def test_registro_01_respeta_diseno_oficial():
    r = registro_01(EmpleadorLSD("30-69706631-0", "202608", nro_liq=1), 1)
    assert len(r) == 35
    assert r[0:2] == "01"
    assert r[2:13] == "30697066310"
    assert r[13:15] == "SJ"
    assert r[15:21] == "202608"
    assert r[21] == "M"
    assert r[22:27] == "00001"
    assert r[27:29] == "30"
    assert r[29:35] == "000001"


def test_registro_02_cbu_dias_fechas_y_forma_en_posicion_2026():
    r = registro_02(_trabajador())
    assert len(r) == 115
    assert r[73:95] == "0170099920000001234567"
    assert r[95:98] == "030"
    assert r[98:106] == "20260904"
    assert r[106:114] == "20260904"
    assert r[114] == "3"


def test_registro_03_codigo_cantidad_unidad_importe_signo_y_ajuste():
    c = ConceptoLSD(
        "SUELDO", Decimal("1184999.99"), "C", Decimal("1"), "M", "202607"
    )
    r = registro_03("27240320520", c)
    assert len(r) == 51
    assert r[13:23] == "SUELDO    "
    assert r[23:28] == "00100"
    assert r[28] == "M"
    assert r[29:44] == "000000118499999"
    assert r[44] == "C"
    assert r[45:51] == "202607"


def test_registro_04_y_archivo_ansi_crlf():
    t = _trabajador()
    assert len(registro_04(t)) == 370
    emp = EmpleadorLSD("30697066310", "202608")
    texto = build_lsd(emp, [t])
    lineas = texto.splitlines()
    assert [len(x) for x in lineas] == [35, 115, 51, 51, 370]
    assert texto.endswith("\r\n")
    assert build_lsd_bytes(emp, [t]) == texto.encode("latin-1")


def test_no_genera_archivo_incompleto_silenciosamente():
    t = _trabajador()
    t.cbu = ""
    try:
        registro_02(t)
    except ValueError as exc:
        assert "CBU de 22 digitos" in str(exc)
    else:
        raise AssertionError("debió bloquear una acreditación sin CBU")
