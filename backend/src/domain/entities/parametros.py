"""Parámetros legales versionados y set de amparos (dominio puro).

Ningún valor legal vive hardcodeado en el motor: el motor recibe estos objetos
y solo lee de ellos (sección 0.2 del prompt maestro).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from ..value_objects.dinero import Dinero
from ..value_objects.periodo import Periodo


@dataclass(frozen=True)
class ParametroLegal:
    codigo: str                 # p.ej. "APORTE_JUBILACION"
    valor: Decimal
    unidad: str                 # "%" (fracción, 0.11 == 11%) | "ARS"
    ambito: str                 # "empleado" | "empleador"
    valid_from: date
    valid_to: Optional[date] = None
    is_verified: bool = False
    fuente: str = ""
    cct_numero: Optional[str] = None      # concepto propio de un convenio (null = global)
    incidencias: Optional[dict] = None    # qué bases integra / qué aportes dispara


@dataclass(frozen=True)
class EscalaSalarial:
    cct_numero: str
    categoria: str
    basico: Dinero
    valid_from: date
    valid_to: Optional[date] = None
    is_verified: bool = False
    fuente: str = ""


@dataclass(frozen=True)
class Amparo:
    """Cautelar que suspende un artículo de la Ley 27.802 / Decreto 407/2026.

    ``concepto_afectado`` es el código interno del motor de cálculo cuyo régimen
    cambia cuando el amparo está vigente.
    """

    cct_numero: str
    articulo_suspendido: str    # "L27802:131", "D407:5", ...
    concepto_afectado: str      # código interno del motor, p.ej. "APORTE_MODERNIZACION"
    estado: str                 # "vigente" | "revocada" | "firme"
    valid_from: date
    valid_to: Optional[date] = None
    juzgado: str = ""
    is_verified: bool = False


class ParametroSet:
    """Conjunto de parámetros vigentes para una liquidación."""

    def __init__(self, parametros: List[ParametroLegal]):
        self._por_codigo: Dict[str, ParametroLegal] = {p.codigo: p for p in parametros}
        self._todos: List[ParametroLegal] = list(parametros)

    def conceptos_convenio(self, cct_numero: str) -> List[ParametroLegal]:
        """Conceptos en ARS propios de un convenio (NR/adicionales), ya filtrados
        por período. El motor los aplica leyendo sus ``incidencias`` —sin saber
        de qué convenio se trata."""
        return [p for p in self._todos
                if p.cct_numero == cct_numero and p.unidad == "ARS"]

    def _obtener(self, codigo: str) -> ParametroLegal:
        if codigo not in self._por_codigo:
            raise KeyError(f"Parámetro legal faltante: {codigo}")
        return self._por_codigo[codigo]

    def fraccion(self, codigo: str) -> Decimal:
        """Devuelve el valor como fracción (0.11 para 11%)."""
        p = self._obtener(codigo)
        if p.unidad != "%":
            raise ValueError(f"{codigo} no es un porcentaje")
        return p.valor

    def valor_ars(self, codigo: str) -> Dinero:
        p = self._obtener(codigo)
        if p.unidad != "ARS":
            raise ValueError(f"{codigo} no es un valor en ARS")
        return Dinero(p.valor)

    def existe(self, codigo: str) -> bool:
        return codigo in self._por_codigo

    def hay_no_verificados(self) -> bool:
        return any(not p.is_verified for p in self._por_codigo.values())


class AmparoSet:
    """Conjunto de amparos; decide qué régimen aplicar por concepto."""

    def __init__(self, amparos: Optional[List[Amparo]] = None):
        self._amparos: List[Amparo] = list(amparos) if amparos else []

    def amparo_vigente(
        self, cct_numero: str, concepto_afectado: str, periodo: Periodo
    ) -> Optional[Amparo]:
        """Devuelve el amparo aplicable al concepto en el período, o None."""
        ref = periodo.primer_dia()
        for a in self._amparos:
            if a.cct_numero != cct_numero:
                continue
            if a.concepto_afectado != concepto_afectado:
                continue
            if a.estado != "vigente":
                continue
            if a.valid_from > ref:
                continue
            if a.valid_to is not None and a.valid_to < ref:
                continue
            return a
        return None
