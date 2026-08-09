"""Catálogo de conceptos ARCA para el Libro de Sueldos Digital.

Mapea cada concepto que produce el motor de Sueldo Claro (código interno) al
CONCEPTO ARCA oficial que corresponde informar en el LSD, junto con su grupo
(REMUNERATIVO / NO_REMUNERATIVO / DESCUENTO), incidencias de subsistemas y clase de tope.

Fuentes oficiales (ARCA / AFIP):
- Guía N.º 4b «Administrar conceptos» (grupos y familia de descuentos 810000).
- Guía N.º 15 «Interfaz de liquidación» (registros 02/03/04).
- Guía N.º 18 «Armado de bases imponibles LSD» (Bases 1 a 10).
- Guía N.º 28 «Sueldo Anual Complementario (SAC)».
- Guía N.º 31 «Vacaciones».
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional


class GrupoARCA(str, Enum):
    REMUNERATIVO = "REMUNERATIVO"
    NO_REMUNERATIVO = "NO_REMUNERATIVO"
    DESCUENTO = "DESCUENTO"


class ClaseTopeARCA(str, Enum):
    MENSUAL = "MENSUAL"                  # Haberes ordinarios + Plus vacacional (151000)
    SAC = "SAC"                          # SAC estándar (12X.XXX excepto 120003)
    SAC_PROPORCIONAL = "SAC_PROPORCIONAL"# SAC proporcional desvinculación (120003)
    VACACIONES = "VACACIONES"            # Licencia ordinaria vacaciones (150000)
    SIN_TOPE = "SIN_TOPE"                # No sujeto a tope previsional (ej. ART Base 9 o contribuciones)


@dataclass(frozen=True)
class IncidenciasSubsistemasARCA:
    """Subsistemas oficiales de seguridad social que integra el concepto. Default seguro en False."""
    integra_sipa: bool = False           # Jubilación / Previsional (Bases 1, 2)
    integra_inssjyp: bool = False        # INSSJP / PAMI (Bases 2, 5)
    integra_aaff_fne: bool = False       # AAFF + FNE + RENATRE (Base 3)
    integra_obra_social: bool = False    # Obra Social + FSR (Bases 4, 8)
    integra_lrt: bool = False            # Riesgos del Trabajo / ART (Base 9)


@dataclass(frozen=True)
class ConceptoARCA:
    """Definición y comportamiento normativo ARCA de un concepto de recibo."""

    # 1. Identificación y clasificación oficial
    codigo_tipo_arca: Optional[str]              # Código oficial ARCA 6 díg. (ej. "110000", "810000", "540000")
    grupo: GrupoARCA                             # REMUNERATIVO | NO_REMUNERATIVO | DESCUENTO
    descripcion: str                             # Descripción oficial del catálogo

    # 2. Incidencias y clasificación de tope
    incidencias: IncidenciasSubsistemasARCA = field(default_factory=IncidenciasSubsistemasARCA)
    clase_tope: ClaseTopeARCA = ClaseTopeARCA.MENSUAL
    bases_potenciales: List[int] = field(default_factory=list)  # Lista de bases F.931 (1..10) que potencialmente integra

    # 3. Banderas de comportamiento normativo
    aplica_tope_os: bool = True                  # Si aplica tope o piso imponible de Obra Social
    admite_regimen_diferencial: bool = False     # Si computa para Bases 6 y 7 en regímenes especiales/insalubres
    integra_lrt: bool = True                     # Si computa para la Base 9 de ART / LRT
    aplica_detraccion_ley27541: bool = True      # Si es elegible para la detracción patronal en Base 10

    # 4. Parámetros de liquidación y personalización
    requiere_cantidad_dias: bool = False         # Exige informar días/horas en Registro 03 para prorrateo de tope
    permite_override_empleador: bool = True      # Si el empleador puede personalizar la homologación

    # 5. Trazabilidad legal y auditoría
    fuente: str = ""                             # Referencia oficial (ej. "ARCA Guía N.º 18 / Guía N.º 28")
    valid_from: date = date(2026, 1, 1)          # Inicio de vigencia de la regla
    valid_to: Optional[date] = None              # Fin de vigencia (None si está vigente)
    verificado: bool = False                     # True sólo si el código proviene de fuente oficial ARCA

    @property
    def codigo_afip(self) -> Optional[str]:
        """Alias de compatibilidad para codigo_tipo_arca."""
        return self.codigo_tipo_arca

    @property
    def bases(self) -> List[int]:
        """Alias de compatibilidad para bases_potenciales."""
        return self.bases_potenciales


# Familia de DESCUENTOS que ARCA usa para el control del F.931
# (Guía N.º 4b, sección «OTRAS CONSIDERACIONES», punto 5). VERIFICADO.
_D = GrupoARCA.DESCUENTO
_R = GrupoARCA.REMUNERATIVO
_NR = GrupoARCA.NO_REMUNERATIVO
_FUENTE_G4B = "ARCA – Guía N.º 4b Administrar conceptos (familia 810000 / 820000)"
_FUENTE_G18 = "ARCA – Guía N.º 18 Armado de bases imponibles LSD"

# Incidencias estándar para conceptos remunerativos de haberes ordinarios
_INC_REM = IncidenciasSubsistemasARCA(
    integra_sipa=True,
    integra_inssjyp=True,
    integra_aaff_fne=True,
    integra_obra_social=True,
    integra_lrt=True,
)

# Mapeo: código interno del motor Sueldo Claro -> concepto ARCA.
CATALOGO: Dict[str, ConceptoARCA] = {
    # -------- DESCUENTOS (aportes del trabajador) — VERIFICADOS --------
    "APORTE_JUBILACION": ConceptoARCA("810000", _D, "Aporte Sistema Previsional (SIPA)", verificado=True, fuente=_FUENTE_G4B, clase_tope=ClaseTopeARCA.SIN_TOPE),
    "APORTE_LEY19032":   ConceptoARCA("810001", _D, "Aporte INSSJyP (Ley 19.032)", verificado=True, fuente=_FUENTE_G4B, clase_tope=ClaseTopeARCA.SIN_TOPE),
    "APORTE_OBRA_SOCIAL": ConceptoARCA("810002", _D, "Aporte Obra Social", verificado=True, fuente=_FUENTE_G4B, clase_tope=ClaseTopeARCA.SIN_TOPE),
    # Cuota sindical y aportes solidarios: NO integran el F.931 -> «otros descuentos».
    "CUOTA_SINDICAL":        ConceptoARCA("820000", _D, "Cuota sindical (otros descuentos)", verificado=True, fuente=_FUENTE_G4B, clase_tope=ClaseTopeARCA.SIN_TOPE),
    "APORTE_SOLIDARIO_UOCRA": ConceptoARCA("820000", _D, "Aporte solidario UOCRA (otros descuentos)", verificado=True, fuente=_FUENTE_G4B, clase_tope=ClaseTopeARCA.SIN_TOPE),

    # -------- REMUNERATIVOS --------
    "BASICO":         ConceptoARCA("110000", _R, "Sueldo básico", incidencias=_INC_REM, bases_potenciales=[1, 2, 3, 4, 5, 8, 9, 10], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.MENSUAL),
    "ANTIGUEDAD":     ConceptoARCA("120000", _R, "Antigüedad", incidencias=_INC_REM, bases_potenciales=[1, 2, 3, 4, 5, 8, 9, 10], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.MENSUAL),
    "PRESENTISMO":    ConceptoARCA("120000", _R, "Presentismo", incidencias=_INC_REM, bases_potenciales=[1, 2, 3, 4, 5, 8, 9, 10], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.MENSUAL),
    "HORAS_EXTRA_50": ConceptoARCA("130000", _R, "Horas extra 50%", incidencias=_INC_REM, bases_potenciales=[1, 2, 3, 4, 5, 8, 9, 10], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.MENSUAL),
    "HORAS_EXTRA_100": ConceptoARCA("130000", _R, "Horas extra 100%", incidencias=_INC_REM, bases_potenciales=[1, 2, 3, 4, 5, 8, 9, 10], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.MENSUAL),
    "SAC":            ConceptoARCA("120000", _R, "SAC (Sueldo Anual Complementario)", incidencias=_INC_REM, bases_potenciales=[1, 2, 3, 4, 5, 8, 9, 10], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.SAC),
    "VACACIONES":     ConceptoARCA("150000", _R, "Vacaciones (Licencia ordinaria)", incidencias=_INC_REM, bases_potenciales=[1, 2, 3, 4, 5, 8, 9, 10], requiere_cantidad_dias=True, verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.VACACIONES),

    # -------- NO REMUNERATIVOS --------
    "SANIDAD_SUMA_NR_JUN_JUL": ConceptoARCA("540000", _NR, "Suma no remunerativa FATSA", incidencias=IncidenciasSubsistemasARCA(integra_sipa=False, integra_inssjyp=False, integra_aaff_fne=False, integra_obra_social=True, integra_lrt=True), bases_potenciales=[4, 5, 8, 9], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.SIN_TOPE),
    "SANIDAD_SUMA_NR_AGO":     ConceptoARCA("540000", _NR, "Suma no remunerativa FATSA", incidencias=IncidenciasSubsistemasARCA(integra_sipa=False, integra_inssjyp=False, integra_aaff_fne=False, integra_obra_social=True, integra_lrt=True), bases_potenciales=[4, 5, 8, 9], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.SIN_TOPE),
    "SANIDAD_DIA_SANIDAD_122/75": ConceptoARCA("540000", _NR, "Día de la Sanidad (pago único)", incidencias=IncidenciasSubsistemasARCA(integra_sipa=False, integra_inssjyp=False, integra_aaff_fne=False, integra_obra_social=True, integra_lrt=True), bases_potenciales=[4, 5, 8, 9], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.SIN_TOPE),
    "SANIDAD_DIA_SANIDAD_108/75": ConceptoARCA("540000", _NR, "Día de la Sanidad (pago único)", incidencias=IncidenciasSubsistemasARCA(integra_sipa=False, integra_inssjyp=False, integra_aaff_fne=False, integra_obra_social=True, integra_lrt=True), bases_potenciales=[4, 5, 8, 9], verificado=True, fuente=_FUENTE_G18, clase_tope=ClaseTopeARCA.SIN_TOPE),
    # Aporte modernización (Ley 27.802 art. 131): régimen nuevo, código a confirmar.
    "APORTE_MODERNIZACION": ConceptoARCA("820000", _D, "Aporte modernización (Ley 27.802)", verificado=False, fuente="art. 131 Ley 27.802", clase_tope=ClaseTopeARCA.SIN_TOPE),
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

