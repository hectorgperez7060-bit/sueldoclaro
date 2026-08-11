"""Value object monetario.

Regla de oro del proyecto (sección 0.3 del prompt maestro):
- Todo importe usa ``Decimal``, nunca ``float``.
- El redondeo ``ROUND_HALF_UP`` a 2 decimales se aplica SOLO en el resultado
  final de cada concepto, no en los cálculos intermedios.

Por eso ``Dinero`` guarda el monto en precisión completa y expone ``redondear()``
para producir el importe final de línea. Las operaciones aritméticas devuelven
un nuevo ``Dinero`` sin redondear.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Union

DOS_DECIMALES = Decimal("0.01")

Numerico = Union["Dinero", Decimal, int, str]


def _a_decimal(valor: Numerico) -> Decimal:
    if isinstance(valor, Dinero):
        return valor.monto
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, str):
        return Decimal(valor)
    raise TypeError(f"No se puede convertir {type(valor)!r} a Dinero/Decimal")


@dataclass(frozen=True)
class Dinero:
    """Importe monetario en precisión completa (ARS)."""

    monto: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "monto", _a_decimal(self.monto))

    # --- constructores ---
    @classmethod
    def cero(cls) -> "Dinero":
        return cls(Decimal("0"))

    @classmethod
    def de(cls, valor: Numerico) -> "Dinero":
        return cls(_a_decimal(valor))

    # --- aritmética (precisión completa, sin redondear) ---
    def __add__(self, otro: Numerico) -> "Dinero":
        return Dinero(self.monto + _a_decimal(otro))

    __radd__ = __add__

    def __sub__(self, otro: Numerico) -> "Dinero":
        return Dinero(self.monto - _a_decimal(otro))

    def multiplicar(self, factor: Union[Decimal, int, str]) -> "Dinero":
        """Multiplica por un factor escalar (Decimal). Nunca float."""
        if isinstance(factor, float):
            raise TypeError("Prohibido multiplicar Dinero por float; usar Decimal")
        return Dinero(self.monto * Decimal(str(factor)) if not isinstance(factor, Decimal) else self.monto * factor)

    def porcentaje(self, pct: Decimal) -> "Dinero":
        """Aplica un porcentaje expresado como fracción (0.11 = 11%)."""
        if isinstance(pct, float):
            raise TypeError("Prohibido usar float para porcentajes; usar Decimal")
        return Dinero(self.monto * pct)

    def dividir(self, divisor: Union[Decimal, int, str]) -> "Dinero":
        if isinstance(divisor, float):
            raise TypeError("Prohibido dividir Dinero por float; usar Decimal")
        d = divisor if isinstance(divisor, Decimal) else Decimal(str(divisor))
        return Dinero(self.monto / d)

    # --- resultado final de concepto ---
    def redondear(self) -> "Dinero":
        """ROUND_HALF_UP a 2 decimales. Usar solo en el importe final de línea."""
        return Dinero(self.monto.quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP))

    def es_cero(self) -> bool:
        return self.monto == 0

    # --- comparaciones ---
    def __lt__(self, otro: Numerico) -> bool:
        return self.monto < _a_decimal(otro)

    def __le__(self, otro: Numerico) -> bool:
        return self.monto <= _a_decimal(otro)

    def __gt__(self, otro: Numerico) -> bool:
        return self.monto > _a_decimal(otro)

    def __ge__(self, otro: Numerico) -> bool:
        return self.monto >= _a_decimal(otro)

    @staticmethod
    def minimo(a: "Dinero", b: "Dinero") -> "Dinero":
        return a if a.monto <= b.monto else b

    def __str__(self) -> str:
        return f"$ {self.redondear().monto:,.2f}"
