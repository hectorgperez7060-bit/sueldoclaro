"""Entidad y validaciones de novedades mensuales, independientes de la UI."""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from domain.value_objects.periodo import Periodo


@dataclass(frozen=True)
class DatosNovedadMensual:
    periodo: str
    dias_trabajados: int = 0
    faltas_justificadas: int = 0
    faltas_injustificadas: int = 0
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    feriados_trabajados: int = 0
    feriados_no_trabajados: int = 0
    licencias: int = 0
    vacaciones: int = 0
    premios: Decimal = Decimal("0")
    tipo_premio: str = "pendiente"
    descuentos_adicionales: Decimal = Decimal("0")
    observaciones: str = ""
    adicionales_convencionales: tuple[str, ...] = ()
    cantidades_adicionales: tuple[tuple[str, Decimal], ...] = ()
    horas_normales_q1: Optional[Decimal] = None
    horas_normales_q2: Optional[Decimal] = None
    asistencia_perfecta_q1: Optional[bool] = None
    asistencia_perfecta_q2: Optional[bool] = None
    feriados_habilitados_q1: int = 0
    feriados_habilitados_q2: int = 0

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
        if isinstance(self.feriados_trabajados, bool) or not isinstance(
            self.feriados_trabajados, int
        ):
            raise ValueError("Feriados trabajados debe ser un número entero")
        if not 0 <= self.feriados_trabajados <= max_dias:
            raise ValueError(
                f"Feriados trabajados debe estar entre 0 y {max_dias} para {self.periodo}"
            )
        if isinstance(self.feriados_no_trabajados, bool) or not isinstance(
            self.feriados_no_trabajados, int
        ):
            raise ValueError("Feriados no trabajados debe ser un número entero")
        if not 0 <= self.feriados_no_trabajados <= max_dias:
            raise ValueError(
                f"Feriados no trabajados debe estar entre 0 y {max_dias} para {self.periodo}"
            )
        if self.feriados_trabajados + self.feriados_no_trabajados > max_dias:
            raise ValueError("La cantidad total de feriados informados supera los días del mes")
        for nombre, valor in {
            "Horas normales de la primera quincena": self.horas_normales_q1,
            "Horas normales de la segunda quincena": self.horas_normales_q2,
        }.items():
            if valor is not None and not Decimal("0") <= Decimal(str(valor)) <= Decimal("200"):
                raise ValueError(f"{nombre} debe estar entre 0 y 200")
        for nombre, valor in {
            "Asistencia perfecta de la primera quincena": self.asistencia_perfecta_q1,
            "Asistencia perfecta de la segunda quincena": self.asistencia_perfecta_q2,
        }.items():
            if valor is not None and not isinstance(valor, bool):
                raise ValueError(f"{nombre} debe informarse como sí o no")
        if self.feriados_habilitados_q1 < 0 or self.feriados_habilitados_q2 < 0:
            raise ValueError("Los feriados habilitados por quincena no pueden ser negativos")
        if self.feriados_habilitados_q1 + self.feriados_habilitados_q2 > self.feriados_no_trabajados:
            raise ValueError(
                "Los feriados habilitados por quincena no pueden superar los feriados no trabajados"
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

        codigos = tuple(self.adicionales_convencionales)
        if any(not isinstance(codigo, str) or not codigo.strip() for codigo in codigos):
            raise ValueError("Los adicionales convencionales deben tener un código válido")
        if len(codigos) != len(set(codigos)):
            raise ValueError("No se puede informar dos veces el mismo adicional convencional")
        cantidades = dict(self.cantidades_adicionales)
        if len(cantidades) != len(tuple(self.cantidades_adicionales)):
            raise ValueError("No se puede informar dos veces la cantidad de un adicional")
        cantidades_auxiliares = {
            "HORAS_TOTALES_PERIODO": {"NOCTURNO_VOLUNTARIO", "NOCTURNIDAD"},
        }
        for codigo, cantidad in cantidades.items():
            principales = cantidades_auxiliares.get(codigo, {codigo})
            if not set(codigos).intersection(principales):
                raise ValueError("Toda cantidad debe corresponder a un adicional seleccionado")
            minimo_cero = codigo == "FALLA_CAJA"
            if Decimal(str(cantidad)) < 0 or (not minimo_cero and Decimal(str(cantidad)) == 0):
                raise ValueError("La cantidad de un adicional debe ser mayor que cero")

    def para_persistir(self) -> dict:
        return {
            "periodo": self.periodo,
            "dias_trabajados": self.dias_trabajados,
            "faltas_justificadas": self.faltas_justificadas,
            "faltas_injustificadas": self.faltas_injustificadas,
            "horas_extra_50": Decimal(str(self.horas_extra_50)),
            "horas_extra_100": Decimal(str(self.horas_extra_100)),
            "feriados_trabajados": self.feriados_trabajados,
            "feriados_no_trabajados": self.feriados_no_trabajados,
            "licencias": self.licencias,
            "vacaciones": self.vacaciones,
            "premios": Decimal(str(self.premios)),
            "tipo_premio": self.tipo_premio,
            "descuentos_adicionales": Decimal(str(self.descuentos_adicionales)),
            "observaciones": self.observaciones.strip(),
            "adicionales_convencionales": list(self.adicionales_convencionales),
            "cantidades_adicionales": {
                codigo: str(Decimal(str(cantidad)))
                for codigo, cantidad in self.cantidades_adicionales
            },
            "horas_normales_q1": self.horas_normales_q1,
            "horas_normales_q2": self.horas_normales_q2,
            "asistencia_perfecta_q1": self.asistencia_perfecta_q1,
            "asistencia_perfecta_q2": self.asistencia_perfecta_q2,
            "feriados_habilitados_q1": self.feriados_habilitados_q1,
            "feriados_habilitados_q2": self.feriados_habilitados_q2,
        }
