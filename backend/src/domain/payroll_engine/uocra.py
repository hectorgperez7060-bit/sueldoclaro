"""Núcleo quincenal UOCRA, todavía desacoplado del recibo productivo.

No contiene escalas ni fechas: recibe la escala versionada y los hechos de
cada quincena. El jornal usa el total de zona; la asistencia, el básico puro.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from domain.entities.parametros import EscalaSalarial
from domain.value_objects.dinero import Dinero


PORCENTAJE_ASISTENCIA = Decimal("0.20")


@dataclass(frozen=True)
class HechosQuincenalesUocra:
    horas_q1: Optional[Decimal]
    horas_q2: Optional[Decimal]
    asistencia_q1: Optional[bool]
    asistencia_q2: Optional[bool]


@dataclass(frozen=True)
class ResultadoQuincenaUocra:
    numero: int
    horas: Optional[Decimal]
    basico: Dinero
    asistencia: Dinero

    @property
    def remunerativo(self) -> Dinero:
        return (self.basico + self.asistencia).redondear()


@dataclass(frozen=True)
class ResultadoBaseUocra:
    primera: ResultadoQuincenaUocra
    segunda: ResultadoQuincenaUocra

    @property
    def basico_total(self) -> Dinero:
        return (self.primera.basico + self.segunda.basico).redondear()

    @property
    def asistencia_total(self) -> Dinero:
        return (self.primera.asistencia + self.segunda.asistencia).redondear()

    @property
    def remunerativo_total(self) -> Dinero:
        return (self.basico_total + self.asistencia_total).redondear()


def _validar_escala(escala: EscalaSalarial) -> None:
    if escala.unidad_escala not in {"HORA", "MENSUAL"}:
        raise ValueError("La escala UOCRA debe declarar unidad HORA o MENSUAL")
    if escala.basico_puro is None:
        raise ValueError("La escala UOCRA no informa el básico puro para calcular asistencia")


def _validar_hechos(escala: EscalaSalarial, hechos: HechosQuincenalesUocra) -> None:
    if hechos.asistencia_q1 is None or hechos.asistencia_q2 is None:
        raise ValueError("Debe informarse la asistencia perfecta de ambas quincenas")
    if escala.unidad_escala == "HORA":
        if hechos.horas_q1 is None or hechos.horas_q2 is None:
            raise ValueError("Debe informarse las horas normales de ambas quincenas")
        for horas in (hechos.horas_q1, hechos.horas_q2):
            if not Decimal("0") <= Decimal(horas) <= Decimal("200"):
                raise ValueError("Las horas normales de cada quincena deben estar entre 0 y 200")
    elif hechos.horas_q1 is not None or hechos.horas_q2 is not None:
        raise ValueError("El Sereno mensualizado no debe informar horas normales quincenales")


def calcular_base_quincenal(
    escala: EscalaSalarial,
    hechos: HechosQuincenalesUocra,
) -> ResultadoBaseUocra:
    """Calcula básico y art. 52; no calcula extras, feriados ni Fondo de Cese."""
    _validar_escala(escala)
    _validar_hechos(escala, hechos)

    resultados = []
    for numero, horas, asistencia in (
        (1, hechos.horas_q1, hechos.asistencia_q1),
        (2, hechos.horas_q2, hechos.asistencia_q2),
    ):
        if escala.unidad_escala == "HORA":
            basico = escala.basico.multiplicar(Decimal(horas)).redondear()
            base_asistencia = escala.basico_puro.multiplicar(Decimal(horas))
        else:
            basico = escala.basico.dividir(Decimal("2")).redondear()
            base_asistencia = escala.basico_puro.dividir(Decimal("2"))
        premio = (
            base_asistencia.porcentaje(PORCENTAJE_ASISTENCIA).redondear()
            if asistencia else Dinero.cero()
        )
        resultados.append(ResultadoQuincenaUocra(numero, horas, basico, premio))
    return ResultadoBaseUocra(resultados[0], resultados[1])
