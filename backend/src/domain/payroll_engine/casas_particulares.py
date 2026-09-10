"""Ley 26.844: cálculo mensual para personal de casas particulares.

Los importes no viven en este módulo. La escala (mensual y por hora), la suma
no remunerativa y los importes fijos de ARCA llegan versionados desde la base.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from domain.entities.concepto import Concepto, TipoConcepto
from domain.entities.liquidacion import ResultadoLiquidacion
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


CCT_CASAS_PARTICULARES = "LEY 26844"
CONDICIONES_ARCA = {"ACTIVO", "ADOLESCENTE_16_17", "JUBILADO"}
CLAVES_NOVEDAD_CASAS = {
    "condicion_arca", "horas_normales_mes", "valor_hora_pactado",
}


@dataclass(frozen=True)
class DatosCasasParticulares:
    condicion_arca: str
    horas_normales_mes: Optional[Decimal] = None
    valor_hora_pactado: Optional[Dinero] = None


@dataclass(frozen=True)
class ValoresEscalaCasas:
    mensual: Dinero
    hora: Dinero


@dataclass(frozen=True)
class ImportesArcaCasas:
    aporte_trabajador: Dinero
    contribucion_empleador: Dinero
    art: Dinero


@dataclass(frozen=True)
class ResultadoBaseCasas:
    modalidad: str
    horas_semanales: Decimal
    cantidad: Decimal
    valor_unitario: Dinero
    importe: Dinero


def validar_novedad_casas(datos: dict) -> dict:
    if not isinstance(datos, dict):
        raise ValueError("El detalle de Casas Particulares debe ser un objeto")
    desconocidas = set(datos) - CLAVES_NOVEDAD_CASAS
    if desconocidas:
        raise ValueError(
            "Campos de Casas Particulares desconocidos: " + ", ".join(sorted(desconocidas))
        )
    condicion = str(datos.get("condicion_arca") or "").strip().upper()
    if condicion not in CONDICIONES_ARCA:
        raise ValueError("Elegí la condición ARCA: activo, adolescente de 16/17 o jubilado")
    salida: dict = {"condicion_arca": condicion}
    for campo in ("horas_normales_mes", "valor_hora_pactado"):
        valor = datos.get(campo)
        if valor not in (None, ""):
            numero = Decimal(str(valor))
            if numero < 0:
                raise ValueError(f"{campo} no puede ser negativo")
            salida[campo] = str(numero)
    if "horas_normales_mes" in salida and Decimal(salida["horas_normales_mes"]) > 300:
        raise ValueError("Las horas normales del mes no pueden superar 300")
    return salida


def datos_casas_desde_dict(datos: dict) -> DatosCasasParticulares:
    limpio = validar_novedad_casas(datos)
    return DatosCasasParticulares(
        condicion_arca=limpio["condicion_arca"],
        horas_normales_mes=(
            Decimal(limpio["horas_normales_mes"])
            if limpio.get("horas_normales_mes") is not None else None
        ),
        valor_hora_pactado=(
            Dinero(Decimal(limpio["valor_hora_pactado"]))
            if limpio.get("valor_hora_pactado") is not None else None
        ),
    )


def tramo_horas_arca(horas_semanales: Decimal) -> str:
    horas = Decimal(str(horas_semanales))
    if not Decimal("0") < horas <= Decimal("48"):
        raise ValueError("Las horas semanales deben ser mayores que cero y no superar 48")
    if horas < Decimal("12"):
        return "MENOS_12"
    if horas < Decimal("16"):
        return "12_A_15"
    return "16_O_MAS"


def validar_condicion_trabajador(
    condicion_arca: str,
    fecha_nacimiento: Optional[date],
    fecha_calculo: date,
    horas_semanales: Decimal,
    categoria: str,
) -> None:
    if condicion_arca not in CONDICIONES_ARCA:
        raise ValueError("Condición ARCA inválida")
    if fecha_nacimiento is not None:
        edad = fecha_calculo.year - fecha_nacimiento.year - (
            (fecha_calculo.month, fecha_calculo.day)
            < (fecha_nacimiento.month, fecha_nacimiento.day)
        )
        if condicion_arca == "ADOLESCENTE_16_17" and edad not in {16, 17}:
            raise ValueError("La condición adolescente no coincide con la fecha de nacimiento")
        if condicion_arca == "ACTIVO" and edad < 18:
            raise ValueError("Para una persona de 16 o 17 años elegí la condición adolescente")
    elif condicion_arca == "ADOLESCENTE_16_17":
        raise ValueError("La condición adolescente requiere fecha de nacimiento en el legajo")
    if condicion_arca == "ADOLESCENTE_16_17":
        if Decimal(str(horas_semanales)) > Decimal("36"):
            raise ValueError("El trabajo adolescente no puede superar 36 horas semanales")
        if "sin retiro" in categoria.casefold():
            raise ValueError("Una persona de 16 o 17 años no puede trabajar sin retiro")


def anios_antiguedad_computables(fecha_ingreso: date, fecha_calculo: date) -> int:
    """El 1% comenzó a devengarse el 01/09/2020, sin retroactividad."""
    inicio = max(fecha_ingreso, date(2020, 9, 1))
    anios = fecha_calculo.year - inicio.year
    if (fecha_calculo.month, fecha_calculo.day) < (inicio.month, inicio.day):
        anios -= 1
    return max(anios, 0)


def calcular_base_casas(
    valores: ValoresEscalaCasas,
    horas_semanales: Decimal,
    horas_normales_mes: Optional[Decimal],
    remuneracion_pactada_mensual: Optional[Dinero] = None,
    valor_hora_pactado: Optional[Dinero] = None,
) -> ResultadoBaseCasas:
    horas_sem = Decimal(str(horas_semanales))
    tramo_horas_arca(horas_sem)  # valida 0 < horas <= 48
    if valores.mensual.monto <= 0 or valores.hora.monto <= 0:
        raise ValueError("La escala debe tener valor mensual y por hora verificados")

    if horas_sem < Decimal("24"):
        if horas_normales_mes is None:
            raise ValueError("Informá las horas normales realmente trabajadas en el mes")
        cantidad = Decimal(str(horas_normales_mes))
        if not Decimal("0") <= cantidad <= Decimal("300"):
            raise ValueError("Las horas normales del mes deben estar entre 0 y 300")
        valor = valores.hora
        if valor_hora_pactado is not None and valor_hora_pactado > valor:
            valor = valor_hora_pactado
        return ResultadoBaseCasas(
            "HORA", horas_sem, cantidad, valor, valor.multiplicar(cantidad).redondear()
        )

    proporcion = min(horas_sem / Decimal("48"), Decimal("1"))
    minimo = valores.mensual.porcentaje(proporcion)
    pactado = remuneracion_pactada_mensual or Dinero.cero()
    importe = max(minimo.monto, pactado.monto)
    base = Dinero(importe).redondear()
    # El valor normal de hora conserva como mínimo la tarifa horaria oficial.
    divisor = horas_sem * Decimal("4")
    valor_derivado = base.dividir(divisor)
    valor_hora = valor_derivado if valor_derivado > valores.hora else valores.hora
    return ResultadoBaseCasas("MENSUAL", horas_sem, proporcion, valor_hora, base)


def dias_vacaciones_casas(
    anios: int, meses_adicionales: int = 0, dias_trabajo_efectivo: int = 0,
) -> int:
    if anios < 0 or not 0 <= meses_adicionales <= 11 or dias_trabajo_efectivo < 0:
        raise ValueError("La antigüedad y los días trabajados no pueden ser negativos")
    if anios == 0 and meses_adicionales <= 6:
        return dias_trabajo_efectivo // 20
    if anios <= 5:
        return 14
    if anios <= 10:
        return 21
    if anios <= 20:
        return 28
    return 35


def calcular_sac_casas(mejor_remuneracion: Dinero, meses_trabajados: Decimal = Decimal("6")) -> Dinero:
    meses = Decimal(str(meses_trabajados))
    if not Decimal("0") <= meses <= Decimal("6"):
        raise ValueError("Los meses trabajados del semestre deben estar entre 0 y 6")
    return mejor_remuneracion.multiplicar(meses).dividir(Decimal("12")).redondear()


def armar_recibo_casas(
    empleado_cuil: str,
    periodo: Periodo,
    base: ResultadoBaseCasas,
    fecha_ingreso: date,
    fecha_calculo: date,
    antiguedad_pct_anual: Decimal,
    horas_extra_50: Decimal,
    horas_extra_100: Decimal,
    arca: ImportesArcaCasas,
    suma_no_remunerativa: Dinero = Dinero(Decimal("0")),
    faltas_injustificadas: int = 0,
    premio: Dinero = Dinero(Decimal("0")),
    tipo_premio: str = "pendiente",
    descuento_adicional: Dinero = Dinero(Decimal("0")),
    detalle_descuento: str = "",
) -> ResultadoLiquidacion:
    if Decimal(str(antiguedad_pct_anual)) < 0:
        raise ValueError("El porcentaje de antigüedad no puede ser negativo")
    he50, he100 = Decimal(str(horas_extra_50)), Decimal(str(horas_extra_100))
    if he50 < 0 or he100 < 0:
        raise ValueError("Las horas extra no pueden ser negativas")
    if faltas_injustificadas < 0:
        raise ValueError("Las faltas injustificadas no pueden ser negativas")
    if premio.monto and tipo_premio not in {"remunerativo", "no_remunerativo"}:
        raise ValueError("Indicá si el premio es remunerativo o no remunerativo")
    if descuento_adicional.monto and not detalle_descuento.strip():
        raise ValueError("El descuento adicional requiere una observación")

    conceptos = [Concepto(
        "BASICO_CASAS_PARTICULARES", "Salario básico · Ley 26.844",
        TipoConcepto.REMUNERATIVO, base.importe,
        cantidad=base.cantidad, base_calculo=base.valor_unitario,
        unidad="hora" if base.modalidad == "HORA" else "mensual proporcional",
    )]
    if base.modalidad == "MENSUAL" and faltas_injustificadas:
        descuento_faltas = base.importe.dividir(Decimal("30")).multiplicar(
            Decimal(faltas_injustificadas)
        ).redondear()
        conceptos.append(Concepto(
            "FALTAS_INJUSTIFICADAS_CASAS", "Faltas injustificadas",
            TipoConcepto.DEDUCCION, descuento_faltas,
            cantidad=Decimal(faltas_injustificadas),
            base_calculo=base.importe.dividir(Decimal("30")), unidad="día",
        ))

    anios = anios_antiguedad_computables(fecha_ingreso, fecha_calculo)
    if anios:
        antiguedad = base.importe.porcentaje(
            Decimal(anios) * Decimal(str(antiguedad_pct_anual))
        ).redondear()
        conceptos.append(Concepto(
            "ANTIGUEDAD_CASAS", "Antigüedad desde septiembre de 2020",
            TipoConcepto.REMUNERATIVO, antiguedad, cantidad=Decimal(anios),
            base_calculo=base.importe, unidad="1% por año computable",
        ))
    for codigo, descripcion, horas, factor in (
        ("HORAS_EXTRA_50_CASAS", "Horas extra al 50%", he50, Decimal("1.5")),
        ("HORAS_EXTRA_100_CASAS", "Horas extra al 100%", he100, Decimal("2")),
    ):
        if horas:
            conceptos.append(Concepto(
                codigo, descripcion, TipoConcepto.REMUNERATIVO,
                base.valor_unitario.multiplicar(horas * factor).redondear(),
                cantidad=horas, base_calculo=base.valor_unitario, unidad="hora con recargo",
            ))
    if suma_no_remunerativa.monto:
        conceptos.append(Concepto(
            "SUMA_NR_CASAS", "Suma extraordinaria no remunerativa",
            TipoConcepto.NO_REMUNERATIVO, suma_no_remunerativa.redondear(),
        ))
    if premio.monto:
        conceptos.append(Concepto(
            "PREMIO", "Premio", TipoConcepto.REMUNERATIVO
            if tipo_premio == "remunerativo" else TipoConcepto.NO_REMUNERATIVO,
            premio.redondear(),
        ))
    if arca.aporte_trabajador.monto:
        conceptos.append(Concepto(
            "APORTE_OBRA_SOCIAL_CASAS", "Aporte a obra social · ARCA",
            TipoConcepto.DEDUCCION, arca.aporte_trabajador.redondear(),
            destino_pago="ARCA", codigo_boleta="F102RT",
            canal_pago="ARCA Casas Particulares",
        ))
    conceptos.extend([
        Concepto(
            "CONTRIBUCION_JUBILACION_CASAS", "Contribución jubilatoria · ARCA",
            TipoConcepto.CONTRIBUCION, arca.contribucion_empleador.redondear(),
            destino_pago="ARCA", codigo_boleta="F102RT",
        ),
        Concepto(
            "ART_CASAS_PARTICULARES", "Cuota de riesgos del trabajo · ARCA",
            TipoConcepto.CONTRIBUCION, arca.art.redondear(),
            destino_pago="ARCA", codigo_boleta="F102RT",
        ),
    ])
    if descuento_adicional.monto:
        conceptos.append(Concepto(
            "DESCUENTO_ADICIONAL", detalle_descuento.strip(), TipoConcepto.DEDUCCION,
            descuento_adicional.redondear(),
        ))
    return ResultadoLiquidacion(empleado_cuil, periodo, "mensual", conceptos)
