"""Catálogo de conceptos ARCA para el Libro de Sueldos Digital.

Mapea cada concepto que produce el motor de Sueldo Claro (código interno) al
CONCEPTO ARCA oficial que corresponde informar en el LSD, junto con el grupo
(remunerativo / no remunerativo / descuento) y las bases imponibles que afecta.

Fuentes oficiales (ARCA / AFIP):
- Guía N.º 4b «Administrar conceptos» (grupos y familia de descuentos 810000).
- Guía N.º 15 «Interfaz de liquidación» (registros 02/03/04, bases imponibles 1-10).

Regla de oro (no vender humo): sólo se marca ``verificado=True`` un concepto
cuyo código ARCA salió de una fuente oficial. Los que faltan confirmar contra el
archivo «Diseño interfaz conceptos» de ARCA quedan con ``verificado=False`` y NO
deben usarse para generar un LSD de producción hasta confirmarlos.

Grupos ARCA:
- REMUNERATIVO: integra remuneración bruta y (según perfil) todas las BI.
- NO_REMUNERATIVO: integra bruto pero sólo las BI que correspondan (p.ej. LRT).
- DESCUENTO: aportes del trabajador. La familia 810000 arma el control del F.931.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class GrupoARCA(str, Enum):
    REMUNERATIVO = "remunerativo"
    NO_REMUNERATIVO = "no_remunerativo"
    DESCUENTO = "descuento"


@dataclass(frozen=True)
class ConceptoARCA:
    codigo_afip: Optional[str]      # código ARCA (6 díg.); None si aún no confirmado
    grupo: GrupoARCA
    descripcion: str
    verificado: bool = False        # True sólo si el código salió de fuente oficial
    fuente: str = ""
    # Bases imponibles (1..10) que el concepto integra. Vacío para descuentos.
    bases: List[int] = field(default_factory=list)


# Familia de DESCUENTOS que ARCA usa para el control del F.931
# (Guía N.º 4b, sección «OTRAS CONSIDERACIONES», punto 5). VERIFICADO.
_D = GrupoARCA.DESCUENTO
_R = GrupoARCA.REMUNERATIVO
_NR = GrupoARCA.NO_REMUNERATIVO
_FUENTE_G4B = "ARCA – Guía N.º 4b Administrar conceptos (familia 810000 / 820000)"

# Mapeo: código interno del motor Sueldo Claro -> concepto ARCA.
CATALOGO: Dict[str, ConceptoARCA] = {
    # -------- DESCUENTOS (aportes del trabajador) — VERIFICADOS --------
    "APORTE_JUBILACION": ConceptoARCA("810000", _D, "Aporte Sistema Previsional (SIPA)", True, _FUENTE_G4B),
    "APORTE_LEY19032":   ConceptoARCA("810001", _D, "Aporte INSSJyP (Ley 19.032)", True, _FUENTE_G4B),
    "APORTE_OBRA_SOCIAL": ConceptoARCA("810002", _D, "Aporte Obra Social", True, _FUENTE_G4B),
    # Cuota sindical y aportes solidarios: NO integran el F.931 -> «otros descuentos».
    "CUOTA_SINDICAL":        ConceptoARCA("820000", _D, "Cuota sindical (otros descuentos)", True, _FUENTE_G4B),
    "APORTE_SOLIDARIO_UOCRA": ConceptoARCA("820000", _D, "Aporte solidario UOCRA (otros descuentos)", True, _FUENTE_G4B),

    # -------- REMUNERATIVOS — código exacto A CONFIRMAR --------
    # El rango de «Sueldos» va del 110000 al 119999 (Guía N.º 4b), pero el código
    # puntual de cada adicional debe confirmarse contra «Diseño interfaz conceptos».
    "BASICO":         ConceptoARCA(None, _R, "Sueldo básico", False, "rango 110000-119999 (confirmar código)"),
    "ANTIGUEDAD":     ConceptoARCA(None, _R, "Antigüedad", False, "confirmar código ARCA"),
    "PRESENTISMO":    ConceptoARCA(None, _R, "Presentismo", False, "confirmar código ARCA"),
    "HORAS_EXTRA_50": ConceptoARCA(None, _R, "Horas extra 50%", False, "rango 130000-139999 (confirmar)"),
    "HORAS_EXTRA_100": ConceptoARCA(None, _R, "Horas extra 100%", False, "rango 130000-139999 (confirmar)"),

    # -------- NO REMUNERATIVOS — código exacto A CONFIRMAR --------
    "SANIDAD_SUMA_NR_JUN_JUL": ConceptoARCA(None, _NR, "Suma no remunerativa FATSA", False, "confirmar código ARCA"),
    "SANIDAD_SUMA_NR_AGO":     ConceptoARCA(None, _NR, "Suma no remunerativa FATSA", False, "confirmar código ARCA"),
    "SANIDAD_DIA_SANIDAD_122/75": ConceptoARCA(None, _NR, "Día de la Sanidad (pago único)", False, "confirmar código ARCA"),
    "SANIDAD_DIA_SANIDAD_108/75": ConceptoARCA(None, _NR, "Día de la Sanidad (pago único)", False, "confirmar código ARCA"),
    # Aporte modernización (Ley 27.802 art. 131): régimen nuevo, código a confirmar.
    "APORTE_MODERNIZACION": ConceptoARCA(None, _D, "Aporte modernización (Ley 27.802)", False, "confirmar código ARCA"),
}


def concepto_arca(codigo_interno: str) -> Optional[ConceptoARCA]:
    return CATALOGO.get(codigo_interno)


def faltan_por_confirmar() -> List[str]:
    """Códigos internos cuyo concepto ARCA todavía no está verificado.

    El generador de LSD debe abortar si algún concepto liquidado está en esta
    lista: preferimos no generar archivo antes que generar uno que ARCA rechace.
    """
    return [k for k, v in CATALOGO.items() if not v.verificado]


def es_generable(codigos_liquidados: List[str]) -> bool:
    """True sólo si TODOS los conceptos liquidados tienen código ARCA verificado."""
    return all(
        (c in CATALOGO and CATALOGO[c].verificado) for c in codigos_liquidados
    )
