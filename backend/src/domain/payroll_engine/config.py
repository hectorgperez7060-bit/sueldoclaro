"""Configuración de cálculo por CCT (parámetros no monetarios del convenio).

Estos valores describen *cómo* calcula un convenio (divisores, alícuotas de
adicionales propios del CCT). Se cargan desde la BD junto con la escala; el motor
no los hardcodea.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class CctConfig:
    cct_numero: str
    # Antigüedad: porcentaje del básico por año (Comercio 130/75 = 1% => 0.01).
    antiguedad_pct_por_anio: Decimal
    # Presentismo: divisor sobre (básico+antigüedad). Comercio = 12 (1/12 = 8,33%).
    presentismo_divisor: Decimal
    # Divisor para valor hora de horas extra. Comercio = 200.
    divisor_horas: Decimal
    aplica_presentismo: bool = True
    aplica_cuota_sindical: bool = True
    # Cuota sindical propia del convenio (fracción). None => usa el parámetro global.
    cuota_sindical_pct: Optional[Decimal] = None
