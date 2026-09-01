"""Bases imponibles reproducibles para el snapshot LSD.

No estima vigencias: cada período habilitado debe declarar su tope oficial.
Si falta un dato, la liquidación salarial continúa pero el TXT ARCA queda bloqueado.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from infrastructure.lsd.catalogo_afip import GrupoARCA, concepto_arca

TOPES_SIPA_MAX = {
    "2026-08": (
        Decimal("4594798.23"),
        "ANSES Resolución 232/2026, base imponible máxima agosto 2026",
    ),
}


def _info(codigo: str):
    info = concepto_arca(codigo)
    if info is not None:
        return info
    if codigo.startswith(("NO_REM_2026_08_749_", "NO_REM_2026_08_761_")):
        # Familia oficial ARCA 540000. La clasificación de la suma es la que
        # declara el acta SOECRA: no integra seguridad social en agosto.
        return {
            "grupo": GrupoARCA.NO_REMUNERATIVO,
            "codigo_tipo_arca": "540000",
            "integra_os": False,
            "integra_lrt": False,
            "verificado": True,
        }
    return None


def codigo_empleador(codigo: str) -> str:
    conocidos = {
        "BASICO": "BASICO", "ANTIGUEDAD": "ANTIG",
        "PRESENTISMO": "PRESENT", "HORAS_EXTRA_50": "HEX50",
        "HORAS_EXTRA_100": "HEX100", "SAC": "SAC",
        "VACACIONES": "VACACIONES", "APORTE_JUBILACION": "JUBILAC",
        "APORTE_LEY19032": "INSSJP", "APORTE_OBRA_SOCIAL": "OBRA_SOC",
        "CUOTA_SINDICAL": "CUOTA_SIND",
    }
    if codigo in conocidos:
        return conocidos[codigo]
    if codigo.startswith("NO_REM_2026_08_749_"):
        return "NR749AGO"
    if codigo.startswith("NO_REM_2026_08_761_"):
        return "NR761AGO"
    raise ValueError(f"Concepto sin código de empleador ARCA: {codigo}")


def codigo_tipo_arca(codigo: str) -> str:
    info = _info(codigo)
    if info is None:
        raise ValueError(f"Concepto sin homologación ARCA: {codigo}")
    if isinstance(info, dict):
        return info["codigo_tipo_arca"]
    if not info.verificado or not info.codigo_tipo_arca:
        raise ValueError(f"Concepto ARCA pendiente de verificar: {codigo}")
    return info.codigo_tipo_arca


def calcular_bases_snapshot(
    conceptos: list[dict[str, Any]], periodo: str, perfil: dict[str, Any],
) -> tuple[list[Decimal], dict[str, str]]:
    if periodo not in TOPES_SIPA_MAX:
        raise ValueError(f"No hay topes oficiales LSD cargados para {periodo}")
    if perfil.get("detraccion_confirmada") is not True:
        raise ValueError("Falta confirmar la detracción Ley 27.541, incluso si corresponde cero")
    remunerativo = Decimal("0")
    base_os_sin_tope = Decimal("0")
    base_lrt = Decimal("0")
    for c in conceptos:
        codigo = str(c.get("codigo", ""))
        info = _info(codigo)
        if info is None:
            raise ValueError(f"Concepto sin homologación ARCA: {codigo}")
        importe = Decimal(str(c.get("importe", 0)))
        tipo = str(c.get("tipo", "")).upper()
        if tipo == "REMUNERATIVO":
            remunerativo += importe
        if isinstance(info, dict):
            integra_os, integra_lrt = info["integra_os"], info["integra_lrt"]
        else:
            if not info.verificado:
                raise ValueError(f"Concepto ARCA pendiente de verificar: {codigo}")
            integra_os = info.incidencias.integra_obra_social
            integra_lrt = info.incidencias.integra_lrt
        if integra_os and tipo != "DESCUENTO":
            base_os_sin_tope += importe
        if integra_lrt and tipo != "DESCUENTO":
            base_lrt += importe

    tope, fuente = TOPES_SIPA_MAX[periodo]
    base_aporte = min(remunerativo, tope)
    detraccion = Decimal(str(perfil.get("detraccion_ley_27541", 0)))
    if detraccion < 0 or detraccion > remunerativo:
        raise ValueError("Detracción Ley 27.541 inválida")
    base6 = Decimal(str(perfil.get("base_diferencial_aporte", 0)))
    base7 = Decimal(str(perfil.get("base_diferencial_contribucion", 0)))
    bases = [
        base_aporte, remunerativo, remunerativo, min(base_os_sin_tope, tope),
        base_aporte, base6, base7, base_os_sin_tope, base_lrt,
        remunerativo - detraccion,
    ]
    return bases, {"tope_sipa_max": str(tope), "fuente_tope": fuente,
                   "detraccion": str(detraccion)}
