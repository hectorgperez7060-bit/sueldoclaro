"""Motor de liquidación puro.

100% dominio: sin BD, sin FastAPI, sin WeasyPrint. Recibe entidades y
parámetros; devuelve un ``ResultadoLiquidacion``. Todo importe es ``Decimal``
vía ``Dinero`` y se redondea (ROUND_HALF_UP, 2 decimales) solo en el importe
final de cada concepto.

Estrategias por amparo (sección 5.4 del prompt): cada concepto afectado por la
reforma declara dos reglas —``regla_ley_27802`` y ``regla_previa``— y el
``AmparoSet`` decide cuál se aplica según el CCT y el período. El concepto
resultante registra qué régimen se usó, para trazabilidad ante inspección.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

from ..entities.concepto import Concepto, Regimen, TipoConcepto
from ..entities.empleado import Empleado
from ..entities.liquidacion import ResultadoLiquidacion
from ..entities.parametros import AmparoSet, EscalaSalarial, ParametroSet
from ..value_objects.dinero import Dinero
from ..value_objects.periodo import Periodo
from .config import CctConfig


@dataclass(frozen=True)
class Novedades:
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    # Para SAC: mejor remuneración mensual devengada del semestre y días trabajados.
    mejor_remuneracion_semestre: Dinero = None  # type: ignore[assignment]
    dias_trabajados_semestre: int = 181
    # Para vacaciones: remuneración habitual del mes.
    remuneracion_habitual: Dinero = None  # type: ignore[assignment]


# Concepto interno afectado por el amparo FAECYS/Comercio (art. 131 Ley 27.802).
_CONCEPTO_MODERNIZACION = "APORTE_MODERNIZACION"


def _desc_nr(codigo: str) -> str:
    """Descripción legible de un concepto no remunerativo de convenio (solo display)."""
    prefijos = {
        "COMERCIO_NR": "Acuerdo no remunerativo",
        "COMERCIO_BONO": "Suma no remun. única (Revisión 2026)",
        "SANIDAD_SUMA_NR": "Suma no remunerativa (acuerdo FATSA)",
        "SANIDAD_DIA": "Día de la Sanidad (pago único)",
    }
    for pref, desc in prefijos.items():
        if codigo.startswith(pref):
            return desc
    return codigo


class MotorLiquidacion:
    def __init__(
        self,
        parametros: ParametroSet,
        amparos: AmparoSet,
    ) -> None:
        self._p = parametros
        self._amparos = amparos

    # ------------------------------------------------------------------ #
    # Haberes remunerativos
    # ------------------------------------------------------------------ #
    def _basico(self, empleado: Empleado, escala: EscalaSalarial) -> Dinero:
        """Básico de escala, o el pactado si es mayor."""
        if empleado.remuneracion_pactada and empleado.remuneracion_pactada > escala.basico:
            return empleado.remuneracion_pactada.redondear()
        return escala.basico.redondear()

    def _antiguedad(self, basico: Dinero, anios: int, cct: CctConfig) -> Dinero:
        pct = cct.antiguedad_pct_por_anio * Decimal(anios)
        return basico.porcentaje(pct).redondear()

    def _presentismo(self, basico: Dinero, antiguedad: Dinero, cct: CctConfig) -> Dinero:
        base = basico + antiguedad
        return base.dividir(cct.presentismo_divisor).redondear()

    def _valor_hora(self, basico: Dinero, antiguedad: Dinero, cct: CctConfig) -> Dinero:
        return (basico + antiguedad).dividir(cct.divisor_horas)  # sin redondear (intermedio)

    # ------------------------------------------------------------------ #
    # Liquidación mensual
    # ------------------------------------------------------------------ #
    def liquidar_mensual(
        self,
        empleado: Empleado,
        periodo: Periodo,
        escala: EscalaSalarial,
        cct: CctConfig,
        novedades: Novedades = Novedades(),
        a_fecha: date = None,  # type: ignore[assignment]
    ) -> ResultadoLiquidacion:
        fecha_calculo = a_fecha or date(periodo.anio, periodo.mes, 28)
        anios = empleado.antiguedad_anios(fecha_calculo)
        conceptos: List[Concepto] = []

        basico = self._basico(empleado, escala)
        # Jornada parcial (LCT art. 92 ter): el básico se prorratea por la
        # proporción de jornada; antigüedad, presentismo, aportes y
        # contribuciones escalan en cascada porque derivan del básico.
        desc_basico = "Sueldo básico"
        if empleado.proporcion_jornada != Decimal("1"):
            basico = basico.porcentaje(empleado.proporcion_jornada).redondear()
            desc_basico = f"Sueldo básico (jornada {empleado.proporcion_jornada})"
        conceptos.append(Concepto("BASICO", desc_basico, TipoConcepto.REMUNERATIVO, basico))

        # ----- Conceptos NO remunerativos del convenio (data-driven por incidencias) -----
        # El motor NO conoce el convenio: por cada concepto lee 'incidencias'
        # (qué bases integra y qué aportes dispara). Ver ParametroSet.conceptos_convenio.
        nr: List[tuple] = []  # (importe, incidencias)
        for p in self._p.conceptos_convenio(cct.cct_numero):
            imp = Dinero(p.valor)
            if empleado.proporcion_jornada != Decimal("1"):
                imp = imp.porcentaje(empleado.proporcion_jornada)
            imp = imp.redondear()
            nr.append((imp, p.incidencias or {}))
            conceptos.append(Concepto(p.codigo, _desc_nr(p.codigo),
                                      TipoConcepto.NO_REMUNERATIVO, imp))

        def _nr(flag: str) -> Dinero:
            total = Dinero.cero()
            for imp, inc in nr:
                if inc.get(flag):
                    total = total + imp
            return total

        # Antigüedad: base = básico + NR que integran antigüedad
        base_antig = (basico + _nr("integra_antiguedad")).redondear()
        antiguedad = base_antig.porcentaje(cct.antiguedad_pct_por_anio * Decimal(anios)).redondear()
        conceptos.append(
            Concepto("ANTIGUEDAD", f"Antigüedad ({anios} años)", TipoConcepto.REMUNERATIVO,
                     antiguedad, cantidad=Decimal(anios))
        )

        # Presentismo: base = básico + NR que integran presentismo + antigüedad
        if cct.aplica_presentismo:
            base_pres = (basico + _nr("integra_presentismo") + antiguedad).redondear()
            presentismo = base_pres.dividir(cct.presentismo_divisor).redondear()
            conceptos.append(
                Concepto("PRESENTISMO", "Presentismo", TipoConcepto.REMUNERATIVO, presentismo)
            )

        # Horas extra (valor hora sobre básico + antigüedad)
        if novedades.horas_extra_50 > 0:
            vh = self.
