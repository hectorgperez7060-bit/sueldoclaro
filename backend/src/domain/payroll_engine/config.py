"""Configuración de cálculo por CCT (parámetros no monetarios del convenio).

Estos valores describen *cómo* calcula un convenio (divisores, alícuotas de
adicionales propios del CCT). Se cargan desde la BD junto con la escala; el motor
no los hardcodea.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Tuple


@dataclass(frozen=True)
class ReglaAdicionalConfig:
    """Fórmula auditable de un adicional convencional remunerativo."""
    codigo: str
    descripcion: str
    porcentaje: Decimal
    base: str
    articulo: str
    requiere_cantidad: bool = False
    # multiplicador: base × porcentaje × cantidad.
    # proporcion_periodo: base × porcentaje × cantidad / cantidad_base.
    modo_calculo: str = "multiplicador"
    clave_cantidad_base: Optional[str] = None
    # Dos reglas del mismo grupo no pueden aplicarse simultáneamente al mismo
    # empleado y período (por ejemplo, dos regímenes alternativos de sector).
    grupo_exclusion: Optional[str] = None
    # Los adicionales generales del convenio se aplican sin que el usuario
    # tenga que cargarlos como novedad mensual (p.ej. asistencia UTHGRA).
    aplica_automaticamente: bool = False
    # Naturaleza del concepto en el recibo. La mayoría son remunerativos;
    # algunos convenios definen expresamente adicionales no remunerativos.
    naturaleza: str = "remunerativo"


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
    # Algunos convenios no calculan antigüedad como un porcentaje lineal por
    # año. Farmacia 414/05, por ejemplo, usa escalones (1 año 5%, 2 años
    # 10%, 5 años 20%, etc.). Cada elemento es (años_desde, fracción).
    # Si no se informa, se conserva el cálculo lineal existente.
    antiguedad_escalones: Optional[Tuple[Tuple[int, Decimal], ...]] = None
    adicionales: Tuple[ReglaAdicionalConfig, ...] = ()
    # Básicos de categorías usadas como referencia por otros adicionales.
    # Se informan por período junto con la escala, nunca quedan en el motor.
    bases_referencia: Tuple[Tuple[str, Decimal], ...] = ()

    def antiguedad_fraccion(self, anios: int) -> Decimal:
        """Porcentaje de antigüedad vigente para la cantidad de años.

        Los escalones se resuelven por el mayor umbral alcanzado. La
        configuración sigue siendo externa al motor y, por lo tanto, auditable
        por convenio y período.
        """
        if not self.antiguedad_escalones:
            return self.antiguedad_pct_por_anio * Decimal(anios)

        porcentaje = Decimal("0")
        for desde, fraccion in sorted(self.antiguedad_escalones, key=lambda x: x[0]):
            if anios < desde:
                break
            porcentaje = fraccion
        return porcentaje

    def base_referencia(self, codigo: str) -> Decimal:
        for clave, importe in self.bases_referencia:
            if clave == codigo:
                return Decimal(importe)
        raise ValueError(f"Falta la base de referencia convencional {codigo}")