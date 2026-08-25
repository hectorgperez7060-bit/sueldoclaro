"""Núcleo UOM CCT 260/75: jornal, mensual e IMGR sin importes incrustados."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from domain.entities.parametros import EscalaSalarial
from domain.entities.concepto import Concepto, TipoConcepto
from domain.entities.liquidacion import ResultadoLiquidacion
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


@dataclass(frozen=True)
class ResultadoBaseUom:
    modalidad: str
    cantidad: Decimal
    valor_unitario: Dinero
    basico: Dinero


@dataclass(frozen=True)
class ResultadoImgrUom:
    garantia_proporcional: Dinero
    ingresos_computables: Dinero
    complemento: Dinero


@dataclass(frozen=True)
class ResultadoAdicionalUom:
    modalidad: str
    cantidad: Decimal
    valor_unitario: Dinero
    importe: Dinero


CLAVES_NOVEDAD_UOM = {
    "horas_normales", "ingresos_computables_imgr", "adicionales",
    "dias_trabajados_abril_julio", "contrato_vigente_31_07",
    "pagos_a_cuenta_absorbibles",
}


def validar_novedad_uom(datos: dict) -> dict:
    if not isinstance(datos, dict):
        raise ValueError("El detalle UOM debe ser un objeto")
    desconocidas = set(datos) - CLAVES_NOVEDAD_UOM
    if desconocidas:
        raise ValueError("Campos UOM desconocidos: " + ", ".join(sorted(desconocidas)))
    salida = {}
    for campo in ("horas_normales", "ingresos_computables_imgr", "pagos_a_cuenta_absorbibles"):
        valor = datos.get(campo)
        if valor is not None:
            numero = Decimal(str(valor))
            if numero < 0:
                raise ValueError(f"{campo} no puede ser negativo")
            salida[campo] = str(numero)
    dias = datos.get("dias_trabajados_abril_julio")
    if dias is not None:
        dias = int(dias)
        if not 0 <= dias <= 122:
            raise ValueError("Los días trabajados abril-julio deben estar entre 0 y 122")
        salida["dias_trabajados_abril_julio"] = dias
    salida["contrato_vigente_31_07"] = bool(datos.get("contrato_vigente_31_07", False))
    adicionales = datos.get("adicionales", {})
    if not isinstance(adicionales, dict):
        raise ValueError("Los adicionales UOM deben ser un objeto")
    salida["adicionales"] = {}
    for codigo, cantidad in adicionales.items():
        if not isinstance(codigo, str) or not codigo.strip() or Decimal(str(cantidad)) <= 0:
            raise ValueError("Cada adicional UOM debe tener código y cantidad positiva")
        salida["adicionales"][codigo] = str(Decimal(str(cantidad)))
    return salida


def calcular_gratificacion_uom(valor: Dinero, proporcion_jornada: Decimal) -> Dinero:
    proporcion = Decimal(str(proporcion_jornada))
    if not Decimal("0") < proporcion <= Decimal("1"):
        raise ValueError("La proporción de jornada UOM debe ser mayor que cero y no superar uno")
    return valor.porcentaje(proporcion).redondear()


def calcular_compensacion_abril_julio_uom(
    cuota: Dinero, dias_trabajados: int, proporcion_jornada: Decimal,
    contrato_vigente_31_07: bool, pagos_a_cuenta_absorbibles: Dinero,
) -> Dinero:
    if not contrato_vigente_31_07:
        return Dinero.cero()
    if not 0 <= int(dias_trabajados) <= 122:
        raise ValueError("Los días trabajados abril-julio deben estar entre 0 y 122")
    if pagos_a_cuenta_absorbibles.monto < 0:
        raise ValueError("Los pagos a cuenta absorbibles no pueden ser negativos")
    proporcion = Decimal(str(proporcion_jornada))
    bruto = cuota.multiplicar(Decimal(int(dias_trabajados)) / Decimal("122"))
    bruto = bruto.porcentaje(proporcion).redondear()
    return Dinero(max(bruto.monto - pagos_a_cuenta_absorbibles.monto, Decimal("0"))).redondear()


def armar_recibo_uom(
    empleado_cuil: str, periodo: Periodo, base: ResultadoBaseUom,
    gratificacion_nr: Dinero, compensacion_nr: Dinero, imgr: ResultadoImgrUom,
    jubilacion_pct: Decimal, inssjp_pct: Decimal, obra_social_pct: Decimal,
    contrib_seguridad_pct: Decimal, contrib_obra_social_pct: Decimal,
    seguro_trabajador: Dinero, seguro_empleador: Dinero,
) -> ResultadoLiquidacion:
    """Resultado UOM con bases explícitas; no presume cuota sindical ni extras."""
    base_rem = (base.basico + imgr.complemento).redondear()
    base_os = (base_rem + gratificacion_nr + compensacion_nr).redondear()
    conceptos = [
        Concepto("BASICO_UOM", "Básico UOM", TipoConcepto.REMUNERATIVO, base.basico,
                 cantidad=base.cantidad, base_calculo=base.valor_unitario,
                 unidad="hora" if base.modalidad == "HORA" else "mensual"),
    ]
    if imgr.complemento.monto:
        conceptos.append(Concepto("COMPLEMENTO_IMGR_UOM", "Complemento IMGR", TipoConcepto.REMUNERATIVO,
                                  imgr.complemento, base_calculo=imgr.garantia_proporcional,
                                  unidad="garantía menos ingresos computables"))
    if gratificacion_nr.monto:
        conceptos.append(Concepto("GRATIFICACION_NR_UOM", "Gratificación extraordinaria no remunerativa",
                                  TipoConcepto.NO_REMUNERATIVO, gratificacion_nr))
    if compensacion_nr.monto:
        conceptos.append(Concepto("COMPENSACION_ABR_JUL_UOM", "Compensación extraordinaria abril-julio · cuota 1",
                                  TipoConcepto.NO_REMUNERATIVO, compensacion_nr))
    conceptos.extend([
        Concepto("APORTE_JUBILACION", "Jubilación", TipoConcepto.DEDUCCION,
                 base_rem.porcentaje(jubilacion_pct).redondear(), base_calculo=base_rem, unidad="porcentaje versionado"),
        Concepto("APORTE_LEY19032", "Ley 19.032 - INSSJP", TipoConcepto.DEDUCCION,
                 base_rem.porcentaje(inssjp_pct).redondear(), base_calculo=base_rem, unidad="porcentaje versionado"),
        Concepto("APORTE_OBRA_SOCIAL", "Obra social", TipoConcepto.DEDUCCION,
                 base_os.porcentaje(obra_social_pct).redondear(), base_calculo=base_os, unidad="porcentaje versionado"),
        Concepto("SEGURO_VIDA_SEPELIO_UOM", "Seguro colectivo de vida y sepelio UOM",
                 TipoConcepto.DEDUCCION, seguro_trabajador, destino_pago="UOMRA"),
        Concepto("CONTRIB_SEGURIDAD_SOCIAL", "Contribuciones patronales seguridad social",
                 TipoConcepto.CONTRIBUCION, base_rem.porcentaje(contrib_seguridad_pct).redondear(), base_calculo=base_rem),
        Concepto("CONTRIB_OBRA_SOCIAL", "Contribución patronal obra social", TipoConcepto.CONTRIBUCION,
                 base_os.porcentaje(contrib_obra_social_pct).redondear(), base_calculo=base_os),
        Concepto("SEGURO_VIDA_SEPELIO_UOM_EMP", "Seguro colectivo de vida y sepelio UOM · empleador",
                 TipoConcepto.CONTRIBUCION, seguro_empleador, destino_pago="UOMRA"),
    ])
    return ResultadoLiquidacion(empleado_cuil, periodo, "mensual", conceptos)


def calcular_base_uom(
    escala: EscalaSalarial,
    horas_normales: Optional[Decimal] = None,
    proporcion_jornada: Decimal = Decimal("1"),
) -> ResultadoBaseUom:
    proporcion = Decimal(str(proporcion_jornada))
    if not Decimal("0") < proporcion <= Decimal("1"):
        raise ValueError("La proporción de jornada UOM debe ser mayor que cero y no superar uno")
    if escala.unidad_escala == "HORA":
        if horas_normales is None:
            raise ValueError("La categoría UOM jornalizada requiere horas normales del período")
        cantidad = Decimal(str(horas_normales))
        if not Decimal("0") <= cantidad <= Decimal("300"):
            raise ValueError("Las horas normales UOM deben estar entre 0 y 300")
        importe = escala.basico.multiplicar(cantidad).redondear()
        return ResultadoBaseUom("HORA", cantidad, escala.basico, importe)
    if escala.unidad_escala == "MENSUAL":
        if horas_normales not in (None, Decimal("0"), 0):
            raise ValueError("La categoría UOM mensualizada no liquida el básico por horas")
        importe = escala.basico.porcentaje(proporcion).redondear()
        return ResultadoBaseUom("MENSUAL", proporcion, escala.basico, importe)
    raise ValueError("La escala UOM debe declarar modalidad HORA o MENSUAL")


def calcular_complemento_imgr(
    imgr: Dinero,
    ingresos_computables_sin_horas_extra: Dinero,
    proporcion_jornada: Decimal = Decimal("1"),
) -> ResultadoImgrUom:
    proporcion = Decimal(str(proporcion_jornada))
    if not Decimal("0") < proporcion <= Decimal("1"):
        raise ValueError("La proporción de jornada UOM debe ser mayor que cero y no superar uno")
    if ingresos_computables_sin_horas_extra.monto < 0:
        raise ValueError("Los ingresos computables para IMGR no pueden ser negativos")
    garantia = imgr.porcentaje(proporcion).redondear()
    complemento = Dinero(max(garantia.monto - ingresos_computables_sin_horas_extra.monto, Decimal("0"))).redondear()
    return ResultadoImgrUom(garantia, ingresos_computables_sin_horas_extra.redondear(), complemento)


def calcular_adicional_uom(
    valor: Dinero, modalidad: str, cantidad: Optional[Decimal] = None,
) -> ResultadoAdicionalUom:
    if modalidad == "FIJO_MENSUAL":
        if cantidad not in (None, Decimal("1"), 1):
            raise ValueError("El adicional fijo UOM no admite una cantidad distinta de uno")
        return ResultadoAdicionalUom(modalidad, Decimal("1"), valor, valor.redondear())
    if modalidad not in {"POR_HORA", "POR_EVENTO"}:
        raise ValueError("Modalidad de adicional UOM no verificada")
    if cantidad is None or Decimal(str(cantidad)) <= 0:
        raise ValueError("El adicional UOM requiere una cantidad positiva")
    qty = Decimal(str(cantidad))
    return ResultadoAdicionalUom(modalidad, qty, valor, valor.multiplicar(qty).redondear())
