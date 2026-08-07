"""Generador del Libro de Sueldos Digital (LSD / RG 3781) - archivo de ancho fijo
para importar en ARCA y producir la DJ F.931.

Formato validado byte-a-byte contra un archivo real aceptado por ARCA
(empleador 27-20736432-6, período 2026-07). Ver tests/test_lsd_golden.py.

Registros:
  01 empleador (cabecera de la liquidación)
  02 datos de la liquidación de cada trabajador
  03 conceptos del recibo (uno por línea)
  04 atributos SUSS/SICOSS + bases imponibles (produce el F.931)

Reglas de oro para que ARCA NO rechace:
  - Codificación ANSI (latin-1), sin compresión.
  - Cada registro en su propia línea, el 01 primero.
  - Ancho fijo exacto por registro; ningún campo obligatorio en blanco.
  - Forma de pago = 1/2/3/4. Si es 3 (acreditación en cuenta) el CBU es obligatorio;
    para las otras formas el CBU va en blanco.
  - Importes en centavos, sin punto ni coma, con ceros a la izquierda.
  - Fechas en formato AAAAMMDD.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List

# ---- helpers de formato de ancho fijo -------------------------------------

def _num(valor, largo: int) -> str:
    """Entero con ceros a la izquierda."""
    s = str(int(valor))
    if len(s) > largo:
        raise ValueError(f"numero {s} excede {largo} posiciones")
    return s.rjust(largo, "0")

def _cent(monto: Decimal, largo: int = 15) -> str:
    """Monto -> centavos, ceros a la izquierda (2 decimales implícitos)."""
    c = int((Decimal(monto) * 100).to_integral_value())
    return _num(abs(c), largo)

def _txt(valor: str, largo: int) -> str:
    """Texto justificado a la izquierda, completado con blancos, truncado si excede."""
    return (valor or "")[:largo].ljust(largo, " ")

def _cuil(cuil: str) -> str:
    d = "".join(ch for ch in (cuil or "") if ch.isdigit())
    if len(d) != 11:
        raise ValueError(f"CUIL invalido: {cuil!r}")
    return d


# ---- estructuras de entrada -----------------------------------------------

@dataclass
class ConceptoLSD:
    codigo: str          # código AFIP del concepto (15 pos, ya formateado o numérico)
    importe: Decimal     # importe positivo
    signo: str           # 'C' (a favor) o 'D' (descuento)

@dataclass
class TrabajadorLSD:
    cuil: str
    legajo: str = ""
    forma_pago: str = "1"          # 1 efectivo, 2 valores, 3 cta bancaria, 4 otra
    cbu: str = ""                  # obligatorio si forma_pago == '3'
    dias_tope: int = 0             # 0 = no proporciona tope
    fecha_pago: str = ""           # AAAAMMDD
    conceptos: List[ConceptoLSD] = field(default_factory=list)
    # bloque de atributos SUSS (posiciones 14..160 del registro 04)
    attrs_suss: str = ""           # 147 chars ya armados (ver build_attrs_suss)
    adherentes_os: int = 0         # cantidad de adherentes de obra social
    remun_total: Decimal = Decimal("0")   # remuneración total
    bases: List[Decimal] = field(default_factory=list)  # hasta 13 bases imponibles

@dataclass
class EmpleadorLSD:
    cuit: str
    periodo: str          # AAAAMM
    tipo_liq: str = "M"   # M mensual
    nro_liq: int = 1
    dias_base: int = 30
    sello: str = "SJ"     # identificador de envío (2 chars) del archivo original
    cola01: str = "0000130000002"  # cola fija validada del registro 01


# ---- registros ------------------------------------------------------------

def registro_01(e: EmpleadorLSD) -> str:
    # 01 + CUIT(11) + sello(2) + periodo(6) + tipo(1) + cola(13) = 35
    r = "01" + _cuil(e.cuit) + _txt(e.sello, 2) + e.periodo + e.tipo_liq + e.cola01
    assert len(r) == 35, f"reg01 len {len(r)}"
    return r

def registro_02(t: TrabajadorLSD) -> str:
    fp = str(t.forma_pago)
    if fp not in ("1", "2", "3", "4"):
        raise ValueError(f"forma de pago invalida: {fp!r} (debe ser 1/2/3/4)")
    cbu = t.cbu if fp == "3" else ""
    if fp == "3" and len(_only(cbu)) != 22:
        raise ValueError("forma de pago 3 exige CBU de 22 digitos")
    # 02 + CUIL(11) + legajo(10) + dependencia(50) + fpago(1) + CBU(22)
    #    + diastope(2) + fechapago(8) + rubrica(8) + reserva(1) = 115
    r = ("02" + _cuil(t.cuil) + _txt(t.legajo, 10) + _txt("", 50) + fp
         + _txt(_only(cbu), 22) + _num(t.dias_tope, 2) + t.fecha_pago
         + _txt("", 8) + "0")
    assert len(r) == 115, f"reg02 len {len(r)}"
    return r

def registro_03(cuil: str, c: ConceptoLSD) -> str:
    cod = c.codigo if not c.codigo.isdigit() else _num(c.codigo, 15)
    cod = _txt(cod, 15) if len(cod) != 15 else cod
    signo = c.signo.upper()
    if signo not in ("C", "D"):
        raise ValueError("signo debe ser C o D")
    # 03 + CUIL(11) + concepto(15) + '$' + importe(15) + signo(1) + relleno(6) = 51
    r = "03" + _cuil(cuil) + cod + "$" + _cent(c.importe, 15) + signo + _txt("", 6)
    assert len(r) == 51, f"reg03 len {len(r)}"
    return r

def registro_04(t: TrabajadorLSD) -> str:
    # 04 + CUIL(11) + atributos SUSS(147) + 14 campos de 15 (remun total + 13 bases) = 370
    attrs = _txt(t.attrs_suss, 147)
    bases13 = (list(t.bases) + [Decimal("0")] * 13)[:13]
    cuerpo = "".join(_cent(v, 15) for v in [t.remun_total, *bases13])
    r = "04" + _cuil(t.cuil) + attrs + cuerpo
    assert len(r) == 370, f"reg04 len {len(r)}"
    return r


def _only(s: str) -> str:
    return "".join(ch for ch in (s or "") if ch.isdigit())


def build_lsd(emp: EmpleadorLSD, trabajadores: List[TrabajadorLSD]) -> str:
    lineas = [registro_01(emp)]
    for t in trabajadores:
        lineas.append(registro_02(t))
    for t in trabajadores:
        for c in t.conceptos:
            lineas.append(registro_03(t.cuil, c))
    for t in trabajadores:
        lineas.append(registro_04(t))
    return "\n".join(lineas)
