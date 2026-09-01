"""Generador de interfaz Libro de Sueldos Digital (LSD) para ARCA.

Implementa el diseño oficial LSDiseInterfazLiquidacion 15052026:
registros 01, 02, 03 y 04 de ancho fijo. El resultado es texto ANSI
(latin-1), no un archivo binario.

El archivo sólo debe habilitarse cuando todos los códigos registrales y las
bases imponibles hayan sido informados y validados. ARCA realiza la validación
final y, luego de aceptar la liquidación, arma la DJ F.931.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, List, Optional


def _solo_digitos(valor: str) -> str:
    return "".join(ch for ch in (valor or "") if ch.isdigit())


def _num(valor: Any, largo: int) -> str:
    s = str(int(valor))
    if len(s) > largo:
        raise ValueError(f"numero {s} excede {largo} posiciones")
    return s.rjust(largo, "0")


def _decimal_implicito(valor: Any, enteros: int, decimales: int) -> str:
    d = Decimal(str(valor)).quantize(Decimal(1).scaleb(-decimales), ROUND_HALF_UP)
    if d < 0:
        raise ValueError("los importes y cantidades se informan positivos; use Debito/Credito")
    return _num(int(d * (10 ** decimales)), enteros + decimales)


def _centavos(monto: Any, largo: int = 15) -> str:
    return _decimal_implicito(monto, largo - 2, 2)


def _txt(valor: str, largo: int, *, truncar: bool = False) -> str:
    s = str(valor or "")
    try:
        s.encode("latin-1")
    except UnicodeEncodeError as exc:
        raise ValueError(f"texto no representable en ANSI: {s!r}") from exc
    if len(s) > largo:
        if not truncar:
            raise ValueError(f"texto {s!r} excede {largo} posiciones")
        s = s[:largo]
    return s.ljust(largo)


def _id_fiscal(valor: str, nombre: str) -> str:
    d = _solo_digitos(valor)
    if len(d) != 11:
        raise ValueError(f"{nombre} invalido: debe tener 11 digitos")
    return d


def _fecha(valor: str, *, obligatoria: bool = True) -> str:
    d = _solo_digitos(valor)
    if not d and not obligatoria:
        return " " * 8
    if len(d) != 8:
        raise ValueError("la fecha debe tener formato AAAAMMDD")
    return d


@dataclass
class ConceptoLSD:
    codigo: str
    importe: Decimal
    signo: str
    cantidad: Decimal = Decimal("0")
    unidad: str = "$"
    periodo_ajuste: str = ""


@dataclass
class TrabajadorLSD:
    cuil: str
    legajo: str = ""
    dependencia_revista: str = ""
    cbu: str = ""
    dias_tope: int = 30
    fecha_pago: str = ""
    fecha_rubrica: str = ""
    forma_pago: str = "1"
    conceptos: List[ConceptoLSD] = field(default_factory=list)
    attrs_suss: str = ""
    remun_total: Decimal = Decimal("0")
    bases: List[Decimal] = field(default_factory=list)
    resultado_liquidacion: Optional[Any] = None
    empleado: Optional[Any] = None
    cct: Optional[Any] = None
    parametros_lsd: Optional[Any] = None


@dataclass
class EmpleadorLSD:
    cuit: str
    periodo: str
    tipo_liq: str = "M"
    nro_liq: int = 1
    dias_base: int = 30
    identificacion_envio: str = "SJ"


def registro_01(e: EmpleadorLSD, cantidad_trabajadores: int) -> str:
    periodo = _solo_digitos(e.periodo)
    if len(periodo) != 6:
        raise ValueError("periodo debe tener formato AAAAMM")
    envio = e.identificacion_envio.upper()
    if envio not in {"SJ", "RE"}:
        raise ValueError("identificacion_envio debe ser SJ o RE")
    if envio == "SJ":
        tipo = e.tipo_liq.upper()
        if tipo not in {"M", "Q", "S"}:
            raise ValueError("tipo_liq debe ser M, Q o S")
        numero = _num(e.nro_liq, 5)
    else:
        tipo, numero = " ", " " * 5
    r = ("01" + _id_fiscal(e.cuit, "CUIT") + envio + periodo + tipo + numero
         + _num(e.dias_base, 2) + _num(cantidad_trabajadores, 6))
    assert len(r) == 35
    return r


def registro_02(t: TrabajadorLSD) -> str:
    forma = str(t.forma_pago)
    if forma not in {"1", "2", "3", "4"}:
        raise ValueError("forma de pago debe ser 1, 2, 3 o 4")
    cbu = _solo_digitos(t.cbu)
    if forma == "3" and len(cbu) != 22:
        raise ValueError("la acreditacion en cuenta exige CBU de 22 digitos")
    if forma != "3":
        cbu = ""
    r = ("02" + _id_fiscal(t.cuil, "CUIL") + _txt(t.legajo, 10)
         + _txt(t.dependencia_revista, 50) + _txt(cbu, 22)
         + _num(t.dias_tope, 3) + _fecha(t.fecha_pago)
         + _fecha(t.fecha_rubrica, obligatoria=False) + forma)
    assert len(r) == 115
    return r


def registro_03(cuil: str, c: ConceptoLSD) -> str:
    codigo = str(c.codigo or "")
    if not codigo or len(codigo) > 10:
        raise ValueError("codigo de concepto del empleador debe ocupar hasta 10 posiciones")
    unidad = str(c.unidad or " ")
    if unidad not in {" ", "$", "%", "A", "M", "Q", "S", "D", "H"}:
        raise ValueError("unidad de concepto no admitida por ARCA")
    signo = c.signo.upper()
    if signo not in {"D", "C"}:
        raise ValueError("signo debe ser D o C")
    ajuste = _solo_digitos(c.periodo_ajuste)
    if ajuste and len(ajuste) != 6:
        raise ValueError("periodo de ajuste debe tener formato AAAAMM")
    r = ("03" + _id_fiscal(cuil, "CUIL") + _txt(codigo, 10)
         + _decimal_implicito(c.cantidad, 3, 2) + unidad
         + _centavos(c.importe, 15) + signo + _txt(ajuste, 6))
    assert len(r) == 51
    return r


def registro_04(t: TrabajadorLSD) -> str:
    attrs = _txt(t.attrs_suss, 147)
    if not t.bases and t.resultado_liquidacion and t.empleado and t.cct and t.parametros_lsd:
        from infrastructure.lsd.calculator import calcular_bases_lsd
        bases_fuente = calcular_bases_lsd(
            resultado=t.resultado_liquidacion, empleado=t.empleado, cct=t.cct,
            parametros=t.parametros_lsd, periodo=t.parametros_lsd.periodo,
        )
    else:
        bases_fuente = t.bases
    bases13 = (list(bases_fuente) + [Decimal("0")] * 13)[:13]
    r = ("04" + _id_fiscal(t.cuil, "CUIL") + attrs
         + "".join(_centavos(v, 15) for v in [t.remun_total, *bases13]))
    assert len(r) == 370
    return r


def build_lsd(emp: EmpleadorLSD, trabajadores: List[TrabajadorLSD]) -> str:
    lineas = [registro_01(emp, len(trabajadores))]
    lineas.extend(registro_02(t) for t in trabajadores)
    for trabajador in trabajadores:
        lineas.extend(registro_03(trabajador.cuil, c) for c in trabajador.conceptos)
    lineas.extend(registro_04(t) for t in trabajadores)
    return "\r\n".join(lineas) + "\r\n"


def build_lsd_bytes(emp: EmpleadorLSD, trabajadores: List[TrabajadorLSD]) -> bytes:
    return build_lsd(emp, trabajadores).encode("latin-1")
