"""Entidad Empleado (dominio puro)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from ..value_objects.cuil import Cuil
from ..value_objects.dinero import Dinero


@dataclass(frozen=True)
class Empleado:
    nombre: str
    apellido: str
    cuil: Cuil
    fecha_ingreso: date
    cct_numero: str
    categoria: str
    legajo: str
    remuneracion_pactada: Optional[Dinero] = None  # si supera el básico de escala
    afiliado_sindicato: bool = True
    fecha_egreso: Optional[date] = None
    # Jornada como fracción de la jornada completa (1 = completa, 0.5 = media).
    # Contrato a tiempo parcial (LCT art. 92 ter): remuneración proporcional.
    proporcion_jornada: Decimal = Decimal("1")
    # Datos estructurados para resolver la cuota sindical de afiliado (Art. 101).
    # NO se derivan del domicilio de texto libre. El motor NO los usa: los consume
    # el repositorio para elegir la cuota oficial por CCT + localidad/filial.
    localidad: Optional[str] = None
    filial_sindical: Optional[str] = None

    def antiguedad_anios(self, a_fecha: date) -> int:
        """Años completos de antigüedad a una fecha dada."""
        anios = a_fecha.year - self.fecha_ingreso.year
        if (a_fecha.month, a_fecha.day) < (self.fecha_ingreso.month, self.fecha_ingreso.day):
            anios -= 1
        return max(anios, 0)

    def antiguedad_meses(self, a_fecha: date) -> int:
        """Meses adicionales por sobre los años completos."""
        meses = (a_fecha.year - self.fecha_ingreso.year) * 12 + (a_fecha.month - self.fecha_ingreso.month)
        if a_fecha.day < self.fecha_ingreso.day:
            meses -= 1
        return max(meses % 12, 0)
"""Entidad Empleado (dominio puro)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from ..value_objects.cuil import Cuil
from ..value_objects.dinero import Dinero


@dataclass(frozen=True)
class Empleado:
    nombre: str
    apellido: str
    cuil: Cuil
    fecha_ingreso: date
    cct_numero: str
    categoria: str
    legajo: str
    remuneracion_pactada: Optional[Dinero] = None  # si supera el básico de escala
    afiliado_sindicato: bool = True
    fecha_egreso: Optional[date] = None
    # Jornada como fracción de la jornada completa (1 = completa, 0.5 = media).
    # Contrato a tiempo parcial (LCT art. 92 ter): remuneración proporcional.
    proporcion_jornada: Decimal = Decimal("1")

    def antiguedad_anios(self, a_fecha: date) -> int:
        """Años completos de antigüedad a una fecha dada."""
        anios = a_fecha.year - self.fecha_ingreso.year
        if (a_fecha.month, a_fecha.day) < (self.fecha_ingreso.month, self.fecha_ingreso.day):
            anios -= 1
        return max(anios, 0)

    def antiguedad_meses(self, a_fecha: date) -> int:
        """Meses adicionales por sobre los años completos."""
        meses = (a_fecha.year - self.fecha_ingreso.year) * 12 + (a_fecha.month - self.fecha_ingreso.month)
        if a_fecha.day < self.fecha_ingreso.day:
            meses -= 1
        return max(meses % 12, 0)
