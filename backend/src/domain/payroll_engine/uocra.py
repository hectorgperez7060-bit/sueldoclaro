"""Núcleo quincenal UOCRA conectado en modo de vista previa segura.

No contiene escalas ni fechas: recibe la escala versionada y los hechos de
cada quincena. El jornal usa el total de zona; la asistencia, el básico puro.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import calendar
from decimal import Decimal
from typing import Optional

from domain.entities.parametros import EscalaSalarial
from domain.entities.concepto import Concepto, TipoConcepto
from domain.entities.liquidacion import ResultadoLiquidacion
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


PORCENTAJE_ASISTENCIA = Decimal("0.20")
CRITERIOS_ANIVERSARIO_FCL = {"MES_COMPLETO_12", "MES_COMPLETO_8", "PRORRATEO_DIAS"}


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
    base_asistencia: Dinero
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


@dataclass(frozen=True)
class ComponentesFondoCese:
    """Bases clasificadas: las exclusiones se conservan para trazabilidad."""
    basico: Dinero
    asistencia: Dinero = Dinero(Decimal("0"))
    adicionales_remunerativos: Dinero = Dinero(Decimal("0"))
    horas_extra_valor_normal: Dinero = Dinero(Decimal("0"))
    sac: Dinero = Dinero(Decimal("0"))
    recargos_legales_horas_extra: Dinero = Dinero(Decimal("0"))
    indemnizaciones: Dinero = Dinero(Decimal("0"))

    @property
    def base_incluida(self) -> Dinero:
        return (
            self.basico + self.asistencia + self.adicionales_remunerativos
            + self.horas_extra_valor_normal
        ).redondear()


@dataclass(frozen=True)
class ResultadoFondoCese:
    porcentaje: Decimal
    base: Dinero
    importe: Dinero
    sac_excluido: Dinero
    recargos_extra_excluidos: Dinero
    indemnizaciones_excluidas: Dinero


@dataclass(frozen=True)
class DecisionProfesionalFcl:
    criterio: str
    aprobado_por: str
    fundamento: str


def resolver_alicuota_fcl(
    fecha_ingreso: date,
    periodo: Periodo,
    decision_aniversario: Optional[DecisionProfesionalFcl] = None,
) -> Decimal:
    """Resuelve tramos claros y bloquea el mes aniversario ambiguo."""
    aniversario = fecha_ingreso.replace(year=fecha_ingreso.year + 1)
    inicio = date(periodo.anio, periodo.mes, 1)
    fin = date(periodo.anio, periodo.mes, calendar.monthrange(periodo.anio, periodo.mes)[1])
    if fin < aniversario:
        return Decimal("0.12")
    if inicio >= aniversario:
        return Decimal("0.08")
    if decision_aniversario is None:
        raise ValueError(
            "El trabajador cumple un año durante el período: falta criterio profesional del Fondo de Cese"
        )
    if decision_aniversario.criterio not in CRITERIOS_ANIVERSARIO_FCL:
        raise ValueError("Criterio profesional inválido para el mes aniversario")
    if not decision_aniversario.aprobado_por.strip() or not decision_aniversario.fundamento.strip():
        raise ValueError("El criterio del mes aniversario requiere profesional y fundamento")
    if decision_aniversario.criterio == "PRORRATEO_DIAS":
        raise ValueError(
            "El prorrateo exige bases devengadas separadas antes y después del aniversario"
        )
    return (
        Decimal("0.12")
        if decision_aniversario.criterio == "MES_COMPLETO_12" else Decimal("0.08")
    )


@dataclass(frozen=True)
class EvaluacionFeriadosUocra:
    informados_no_trabajados: int
    habilitados_q1: int
    habilitados_q2: int
    pendientes_requisito: int
    importe_automatico_habilitado: bool = False


@dataclass(frozen=True)
class FeriadoDetalladoUocra:
    fecha: date
    trabajado: bool
    cumple_requisito_art168: bool
    horas_jornada_anterior: Decimal
    remuneraciones_accesorias_jornada: Dinero = Dinero(Decimal("0"))


@dataclass(frozen=True)
class ResultadoFeriadoUocra:
    fecha: date
    trabajado: bool
    valor_dia: Dinero
    adicional_a_pagar: Dinero
    motivo: str


@dataclass(frozen=True)
class HoraExtraDetalladaUocra:
    fecha: date
    hora_inicio: Decimal
    horas: Decimal
    es_feriado: bool = False


@dataclass(frozen=True)
class ResultadoHorasExtraUocra:
    horas_50: Decimal
    horas_100: Decimal
    valor_normal: Dinero
    recargo_legal: Dinero
    total: Dinero


@dataclass(frozen=True)
class ResultadoAdicionalUocra:
    codigo: str
    descripcion: str
    horas: Decimal
    porcentaje: Decimal
    base_horaria: Dinero
    importe: Dinero


def calcular_adicionales_tarea_uocra(
    escala: EscalaSalarial,
    horas_hormigon_manual: Decimal = Decimal("0"),
    horas_altura: Decimal = Decimal("0"),
    altura_metros: Optional[Decimal] = None,
) -> tuple[ResultadoAdicionalUocra, ...]:
    """Arts. 56/57: solo horas efectivas y básico puro, sin adicional de zona."""
    if escala.unidad_escala != "HORA" or escala.basico_puro is None:
        if Decimal(str(horas_hormigon_manual)) or Decimal(str(horas_altura)):
            raise ValueError("Los adicionales por tarea exigen básico horario puro verificado")
        return ()
    resultados = []
    hormigon = Decimal(str(horas_hormigon_manual))
    altura_horas = Decimal(str(horas_altura))
    if hormigon < 0 or altura_horas < 0:
        raise ValueError("Las horas de adicionales UOCRA no pueden ser negativas")
    if hormigon:
        importe = escala.basico_puro.multiplicar(hormigon).porcentaje(Decimal("0.15")).redondear()
        resultados.append(ResultadoAdicionalUocra(
            "ADIC_HORMIGON_ART56", "Colada manual de hormigón · art. 56",
            hormigon, Decimal("0.15"), escala.basico_puro, importe,
        ))
    if altura_horas:
        if altura_metros is None:
            raise ValueError("Debe informarse la altura en metros")
        metros = Decimal(str(altura_metros))
        if metros < 4:
            raise ValueError("El adicional por altura comienza a los 4 metros")
        if metros == 26:
            raise ValueError("El texto convencional superpone los tramos en 26 metros; requiere criterio profesional")
        porcentaje = Decimal("0.15") if metros < 26 else (
            Decimal("0.20") if metros <= 40 else Decimal("0.25")
        )
        importe = escala.basico_puro.multiplicar(altura_horas).porcentaje(porcentaje).redondear()
        resultados.append(ResultadoAdicionalUocra(
            "ADIC_ALTURA_ART57", f"Trabajo en altura ({metros} m) · art. 57",
            altura_horas, porcentaje, escala.basico_puro, importe,
        ))
    return tuple(resultados)


def calcular_horas_extra_detalladas(
    escala: EscalaSalarial,
    detalles: tuple[HoraExtraDetalladaUocra, ...],
    horas_acumuladas_anteriores_anio: Decimal = Decimal("0"),
) -> ResultadoHorasExtraUocra:
    """Clasifica por fecha/hora, controla 3/30/200 y separa normal de recargo."""
    if escala.unidad_escala != "HORA":
        raise ValueError("Las horas extra del Sereno requieren un divisor horario verificado")
    acumulado = Decimal(str(horas_acumuladas_anteriores_anio))
    if acumulado < 0:
        raise ValueError("El acumulado anual anterior no puede ser negativo")
    por_dia: dict[date, Decimal] = {}
    h50 = Decimal("0")
    h100 = Decimal("0")
    for item in detalles:
        inicio = Decimal(str(item.hora_inicio))
        horas = Decimal(str(item.horas))
        if not Decimal("0") <= inicio < Decimal("24") or horas <= 0:
            raise ValueError("Cada hora extra debe tener inicio válido y duración positiva")
        if inicio + horas > Decimal("24"):
            raise ValueError("Una hora extra no puede atravesar la medianoche; dividila en dos")
        por_dia[item.fecha] = por_dia.get(item.fecha, Decimal("0")) + horas
        if item.es_feriado or item.fecha.weekday() == 6:
            h100 += horas
        elif item.fecha.weekday() == 5:
            antes_13 = max(Decimal("0"), min(inicio + horas, Decimal("13")) - inicio)
            h50 += antes_13
            h100 += horas - antes_13
        else:
            h50 += horas
    if any(total > Decimal("3") for total in por_dia.values()):
        raise ValueError("Las horas extra superan el tope de 3 horas diarias")
    total_horas = h50 + h100
    if total_horas > Decimal("30"):
        raise ValueError("Las horas extra superan el tope de 30 horas mensuales")
    if acumulado + total_horas > Decimal("200"):
        raise ValueError("Las horas extra superan el tope de 200 horas anuales")
    normal = escala.basico.multiplicar(total_horas).redondear()
    recargo = (
        escala.basico.multiplicar(h50).porcentaje(Decimal("0.50"))
        + escala.basico.multiplicar(h100)
    ).redondear()
    return ResultadoHorasExtraUocra(
        h50, h100, normal, recargo, (normal + recargo).redondear()
    )


def calcular_feriados_detallados(
    escala: EscalaSalarial,
    feriados: tuple[FeriadoDetalladoUocra, ...],
) -> tuple[ResultadoFeriadoUocra, ...]:
    """LCT 166/168/169 y 155: valor de la jornada anterior por cada feriado."""
    if escala.unidad_escala != "HORA":
        raise ValueError("Este cálculo detallado corresponde a personal jornalizado por hora")
    resultados = []
    fechas = set()
    for feriado in feriados:
        if feriado.fecha in fechas:
            raise ValueError("No se puede informar dos veces el mismo feriado")
        fechas.add(feriado.fecha)
        horas = Decimal(str(feriado.horas_jornada_anterior))
        if not Decimal("0") < horas <= Decimal("9"):
            raise ValueError("Las horas de la jornada anterior deben ser mayores que 0 y no superar 9")
        valor_dia = (
            escala.basico.multiplicar(horas) + feriado.remuneraciones_accesorias_jornada
        ).redondear()
        if not feriado.trabajado and not feriado.cumple_requisito_art168:
            adicional = Dinero.cero()
            motivo = "No cumple el requisito del art. 168 LCT"
        elif feriado.trabajado:
            adicional = valor_dia
            motivo = "Feriado trabajado: adicional igual al salario normal"
        else:
            adicional = valor_dia
            motivo = "Feriado no trabajado habilitado por art. 168 LCT"
        resultados.append(ResultadoFeriadoUocra(
            feriado.fecha, feriado.trabajado, valor_dia, adicional, motivo
        ))
    return tuple(resultados)


@dataclass(frozen=True)
class TasasAportesUocra:
    jubilacion: Decimal
    inssjp: Decimal
    obra_social_trabajador: Decimal
    seguridad_social_empleador: Decimal
    obra_social_empleador: Decimal
    aporte_solidario_no_afiliado: Decimal
    contribucion_empresaria_uocra: Decimal


@dataclass(frozen=True)
class ResultadoAportesUocra:
    jubilacion: Dinero
    inssjp: Dinero
    obra_social_trabajador: Dinero
    aporte_sindical_trabajador: Dinero
    concepto_sindical: str
    seguridad_social_empleador: Dinero
    obra_social_empleador: Dinero
    contribucion_empresaria_uocra: Dinero
    base_remunerativa_actual: Dinero
    base_contribucion_uocra_mes_anterior: Dinero


def _validar_tasa(nombre: str, valor: Decimal) -> Decimal:
    tasa = Decimal(str(valor))
    if not Decimal("0") <= tasa <= Decimal("1"):
        raise ValueError(f"La tasa {nombre} debe estar entre 0 y 1")
    return tasa


def calcular_aportes_y_contribuciones(
    base_remunerativa_actual: Dinero,
    base_obra_social_actual: Dinero,
    base_contribucion_uocra_mes_anterior: Optional[Dinero],
    tasas: TasasAportesUocra,
    afiliado_sindicato: Optional[bool],
    cuota_sindical_verificada: Optional[Decimal] = None,
) -> ResultadoAportesUocra:
    """Calcula conceptos separados; nunca usa el mes actual como base patronal UOCRA."""
    if afiliado_sindicato is None:
        raise ValueError("Debe informarse la condición de afiliación sindical")
    if base_contribucion_uocra_mes_anterior is None:
        raise ValueError("Falta la base remunerativa del plantel del mes anterior")

    valores = {
        nombre: _validar_tasa(nombre, getattr(tasas, nombre))
        for nombre in tasas.__dataclass_fields__
    }
    if afiliado_sindicato:
        if cuota_sindical_verificada is None:
            raise ValueError("Falta una cuota sindical UOCRA verificada para el afiliado")
        tasa_sindical = _validar_tasa("cuota_sindical_verificada", cuota_sindical_verificada)
        concepto_sindical = "CUOTA_SINDICAL_UOCRA"
    else:
        tasa_sindical = valores["aporte_solidario_no_afiliado"]
        concepto_sindical = "APORTE_SOLIDARIO_UOCRA"

    return ResultadoAportesUocra(
        jubilacion=base_remunerativa_actual.porcentaje(valores["jubilacion"]).redondear(),
        inssjp=base_remunerativa_actual.porcentaje(valores["inssjp"]).redondear(),
        obra_social_trabajador=base_obra_social_actual.porcentaje(
            valores["obra_social_trabajador"]
        ).redondear(),
        aporte_sindical_trabajador=base_remunerativa_actual.porcentaje(
            tasa_sindical
        ).redondear(),
        concepto_sindical=concepto_sindical,
        seguridad_social_empleador=base_remunerativa_actual.porcentaje(
            valores["seguridad_social_empleador"]
        ).redondear(),
        obra_social_empleador=base_obra_social_actual.porcentaje(
            valores["obra_social_empleador"]
        ).redondear(),
        contribucion_empresaria_uocra=base_contribucion_uocra_mes_anterior.porcentaje(
            valores["contribucion_empresaria_uocra"]
        ).redondear(),
        base_remunerativa_actual=base_remunerativa_actual.redondear(),
        base_contribucion_uocra_mes_anterior=base_contribucion_uocra_mes_anterior.redondear(),
    )


def armar_recibo_prueba_uocra(
    empleado_cuil: str,
    periodo: Periodo,
    base: ResultadoBaseUocra,
    fondo_cese: ResultadoFondoCese,
    aportes: ResultadoAportesUocra,
    feriados: tuple[ResultadoFeriadoUocra, ...] = (),
    horas_extra: Optional[ResultadoHorasExtraUocra] = None,
    adicionales_tarea: tuple[ResultadoAdicionalUocra, ...] = (),
) -> ResultadoLiquidacion:
    """Arma un resultado auditable de prueba; no habilita la confirmación productiva."""
    conceptos = [
        Concepto(
            "BASICO_Q1", "Jornal básico · 1.ª quincena", TipoConcepto.REMUNERATIVO,
            base.primera.basico, cantidad=base.primera.horas or Decimal("1"),
            unidad="hora" if base.primera.horas is not None else "media mensualidad",
        ),
        Concepto(
            "ASISTENCIA_Q1", "Asistencia perfecta · 1.ª quincena",
            TipoConcepto.REMUNERATIVO, base.primera.asistencia,
            base_calculo=base.primera.base_asistencia, unidad="20% sobre básico puro",
        ),
        Concepto(
            "BASICO_Q2", "Jornal básico · 2.ª quincena", TipoConcepto.REMUNERATIVO,
            base.segunda.basico, cantidad=base.segunda.horas or Decimal("1"),
            unidad="hora" if base.segunda.horas is not None else "media mensualidad",
        ),
        Concepto(
            "ASISTENCIA_Q2", "Asistencia perfecta · 2.ª quincena",
            TipoConcepto.REMUNERATIVO, base.segunda.asistencia,
            base_calculo=base.segunda.base_asistencia, unidad="20% sobre básico puro",
        ),
        *[
            Concepto(
                f"FERIADO_{feriado.fecha.isoformat()}",
                ("Feriado trabajado" if feriado.trabajado else "Feriado no trabajado")
                + f" · {feriado.fecha:%d/%m/%Y}",
                TipoConcepto.REMUNERATIVO, feriado.adicional_a_pagar,
                base_calculo=feriado.valor_dia, unidad=feriado.motivo,
            )
            for feriado in feriados if feriado.adicional_a_pagar.monto > 0
        ],
        *([] if horas_extra is None or horas_extra.total.monto == 0 else [
            Concepto("HORAS_EXTRA_UOCRA", "Horas extra UOCRA", TipoConcepto.REMUNERATIVO,
                     horas_extra.total, cantidad=horas_extra.horas_50 + horas_extra.horas_100,
                     base_calculo=horas_extra.valor_normal,
                     unidad=f"{horas_extra.horas_50} h al 50% · {horas_extra.horas_100} h al 100%"),
        ]),
        *[
            Concepto(a.codigo, a.descripcion, TipoConcepto.REMUNERATIVO, a.importe,
                     cantidad=a.horas, base_calculo=a.base_horaria,
                     unidad=f"{a.porcentaje * 100}% por hora efectiva")
            for a in adicionales_tarea
        ],
        Concepto("APORTE_JUBILACION", "Jubilación", TipoConcepto.DEDUCCION,
                 aportes.jubilacion, base_calculo=aportes.base_remunerativa_actual,
                 unidad="porcentaje versionado"),
        Concepto("APORTE_LEY19032", "Ley 19.032 - INSSJP", TipoConcepto.DEDUCCION,
                 aportes.inssjp, base_calculo=aportes.base_remunerativa_actual,
                 unidad="porcentaje versionado"),
        Concepto("APORTE_OBRA_SOCIAL", "Obra social", TipoConcepto.DEDUCCION,
                 aportes.obra_social_trabajador,
                 base_calculo=aportes.base_remunerativa_actual,
                 unidad="porcentaje versionado"),
        Concepto(aportes.concepto_sindical, "Aporte sindical UOCRA",
                 TipoConcepto.DEDUCCION, aportes.aporte_sindical_trabajador,
                 base_calculo=aportes.base_remunerativa_actual,
                 unidad="porcentaje versionado", destino_pago="UOCRA"),
        Concepto("CONTRIB_SEGURIDAD_SOCIAL", "Contribuciones patronales seguridad social",
                 TipoConcepto.CONTRIBUCION, aportes.seguridad_social_empleador,
                 base_calculo=aportes.base_remunerativa_actual,
                 unidad="porcentaje versionado"),
        Concepto("CONTRIB_OBRA_SOCIAL", "Contribución patronal obra social",
                 TipoConcepto.CONTRIBUCION, aportes.obra_social_empleador,
                 base_calculo=aportes.base_remunerativa_actual,
                 unidad="porcentaje versionado"),
        Concepto("FONDO_CESE_LABORAL", "Fondo de Cese Laboral",
                 TipoConcepto.CONTRIBUCION, fondo_cese.importe,
                 base_calculo=fondo_cese.base, unidad=f"{fondo_cese.porcentaje * 100}%"),
        Concepto("CONTRIB_EMPRESARIA_UOCRA", "Contribución empresaria UOCRA",
                 TipoConcepto.CONTRIBUCION, aportes.contribucion_empresaria_uocra,
                 base_calculo=aportes.base_contribucion_uocra_mes_anterior,
                 unidad="2% · plantel del mes anterior", destino_pago="UOCRA"),
    ]
    return ResultadoLiquidacion(empleado_cuil, periodo, "mensual_uocra_prueba", conceptos)


def calcular_fondo_cese(
    componentes: ComponentesFondoCese,
    porcentaje: Decimal,
) -> ResultadoFondoCese:
    """Aplica una alícuota versionada; no decide por sí mismo si es 12% u 8%."""
    porcentaje = Decimal(str(porcentaje))
    if porcentaje not in {Decimal("0.12"), Decimal("0.08")}:
        raise ValueError("La alícuota del Fondo de Cese debe estar verificada como 12% u 8%")
    base = componentes.base_incluida
    return ResultadoFondoCese(
        porcentaje=porcentaje,
        base=base,
        importe=base.porcentaje(porcentaje).redondear(),
        sac_excluido=componentes.sac.redondear(),
        recargos_extra_excluidos=componentes.recargos_legales_horas_extra.redondear(),
        indemnizaciones_excluidas=componentes.indemnizaciones.redondear(),
    )


def evaluar_feriados_no_trabajados(
    informados: int,
    habilitados_q1: int,
    habilitados_q2: int,
) -> EvaluacionFeriadosUocra:
    """Registra el test previo; no inventa la fórmula monetaria pendiente."""
    valores = (informados, habilitados_q1, habilitados_q2)
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in valores):
        raise ValueError("Las cantidades de feriados deben ser enteros no negativos")
    habilitados = habilitados_q1 + habilitados_q2
    if habilitados > informados:
        raise ValueError("Los feriados habilitados no pueden superar los informados")
    return EvaluacionFeriadosUocra(
        informados, habilitados_q1, habilitados_q2, informados - habilitados
    )


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
        resultados.append(ResultadoQuincenaUocra(
            numero, horas, basico, base_asistencia.redondear(), premio
        ))
    return ResultadoBaseUocra(resultados[0], resultados[1])
