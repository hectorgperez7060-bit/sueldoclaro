
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


def _desc_ded(codigo: str) -> str:
    """Descripción legible de una deducción porcentual de convenio (solo display)."""
    prefijos = {
        "APORTE_SINDICAL_ART100": "Aporte sindical 2% (art. 100 CCT)",
        "APORTE_FAECYS": "Aporte FAECYS 0,5% (art. 100)",
        "CUOTA_SINDICAL_ART101": "Cuota sindical (art. 101, afiliados)",
        "APORTE_SOLIDARIO": "Aporte solidario (no afiliado)",
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
            vh = self._valor_hora(basico, antiguedad, cct)
            imp = vh.multiplicar(Decimal("1.5")).multiplicar(novedades.horas_extra_50).redondear()
            conceptos.append(
                Concepto("HORAS_EXTRA_50", "Horas extra al 50%", TipoConcepto.REMUNERATIVO,
                         imp, cantidad=novedades.horas_extra_50)
            )
        if novedades.horas_extra_100 > 0:
            vh = self._valor_hora(basico, antiguedad, cct)
            imp = vh.multiplicar(Decimal("2")).multiplicar(novedades.horas_extra_100).redondear()
            conceptos.append(
                Concepto("HORAS_EXTRA_100", "Horas extra al 100%", TipoConcepto.REMUNERATIVO,
                         imp, cantidad=novedades.horas_extra_100)
            )

        # Base remunerativa = suma de conceptos remunerativos
        base = Dinero.cero()
        for c in conceptos:
            if c.tipo == TipoConcepto.REMUNERATIVO:
                base = base + c.importe
        base = base.redondear()

        # Bases de aportes (data-driven): remunerativos + NR que disparan cada aporte
        base_jubilacion = (base + _nr("aporte_jubilacion")).redondear()
        base_obra_social = (base + _nr("aporte_obra_social")).redondear()
        base_sindical = (base + _nr("aporte_sindicato")).redondear()

        # Tope SIPA sobre la seguridad social
        tope = self._p.valor_ars("TOPE_SIPA") if self._p.existe("TOPE_SIPA") else None
        base_jub_t = Dinero.minimo(base_jubilacion, tope) if tope else base_jubilacion
        base_os_t = Dinero.minimo(base_obra_social, tope) if tope else base_obra_social

        # ----- Deducciones del trabajador (cada una sobre SU base) -----
        conceptos.append(self._deduccion("APORTE_JUBILACION", "Jubilación (11%)", base_jub_t))
        conceptos.append(self._deduccion("APORTE_LEY19032", "Ley 19.032 - INSSJP (3%)", base_jub_t))
        conceptos.append(self._deduccion("APORTE_OBRA_SOCIAL", "Obra social (3%)", base_os_t))

        if cct.aplica_cuota_sindical and empleado.afiliado_sindicato:
            # Cuota propia del convenio si está definida; si no, parámetro global.
            pct = cct.cuota_sindical_pct if cct.cuota_sindical_pct is not None \
                else self._p.fraccion("CUOTA_SINDICAL")
            imp = base_sindical.porcentaje(pct).redondear()
            conceptos.append(Concepto("CUOTA_SINDICAL", "Cuota sindical",
                                      TipoConcepto.DEDUCCION, imp))

        # ----- Deducciones porcentuales del convenio (aportes/cuotas, data-driven) -----
        # Cada una lleva su condición de aplicación en 'ambito':
        #   ded_todos  -> a todo trabajador comprendido (p.ej. aporte art.100, FAECYS)
        #   ded_afil   -> solo afiliados (p.ej. cuota art.101)
        #   ded_noafil -> solo no afiliados (p.ej. aporte solidario UOCRA)
        # Base: la base sindical (remunerativo + NR cuya incidencia lo dispare).
        for d in self._p.deducciones_convenio(cct.cct_numero):
            aplica = (d.ambito == "ded_todos"
                      or (d.ambito == "ded_afil" and empleado.afiliado_sindicato)
                      or (d.ambito == "ded_noafil" and not empleado.afiliado_sindicato))
            if aplica:
                imp = base_sindical.porcentaje(d.valor).redondear()
                conceptos.append(Concepto(d.codigo, _desc_ded(d.codigo),
                                          TipoConcepto.DEDUCCION, imp))

        # ----- Concepto con estrategia por amparo (Ley 27.802 art. 131) -----
        conceptos.append(self._aporte_modernizacion(empleado, periodo, base))

        # ----- Contribuciones patronales (desglose Anexo III) -----
        conceptos.append(self._contribucion("CONTRIB_JUBILACION", "Contrib. jubilación (18%)", base))
        conceptos.append(self._contribucion("CONTRIB_OBRA_SOCIAL", "Contrib. obra social (6%)", base))
        if self._p.existe("CONTRIB_INSSJP"):
            conceptos.append(self._contribucion("CONTRIB_INSSJP", "Contrib. INSSJP", base))
        if self._p.existe("CONTRIB_ASIG_FAM"):
            conceptos.append(self._contribucion("CONTRIB_ASIG_FAM", "Asignaciones familiares", base))

        return ResultadoLiquidacion(empleado.cuil.valor, periodo, "mensual", conceptos)

    def _deduccion(self, codigo: str, descripcion: str, base: Dinero) -> Concepto:
        imp = base.porcentaje(self._p.fraccion(codigo)).redondear()
        return Concepto(codigo, descripcion, TipoConcepto.DEDUCCION, imp)

    def _contribucion(self, codigo: str, descripcion: str, base: Dinero) -> Concepto:
        imp = base.porcentaje(self._p.fraccion(codigo)).redondear()
        return Concepto(codigo, descripcion, TipoConcepto.CONTRIBUCION, imp)

    def _aporte_modernizacion(
        self, empleado: Empleado, periodo: Periodo, base: Dinero
    ) -> Concepto:
        """Aporte creado por el art. 131 de la Ley 27.802.

        - ``regla_ley_27802``: se retiene ``APORTE_MODERNIZACION`` % de la base.
        - ``regla_previa``: no existía => 0 (reactivada por amparo FAECYS/Comercio).
        """
        amparo = self._amparos.amparo_vigente(
            empleado.cct_numero, _CONCEPTO_MODERNIZACION, periodo
        )
        if amparo is not None:
            # regla_previa: el aporte no corre
            return Concepto(
                _CONCEPTO_MODERNIZACION,
                "Aporte modernización (SUSPENDIDO por amparo)",
                TipoConcepto.DEDUCCION,
                Dinero.cero().redondear(),
                regimen=Regimen.PREVIA,
                articulo_amparo=amparo.articulo_suspendido,
            )
        # regla_ley_27802
        imp = base.porcentaje(self._p.fraccion(_CONCEPTO_MODERNIZACION)).redondear()
        return Concepto(
            _CONCEPTO_MODERNIZACION,
            "Aporte modernización (Ley 27.802 art. 131)",
            TipoConcepto.DEDUCCION,
            imp,
            regimen=Regimen.LEY_27802,
        )

    # ------------------------------------------------------------------ #
    # SAC (medio aguinaldo)
    # ------------------------------------------------------------------ #
    def liquidar_sac(
        self,
        empleado: Empleado,
        periodo: Periodo,
        mejor_remuneracion_semestre: Dinero,
        dias_trabajados_semestre: int = 181,
    ) -> ResultadoLiquidacion:
        """SAC = 50% de la mejor remuneración del semestre, proporcional a días."""
        proporcion = Decimal(dias_trabajados_semestre) / Decimal(181)
        bruto = mejor_remuneracion_semestre.multiplicar(Decimal("0.5")).multiplicar(proporcion)
        bruto = bruto.redondear()
        conceptos: List[Concepto] = [
            Concepto("SAC", "SAC (50% mejor remuneración)", TipoConcepto.REMUNERATIVO, bruto)
        ]
        # Aportes sobre el SAC (seguridad social)
        conceptos.append(self._deduccion("APORTE_JUBILACION", "Jubilación (11%)", bruto))
        conceptos.append(self._deduccion("APORTE_LEY19032", "Ley 19.032 - INSSJP (3%)", bruto))
        conceptos.append(self._deduccion("APORTE_OBRA_SOCIAL", "Obra social (3%)", bruto))
        return ResultadoLiquidacion(empleado.cuil.valor, periodo, "sac", conceptos)

    # ------------------------------------------------------------------ #
    # Vacaciones
    # ------------------------------------------------------------------ #
    @staticmethod
    def dias_vacaciones(anios: int) -> int:
        """LCT art. 150. Antigüedad computada al 31/12 (art. 151)."""
        if anios < 5:
            return 14
        if anios < 10:
            return 21
        if anios < 20:
            return 28
        return 35

    def liquidar_vacaciones(
        self,
        empleado: Empleado,
        periodo: Periodo,
        remuneracion_habitual: Dinero,
    ) -> ResultadoLiquidacion:
        anios = empleado.antiguedad_anios(periodo.ultimo_dia_del_anio())
        dias = self.dias_vacaciones(anios)
        valor_dia = remuneracion_habitual.dividir(Decimal("25"))  # LCT: /25
        imp = valor_dia.multiplicar(Decimal(dias)).redondear()
        conceptos = [
            Concepto("VACACIONES", f"Vacaciones ({dias} días)", TipoConcepto.REMUNERATIVO,
                     imp, cantidad=Decimal(dias))
        ]
        return ResultadoLiquidacion(empleado.cuil.valor, periodo, "vacaciones", conceptos)
