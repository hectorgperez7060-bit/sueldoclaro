"""Concepto liquidado: una línea del recibo."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from ..value_objects.dinero import Dinero


class TipoConcepto(str, Enum):
    REMUNERATIVO = "remunerativo"
    NO_REMUNERATIVO = "no_remunerativo"
    DEDUCCION = "deduccion"
    CONTRIBUCION = "contribucion"  # patronal, no afecta el neto del trabajador


class Regimen(str, Enum):
    """Régimen legal aplicado a un concepto (trazabilidad ante inspección)."""

    LEY_27802 = "ley_27802"     # regla nueva de la Ley 27.802 / Decreto 407/2026
    PREVIA = "previa"           # regla previa reactivada por amparo judicial
    NO_APLICA = "no_aplica"     # concepto no afectado por la reforma


@dataclass(frozen=True)
class Concepto:
    codigo: str
    descripcion: str
    tipo: TipoConcepto
    importe: Dinero                 # ya redondeado (resultado final de línea)
    cantidad: Decimal = Decimal("1")
    regimen: Regimen = Regimen.NO_APLICA
    articulo_amparo: Optional[str] = None  # p.ej. "L27802:131" si se aplicó regla previa
