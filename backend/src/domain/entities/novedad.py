"""Entidad y validaciones de novedades mensuales, independientes de la UI."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from decimal import Decimal

from domain.value_objects.periodo import Periodo


@dataclass(frozen=True)
class DatosNovedadMensual:
    periodo: str
    dias_trabajados: int = 0
    faltas_justificadas: int = 0
    faltas_injustificadas: int = 0
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    licencias: int = 0
    vacaciones: int = 0
    premios: Decimal = Decimal("0")
    tipo_premio: str = "pendiente"
    descuentos_adicionales: Decimal = Decimal("0")
    observaciones: str = ""

    def __post_init__(self) -> None:
        try:
            periodo = Periodo.desde_texto(self.periodo)
        except (TypeError, ValueError) as exc:
            raise ValueError("El período debe tener formato AAAA-MM") from exc
        if str(periodo) != self.periodo:
            raise ValueError("El período debe tener formato AAAA-MM")

        max_dias = calendar.monthrange(periodo.anio, periodo.mes)[1]
        campos_dias = {
            "días trabajados": self.dias_trabajados,
            "faltas justificadas": self.faltas_justificadas,
            "faltas injustificadas": self.faltas_injustificadas,
            "licencias": self.licencias,
            "vacaciones": self.vacaciones,
        }
        for nombre, valor in campos_dias.items():
            if isinstance(valor, bool) or not isinstance(valor, int):
                raise ValueError(f"{nombre.capitalize()} debe ser un número entero")
            if not 0 <= valor <= max_dias:
                raise ValueError(
                    f"{nombre.capitalize()} debe estar entre 0 y {max_dias} para {self.periodo}"
                )

        if sum(campos_dias.values()) > max_dias:
            raise ValueError(
                f"La suma de días informados no puede superar {max_dias} para {self.periodo}"
            )

        for nombre, valor in {
            "horas extra al 50%": self.horas_extra_50,
            "horas extra al 100%": self.horas_extra_100,
            "premios": self.premios,
            "descuentos adicionales": self.descuentos_adicionales,
        }.items():
            if Decimal(str(valor)) < 0:
                raise ValueError(f"{nombre.capitalize()} no puede ser negativo")
        if self.tipo_premio not in {"pendiente", "remunerativo", "no_remunerativo"}:
            raise ValueError("Tipo de premio inválido")
        if self.descuentos_adicionales > 0 and not self.observaciones.strip():
            raise ValueError("Los descuentos adicionales requieren una observación")

    def para_persistir(self) -> dict:
        return {
            "periodo": self.periodo,
            "dias_trabajados": self.dias_trabajados,
            "faltas_justificadas": self.faltas_justificadas,
            "faltas_injustificadas": self.faltas_injustificadas,
            "horas_extra_50": Decimal(str(self.horas_extra_50)),
            "horas_extra_100": Decimal(str(self.horas_extra_100)),
            "licencias": self.licencias,
            "vacaciones": self.vacaciones,
            "premios": Decimal(str(self.premios)),
            "tipo_premio": self.tipo_premio,
            "descuentos_adicionales": Decimal(str(self.descuentos_adicionales)),
            "observaciones": self.observaciones.strip(),
        }
