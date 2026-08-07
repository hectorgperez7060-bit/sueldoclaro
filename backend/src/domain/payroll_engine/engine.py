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

        antiguedad = self._antiguedad(basico, anios, cct)
        conceptos.append(
            Concepto("ANTIGUEDAD", f"Antigüedad ({anios} años)", TipoConcepto.REMUNERATIVO,
                     antiguedad, cantidad=Decimal(anios))
        )

        if cct.aplica_presentismo:
            presentismo = self._presentismo(basico, antiguedad, cct)
            conceptos.append(
                Concepto("PRESENTISMO", "Presentismo", TipoConcepto.REMUNERATIVO, presentismo)
            )

        # Horas extra
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

        # ----- Sumas NO remunerativas propias del gremio (paritarias) -----
        # Van antes del cálculo de la base: no integran la base de aportes.
        for c in self._sumas_no_rem_gremio(empleado, periodo):
            conceptos.append(c)

        # Base remunerativa = suma de conceptos remunerativos (ya redondeados)
        base = Dinero.cero()
        for c in conceptos:
            if c.tipo == TipoConcepto.REMUNERATIVO:
                base = base + c.importe
        base = base.redondear()

        # Base imponible con tope SIPA (seguridad social)
        tope = self._p.valor_ars("TOPE_SIPA") if self._p.existe("TOPE_SIPA") else None
        base_sipa = Dinero.minimo(base, tope) if tope else base

        # ----- Deducciones del trabajador (todas desde parametro_legal) -----
        conceptos.append(self._deduccion("APORTE_JUBILACION", "Jubilación (11%)", base_sipa))
        conceptos.append(self._deduccion("APORTE_LEY19032", "Ley 19.032 - INSSJP (3%)", base_sipa))
        conceptos.append(self._deduccion("APORTE_OBRA_SOCIAL", "Obra social (3%)", base_sipa))

        if cct.aplica_cuota_sindical and empleado.afiliado_sindicato:
            # Cuota propia del convenio si está definida; si no, parámetro global.
            pct = cct.cuota_sindical_pct if cct.cuota_sindical_pct is not None \
                else self._p.fraccion("CUOTA_SINDICAL")
            imp = base.porcentaje(pct).redondear()
            conceptos.append(Concepto("CUOTA_SINDICAL", "Cuota sindical",
                                      TipoConcepto.DEDUCCION, imp))

        # ----- Aporte solidario UOCRA 2% (solo NO afiliados, CCT 76/75) -----
        # 2º tramo paritario CCT 76/75: 2% sobre salarios sujetos a aportes,
        # jun–ago 2026, únicamente trabajadores no afiliados. El parámetro ya
        # viene filtrado por período, así que basta con que exista.
        if (empleado.cct_numero == "76/75" and not empleado.afiliado_sindicato
                and self._p.existe("UOCRA_APORTE_SOLIDARIO_76/75")):
            pct = self._p.fraccion("UOCRA_APORTE_SOLIDARIO_76/75")
            imp = base.porcentaje(pct).redondear()
            conceptos.append(Concepto(
                "APORTE_SOLIDARIO_UOCRA",
                "Aporte solidario UOCRA 2% (no afiliado)",
                TipoConcepto.DEDUCCION, imp,
            ))

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

    # Sumas no remunerativas por gremio (paritarias verificadas en la BD).
    _SUMA_NR_SANIDAD = ("SANIDAD_SUMA_NR_JUN_JUL", "SANIDAD_SUMA_NR_AGO")
    _DIA_SANIDAD = {
        "122/75": "SANIDAD_DIA_SANIDAD_122/75",
        "108/75": "SANIDAD_DIA_SANIDAD_108/75",
    }

    def _sumas_no_rem_gremio(self, empleado: Empleado, periodo: Periodo) -> List[Concepto]:
        """Conceptos no remunerativos propios del convenio, según el período.

        Sanidad (FATSA, CCT 108/75 y 122/75): suma no remunerativa mensual y,
        en septiembre, la asignación por el Día de la Sanidad (pago único).
        Todos los importes salen de ``parametro_legal`` (ya filtrado por período).
        """
        out: List[Concepto] = []
        cct = empleado.cct_numero
        if cct in ("108/75", "122/75"):
            prop = empleado.proporcion_jornada
            for cod in self._SUMA_NR_SANIDAD:
                if self._p.existe(cod):
                    val = self._p.valor_ars(cod).porcentaje(prop).redondear()
                    out.append(Concepto(cod, "Suma no remunerativa (acuerdo FATSA)",
                                        TipoConcepto.NO_REMUNERATIVO, val))
                    break
            cod_dia = self._DIA_SANIDAD.get(cct)
            if cod_dia and self._p.existe(cod_dia):
                val = self._p.valor_ars(cod_dia).redondear()
                out.append(Concepto(cod_dia, "Asignación Día de la Sanidad (pago único)",
                                    TipoConcepto.NO_REMUNERATIVO, val))
        return out

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
