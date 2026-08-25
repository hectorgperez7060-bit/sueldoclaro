"""Cálculos variables CCT 40/89, sin importes ni fechas incrustados."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from domain.value_objects.dinero import Dinero


ZONAS_CAMIONEROS = {
    "BASE": Decimal("1"), "COEF_1_20": Decimal("1.20"), "COEF_1_40": Decimal("1.40")
}


@dataclass(frozen=True)
class ValoresVariablesCamioneros:
    comida: Dinero
    viatico_especial: Dinero
    pernoctada: Dinero
    hora_extra_km: Decimal
    viatico_km: Decimal
    permanencia: Dinero
    simple_presencia: Dinero
    permanencia_sur: Dinero
    simple_presencia_sur: Dinero
    cruce_frontera: Dinero
    ingreso_egreso_tdf: Dinero
    plus_vacacional_dia: Dinero
    adicional_bitrenes: Dinero


@dataclass(frozen=True)
class NovedadesVariablesCamioneros:
    zona: str = "BASE"
    dias_comida: Decimal = Decimal("0")
    dias_viatico_especial: Decimal = Decimal("0")
    pernoctadas: Decimal = Decimal("0")
    kilometros_extra: Decimal = Decimal("0")
    kilometros_viatico: Decimal = Decimal("0")
    dias_en_viaje: Decimal = Decimal("0")
    viajes_cordilleranos: Decimal = Decimal("0")
    permanencias: Decimal = Decimal("0")
    simples_presencias: Decimal = Decimal("0")
    permanencias_sur: Decimal = Decimal("0")
    simples_presencias_sur: Decimal = Decimal("0")
    cruces_frontera: Decimal = Decimal("0")
    ingresos_egresos_tdf: Decimal = Decimal("0")
    dias_plus_vacacional: Decimal = Decimal("0")
    unidades_bitrenes: Decimal = Decimal("0")


@dataclass(frozen=True)
class ConceptoVariableCamioneros:
    codigo: str
    descripcion: str
    cantidad: Decimal
    valor_unitario: Dinero
    importe: Dinero


def calcular_variables_camioneros(
    valores: ValoresVariablesCamioneros,
    novedades: NovedadesVariablesCamioneros,
) -> tuple[ConceptoVariableCamioneros, ...]:
    """Liquida solo hechos informados y aplica garantías de kilometraje explícitas."""
    if novedades.zona not in ZONAS_CAMIONEROS:
        raise ValueError("La zona Camioneros debe ser BASE, COEF_1_20 o COEF_1_40")
    cantidades = {
        nombre: Decimal(str(getattr(novedades, nombre)))
        for nombre in novedades.__dataclass_fields__ if nombre != "zona"
    }
    if any(v < 0 for v in cantidades.values()):
        raise ValueError("Las novedades Camioneros no pueden ser negativas")
    factor = ZONAS_CAMIONEROS[novedades.zona]
    resultado: list[ConceptoVariableCamioneros] = []

    def fijo(codigo: str, descripcion: str, cantidad: Decimal, valor: Dinero, zonal: bool = False):
        if not cantidad:
            return
        unitario = valor.multiplicar(factor) if zonal else valor
        resultado.append(ConceptoVariableCamioneros(
            codigo, descripcion, cantidad, unitario.redondear(), unitario.multiplicar(cantidad).redondear()
        ))

    fijo("COMIDA_4_1_12", "Comida", cantidades["dias_comida"], valores.comida, True)
    fijo("VIATICO_ESPECIAL_4_1_13", "Viático especial", cantidades["dias_viatico_especial"], valores.viatico_especial, True)
    fijo("PERNOCTADA_4_1_14", "Pernoctada", cantidades["pernoctadas"], valores.pernoctada, True)

    km_extra = cantidades["kilometros_extra"]
    if km_extra:
        tarifa = Dinero(valores.hora_extra_km).multiplicar(factor)
        fijo("HORAS_EXTRA_KM_4_2_3", "Horas extraordinarias por kilometraje", km_extra, tarifa)

    km_minimos = cantidades["dias_en_viaje"] * Decimal("350")
    km_cordillera = cantidades["viajes_cordilleranos"] * Decimal("700")
    km_viatico = max(cantidades["kilometros_viatico"], km_minimos, km_cordillera)
    if km_viatico:
        tarifa = Dinero(valores.viatico_km).multiplicar(factor)
        fijo("VIATICO_KM_4_2_4", "Viático por kilometraje", km_viatico, tarifa)

    fijo("PERMANENCIA_4_2_5", "Permanencia fuera de residencia", cantidades["permanencias"], valores.permanencia)
    fijo("SIMPLE_PRESENCIA_4_2_5", "Simple presencia", cantidades["simples_presencias"], valores.simple_presencia)
    fijo("PERMANENCIA_SUR_4_2_5", "Permanencia al sur del Río Colorado", cantidades["permanencias_sur"], valores.permanencia_sur)
    fijo("SIMPLE_PRESENCIA_SUR_4_2_5", "Simple presencia al sur del Río Colorado", cantidades["simples_presencias_sur"], valores.simple_presencia_sur)
    fijo("CRUCE_FRONTERA_4_2_17", "Cruce de frontera", cantidades["cruces_frontera"], valores.cruce_frontera)
    fijo("INGRESO_EGRESO_TDF_4_2_17", "Ingreso o egreso de Tierra del Fuego", cantidades["ingresos_egresos_tdf"], valores.ingreso_egreso_tdf)
    fijo("PLUS_VACACIONAL_3_3_2", "Plus vacacional por día", cantidades["dias_plus_vacacional"], valores.plus_vacacional_dia)
    fijo("ADICIONAL_BITRENES", "Adicional bitrenes", cantidades["unidades_bitrenes"], valores.adicional_bitrenes)
    return tuple(resultado)
