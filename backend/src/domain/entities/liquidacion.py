"""Resultado de una liquidación: colección de conceptos + totales."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..value_objects.dinero import Dinero
from ..value_objects.periodo import Periodo
from .concepto import Concepto, Regimen, TipoConcepto


@dataclass
class ResultadoLiquidacion:
    empleado_cuil: str
    periodo: Periodo
    tipo: str  # "mensual" | "sac" | "vacaciones"
    conceptos: List[Concepto] = field(default_factory=list)

    def _suma(self, tipo: TipoConcepto) -> Dinero:
        total = Dinero.cero()
        for c in self.conceptos:
            if c.tipo == tipo:
                total = total + c.importe
        return total.redondear()

    @property
    def total_remunerativo(self) -> Dinero:
        return self._suma(TipoConcepto.REMUNERATIVO)

    @property
    def total_no_remunerativo(self) -> Dinero:
        return self._suma(TipoConcepto.NO_REMUNERATIVO)

    @property
    def total_deducciones(self) -> Dinero:
        return self._suma(TipoConcepto.DEDUCCION)

    @property
    def total_contribuciones(self) -> Dinero:
        return self._suma(TipoConcepto.CONTRIBUCION)

    @property
    def bruto(self) -> Dinero:
        return (self.total_remunerativo + self.total_no_remunerativo).redondear()

    @property
    def neto(self) -> Dinero:
        return (self.bruto - self.total_deducciones).redondear()

    def concepto(self, codigo: str) -> Concepto:
        for c in self.conceptos:
            if c.codigo == codigo:
                return c
        raise KeyError(f"Concepto no encontrado: {codigo}")

    def regimenes_aplicados(self) -> List[tuple]:
        """Trazabilidad: (codigo, regimen, articulo) para conceptos afectados."""
        return [
            (c.codigo, c.regimen.value, c.articulo_amparo)
            for c in self.conceptos
            if c.regimen != Regimen.NO_APLICA
        ]
