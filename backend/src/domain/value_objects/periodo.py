"""Value object Periodo (YYYY-MM) para la liquidación."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Periodo:
    anio: int
    mes: int

    def __post_init__(self) -> None:
        if not (1 <= self.mes <= 12):
            raise ValueError(f"Mes fuera de rango: {self.mes}")
        if self.anio < 1900:
            raise ValueError(f"Año inválido: {self.anio}")

    @classmethod
    def desde_texto(cls, texto: str) -> "Periodo":
        anio_s, mes_s = texto.split("-")
        return cls(int(anio_s), int(mes_s))

    def primer_dia(self) -> date:
        return date(self.anio, self.mes, 1)

    def ultimo_dia_del_anio(self) -> date:
        """Usado por LCT art. 151: la antigüedad de vacaciones se computa al 31/12."""
        return date(self.anio, 12, 31)

    def __str__(self) -> str:
        return f"{self.anio:04d}-{self.mes:02d}"
