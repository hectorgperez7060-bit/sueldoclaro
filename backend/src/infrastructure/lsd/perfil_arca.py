"""Armado validado de los 147 caracteres registrales del Registro 04 ARCA."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

CAMPOS_OBLIGATORIOS = (
    "tipo_empleador", "tipo_operacion", "situacion_revista", "condicion",
    "actividad", "modalidad_contratacion", "siniestrado", "localidad",
    "codigo_obra_social", "dias_trabajados",
)


def faltantes_perfil(perfil: dict[str, Any] | None) -> list[str]:
    p = perfil or {}
    faltan = [campo for campo in CAMPOS_OBLIGATORIOS if p.get(campo) in (None, "")]
    if p.get("forma_pago") == "3" and len("".join(filter(str.isdigit, p.get("cbu", "")))) != 22:
        faltan.append("cbu_22_digitos")
    return faltan


def _texto(valor: Any, largo: int, campo: str) -> str:
    s = str(valor if valor is not None else "")
    if len(s) != largo:
        raise ValueError(f"{campo} debe ocupar exactamente {largo} posiciones")
    return s


def _entero(valor: Any, largo: int, campo: str) -> str:
    try:
        n = int(valor)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{campo} debe ser numérico") from exc
    if n < 0 or len(str(n)) > largo:
        raise ValueError(f"{campo} excede {largo} posiciones")
    return str(n).zfill(largo)


def _importe(valor: Any, campo: str) -> str:
    d = Decimal(str(valor or 0)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    if d < 0:
        raise ValueError(f"{campo} no puede ser negativo")
    centavos = str(int(d * 100))
    if len(centavos) > 15:
        raise ValueError(f"{campo} excede 15 posiciones")
    return centavos.zfill(15)


def _porcentaje(valor: Any, campo: str) -> str:
    d = Decimal(str(valor or 0)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    if d < 0 or d > Decimal("999.99"):
        raise ValueError(f"{campo} debe estar entre 0 y 999,99")
    return str(int(d * 100)).zfill(5)


def construir_atributos_suss(
    perfil: dict[str, Any],
    *,
    conyuge: bool = False,
    hijos: int = 0,
    tiene_cct: bool = True,
) -> str:
    """Devuelve posiciones 14-160 del Registro 04 (diseño ARCA 15/05/2026)."""
    faltan = faltantes_perfil(perfil)
    if faltan:
        raise ValueError("Faltan datos registrales ARCA: " + ", ".join(faltan))
    p = perfil
    situaciones = [
        (p.get("situacion_revista"), p.get("dia_inicio_situacion", 1)),
        (p.get("situacion_revista_2", "00"), p.get("dia_inicio_situacion_2", 0)),
        (p.get("situacion_revista_3", "00"), p.get("dia_inicio_situacion_3", 0)),
    ]
    attrs = (
        ("1" if conyuge else "0")
        + _entero(hijos, 2, "hijos")
        + ("1" if tiene_cct else "0")
        + ("1" if p.get("scvo", True) else "0")
        + ("1" if p.get("reduccion", False) else "0")
        + _texto(p["tipo_empleador"], 1, "tipo_empleador")
        + _texto(p["tipo_operacion"], 1, "tipo_operacion")
        + _texto(p["situacion_revista"], 2, "situacion_revista")
        + _texto(p["condicion"], 2, "condicion")
        + _texto(p["actividad"], 3, "actividad")
        + _texto(p["modalidad_contratacion"], 3, "modalidad_contratacion")
        + _texto(p["siniestrado"], 2, "siniestrado")
        + _texto(p["localidad"], 2, "localidad")
        + "".join(_texto(s, 2, "situacion") + _entero(d, 2, "día situación") for s, d in situaciones)
        + _entero(p["dias_trabajados"], 2, "dias_trabajados")
        + _entero(p.get("horas_trabajadas", 0), 3, "horas_trabajadas")
        + _porcentaje(p.get("aporte_adicional_ss_pct", 0), "aporte_adicional_ss_pct")
        + _porcentaje(p.get("contribucion_diferencial_pct", 0), "contribucion_diferencial_pct")
        + _texto(p["codigo_obra_social"], 6, "codigo_obra_social")
        + _entero(p.get("adherentes_obra_social", 0), 2, "adherentes_obra_social")
        + _importe(p.get("aporte_adicional_os", 0), "aporte_adicional_os")
        + _importe(p.get("contribucion_adicional_os", 0), "contribucion_adicional_os")
        + _importe(p.get("base_diferencial_os_aporte", 0), "base_diferencial_os_aporte")
        + _importe(p.get("base_diferencial_os_contribucion", 0), "base_diferencial_os_contribucion")
        + _importe(p.get("base_diferencial_lrt", 0), "base_diferencial_lrt")
        + _importe(p.get("remuneracion_maternidad", 0), "remuneracion_maternidad")
    )
    if len(attrs) != 147:
        raise AssertionError(f"Atributos SUSS inválidos: {len(attrs)} caracteres")
    return attrs
