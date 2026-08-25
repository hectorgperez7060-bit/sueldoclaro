"""Entidad y validaciones de novedades mensuales, independientes de la UI."""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
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
    feriados_uocra_detalle: tuple[dict, ...] = ()
    fcl_criterio_aniversario: Optional[str] = None
    fcl_aprobado_por: Optional[str] = None
    fcl_fundamento: Optional[str] = None
    base_contribucion_uocra_mes_anterior: Optional[Decimal] = None
    horas_extra_uocra_detalle: tuple[dict, ...] = ()
    horas_extra_uocra_acumuladas_anio: Decimal = Decimal("0")
    horas_hormigon_manual_uocra: Decimal = Decimal("0")
    horas_altura_uocra: Decimal = Decimal("0")
    altura_metros_uocra: Optional[Decimal] = None
    camioneros_detalle: dict = field(default_factory=dict)

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
        fechas_feriado = set()
        trabajados_detalle = 0
        no_trabajados_detalle = 0
        for detalle in self.feriados_uocra_detalle:
            try:
                fecha = date.fromisoformat(str(detalle["fecha"]))
                trabajado = detalle["trabajado"]
                requisito = detalle["cumple_requisito_art168"]
                horas = Decimal(str(detalle["horas_jornada_anterior"]))
                accesorios = Decimal(str(detalle.get("remuneraciones_accesorias", 0)))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("Cada feriado UOCRA debe tener fecha, condición, horas y accesorios válidos") from exc
            if fecha.year != periodo.anio or fecha.month != periodo.mes:
                raise ValueError("La fecha del feriado UOCRA debe pertenecer al período")
            if fecha in fechas_feriado:
                raise ValueError("No se puede informar dos veces el mismo feriado UOCRA")
            fechas_feriado.add(fecha)
            if not isinstance(trabajado, bool) or not isinstance(requisito, bool):
                raise ValueError("Trabajado y requisito del feriado deben informarse como sí o no")
            if not Decimal("0") < horas <= Decimal("9"):
                raise ValueError("Las horas de jornada anterior del feriado deben ser mayores que 0 y no superar 9")
            if accesorios < 0:
                raise ValueError("Los accesorios de la jornada anterior no pueden ser negativos")
            trabajados_detalle += int(trabajado)
            no_trabajados_detalle += int(not trabajado)
        if self.feriados_uocra_detalle and (
            trabajados_detalle != self.feriados_trabajados
            or no_trabajados_detalle != self.feriados_no_trabajados
        ):
            raise ValueError("El detalle UOCRA debe coincidir con las cantidades totales de feriados")

        criterio_fcl = self.fcl_criterio_aniversario
        campos_fcl = (criterio_fcl, self.fcl_aprobado_por, self.fcl_fundamento)
        if any(valor not in (None, "") for valor in campos_fcl):
            if criterio_fcl not in {"MES_COMPLETO_12", "MES_COMPLETO_8", "PRORRATEO_DIAS"}:
                raise ValueError("Criterio del Fondo de Cese inválido")
            if not (self.fcl_aprobado_por or "").strip() or not (self.fcl_fundamento or "").strip():
                raise ValueError("El criterio del Fondo de Cese requiere profesional y fundamento")
        if (
            self.base_contribucion_uocra_mes_anterior is not None
            and Decimal(str(self.base_contribucion_uocra_mes_anterior)) < 0
        ):
            raise ValueError("La base UOCRA del mes anterior no puede ser negativa")
        if not Decimal("0") <= Decimal(str(self.horas_extra_uocra_acumuladas_anio)) <= Decimal("200"):
            raise ValueError("El acumulado anual UOCRA debe estar entre 0 y 200 horas")
        if Decimal(str(self.horas_hormigon_manual_uocra)) < 0 or Decimal(str(self.horas_altura_uocra)) < 0:
            raise ValueError("Las horas de adicionales UOCRA no pueden ser negativas")
        if self.altura_metros_uocra is not None and Decimal(str(self.altura_metros_uocra)) < 0:
            raise ValueError("La altura UOCRA no puede ser negativa")
        if Decimal(str(self.horas_altura_uocra)) > 0 and self.altura_metros_uocra is None:
            raise ValueError("Las horas en altura requieren informar metros")
        if self.camioneros_detalle:
            from domain.payroll_engine.camioneros import novedades_camioneros_desde_dict

            novedades_camioneros_desde_dict(self.camioneros_detalle)
        total_extra_detalle = Decimal("0")
        for detalle in self.horas_extra_uocra_detalle:
            try:
                fecha_extra = date.fromisoformat(str(detalle["fecha"]))
                inicio = Decimal(str(detalle["hora_inicio"]))
                horas = Decimal(str(detalle["horas"]))
                es_feriado = detalle.get("es_feriado", False)
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("Cada hora extra UOCRA debe tener fecha, inicio y duración válidos") from exc
            if fecha_extra.year != periodo.anio or fecha_extra.month != periodo.mes:
                raise ValueError("La fecha de la hora extra UOCRA debe pertenecer al período")
            if not Decimal("0") <= inicio < Decimal("24") or horas <= 0 or inicio + horas > 24:
                raise ValueError("El horario extra UOCRA es inválido")
            if not isinstance(es_feriado, bool):
                raise ValueError("La condición de feriado debe informarse como sí o no")
            total_extra_detalle += horas
        if self.horas_extra_uocra_detalle and total_extra_detalle != (
            Decimal(str(self.horas_extra_50)) + Decimal(str(self.horas_extra_100))
        ):
            raise ValueError("El detalle UOCRA debe coincidir con el total de horas extra")

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
            "feriados_uocra_detalle": list(self.feriados_uocra_detalle),
            "fcl_criterio_aniversario": self.fcl_criterio_aniversario,
            "fcl_aprobado_por": (self.fcl_aprobado_por or "").strip() or None,
            "fcl_fundamento": (self.fcl_fundamento or "").strip() or None,
            "base_contribucion_uocra_mes_anterior": self.base_contribucion_uocra_mes_anterior,
            "horas_extra_uocra_detalle": list(self.horas_extra_uocra_detalle),
            "horas_extra_uocra_acumuladas_anio": Decimal(str(self.horas_extra_uocra_acumuladas_anio)),
            "horas_hormigon_manual_uocra": Decimal(str(self.horas_hormigon_manual_uocra)),
            "horas_altura_uocra": Decimal(str(self.horas_altura_uocra)),
            "altura_metros_uocra": self.altura_metros_uocra,
            "camioneros_detalle": dict(self.camioneros_detalle),
        }
