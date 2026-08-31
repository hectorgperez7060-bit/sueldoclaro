"""Cálculos variables CCT 40/89, sin importes ni fechas incrustados."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from domain.value_objects.dinero import Dinero
from domain.entities.concepto import Concepto, TipoConcepto
from domain.entities.liquidacion import ResultadoLiquidacion
from domain.value_objects.periodo import Periodo


ZONAS_CAMIONEROS = {
    "BASE": Decimal("1"), "COEF_1_20": Decimal("1.20"), "COEF_1_40": Decimal("1.40")
}

RAMAS_CAMIONEROS = {
    "general", "materia_prima_lactea", "auxilio", "residuos", "taller",
    "caudales", "diarios_revistas", "combustibles", "sustancias_peligrosas",
    "pozos_petroliferos", "clearing", "expreso_mudanza", "aguas_gaseosas",
    "logistica", "larga_distancia", "transporte_automoviles",
    "asfalto_caliente", "transporte_pesado", "zafra",
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
    traslados_unidad_descarga: Decimal = Decimal("0")
    viajes_transporte_automoviles: Decimal = Decimal("0")
    dias_asfalto_caliente: Decimal = Decimal("0")


CAMPOS_CANTIDAD_CAMIONEROS = tuple(
    nombre for nombre in NovedadesVariablesCamioneros.__dataclass_fields__ if nombre != "zona"
)
CLAVES_DETALLE_CAMIONEROS = {
    "rama", "camara_frio", "zona", "grupo_taller", "cuenca_petrolifera",
    "la_pampa_mendoza", "toneladas_transporte_pesado",
    "modalidad_transporte_pesado", "radio_zafra", *CAMPOS_CANTIDAD_CAMIONEROS
}

CODIGOS_VIATICO_NO_REMUNERATIVO = {
    "COMIDA_4_1_12", "VIATICO_ESPECIAL_4_1_13", "PERNOCTADA_4_1_14",
    "VIATICO_KM_4_2_4", "PERMANENCIA_4_2_5", "SIMPLE_PRESENCIA_4_2_5",
    "PERMANENCIA_SUR_4_2_5", "SIMPLE_PRESENCIA_SUR_4_2_5",
    "CRUCE_FRONTERA_4_2_17", "INGRESO_EGRESO_TDF_4_2_17",
}


def tramo_transporte_pesado(toneladas: Decimal) -> str:
    """Devuelve el parámetro del ítem 5.8.1.2.a según la carga útil."""
    carga = Decimal(str(toneladas))
    if carga <= 0:
        raise ValueError("la carga útil del transporte pesado debe ser mayor que cero")
    if carga <= Decimal("50"):
        return "CAM_PESADO_HASTA_50_PCT"
    if carga <= Decimal("100"):
        return "CAM_PESADO_50_100_PCT"
    return "CAM_PESADO_MAS_100_PCT"


def novedades_camioneros_desde_dict(datos: dict) -> NovedadesVariablesCamioneros:
    """Valida y convierte la novedad persistida sin aceptar claves silenciosas."""
    if not isinstance(datos, dict):
        raise ValueError("El detalle Camioneros debe ser un objeto")
    desconocidas = set(datos) - CLAVES_DETALLE_CAMIONEROS
    if desconocidas:
        raise ValueError(f"Campos Camioneros desconocidos: {', '.join(sorted(desconocidas))}")
    rama = str(datos.get("rama", "general"))
    if rama not in RAMAS_CAMIONEROS:
        raise ValueError("La rama Camioneros seleccionada no es válida")
    camara_frio = datos.get("camara_frio", False)
    if not isinstance(camara_frio, bool):
        raise ValueError("Cámara de frío debe informarse como sí o no")
    for campo_booleano in ("cuenca_petrolifera", "la_pampa_mendoza"):
        if not isinstance(datos.get(campo_booleano, False), bool):
            raise ValueError(f"{campo_booleano.replace('_', ' ')} debe informarse como sí o no")
    grupo_taller = str(datos.get("grupo_taller") or "")
    if grupo_taller not in {"", "I", "II", "III"}:
        raise ValueError("El grupo de taller debe ser I, II o III")
    novedades = NovedadesVariablesCamioneros(
        zona=str(datos.get("zona", "BASE")),
        **{campo: Decimal(str(datos.get(campo, 0))) for campo in CAMPOS_CANTIDAD_CAMIONEROS},
    )
    if novedades.zona not in ZONAS_CAMIONEROS:
        raise ValueError("La zona Camioneros debe ser BASE, COEF_1_20 o COEF_1_40")
    if any(Decimal(str(getattr(novedades, campo))) < 0 for campo in CAMPOS_CANTIDAD_CAMIONEROS):
        raise ValueError("Las novedades Camioneros no pueden ser negativas")
    return novedades


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


def armar_recibo_camioneros_general(
    empleado_cuil: str,
    periodo: Periodo,
    basico: Dinero,
    anios_antiguedad: int,
    proporcion_jornada: Decimal,
    variables: tuple[ConceptoVariableCamioneros, ...],
    jubilacion_pct: Decimal,
    inssjp_pct: Decimal,
    obra_social_pct: Decimal,
    contrib_seguridad_pct: Decimal,
    contrib_obra_social_pct: Decimal,
    traslados_unidad_descarga: Decimal = Decimal("0"),
    adicionales_rama: tuple[tuple[str, str, Decimal], ...] = (),
    recargo_comida_pct: Decimal = Decimal("0"),
    recargo_viatico_pct: Decimal = Decimal("0"),
    recargo_codigo: str = "RESIDUOS_5_3_11",
    recargo_descripcion: str = "recolección de residuos",
    viajes_transporte_automoviles: Decimal = Decimal("0"),
    jornales_por_viaje_automoviles: Decimal = Decimal("1"),
    dias_asfalto_caliente: Decimal = Decimal("0"),
    jornales_por_dia_asfalto: Decimal = Decimal("1"),
    adicional_zafra_pct: Decimal = Decimal("0"),
) -> ResultadoLiquidacion:
    """Recibo de la rama general con incidencias explícitas del CCT 40/89.

    Los viáticos enumerados por el ítem 4.2.11 no integran remuneración ni
    cargas sociales. Horas extraordinarias por kilometraje y plus vacacional
    sí integran la base. Bitrenes continúa bloqueado porque su hecho generador
    aún no está documentado en el paquete normativo.
    """
    proporcion = Decimal(str(proporcion_jornada))
    if not Decimal("0") < proporcion <= Decimal("1"):
        raise ValueError("la proporción de jornada debe ser mayor que cero y no superar uno")
    if any(v.codigo == "ADICIONAL_BITRENES" for v in variables):
        raise ValueError("el adicional bitrenes todavía requiere documentar su hecho generador")

    basico_proporcional = basico.porcentaje(proporcion).redondear()
    conceptos = [Concepto(
        "BASICO", "Sueldo básico Camioneros", TipoConcepto.REMUNERATIVO,
        basico_proporcional, base_calculo=basico, unidad="mes",
    )]
    remunerativos_variables = Dinero.cero()
    for codigo_rama, descripcion_rama, porcentaje_rama in adicionales_rama:
        porcentaje = Decimal(str(porcentaje_rama))
        if porcentaje <= 0 or porcentaje > Decimal("1"):
            raise ValueError("el porcentaje de rama Camioneros no es válido")
        importe_rama = basico_proporcional.porcentaje(porcentaje).redondear()
        conceptos.append(Concepto(
            codigo_rama, descripcion_rama, TipoConcepto.REMUNERATIVO,
            importe_rama, base_calculo=basico_proporcional,
            unidad=f"{porcentaje * 100}% sobre básico de categoría",
        ))
        remunerativos_variables = remunerativos_variables + importe_rama
    for variable in variables:
        tipo = (
            TipoConcepto.NO_REMUNERATIVO
            if variable.codigo in CODIGOS_VIATICO_NO_REMUNERATIVO
            else TipoConcepto.REMUNERATIVO
        )
        conceptos.append(Concepto(
            variable.codigo, variable.descripcion, tipo, variable.importe,
            cantidad=variable.cantidad, base_calculo=variable.valor_unitario,
            unidad="unidad convencional",
        ))
        if tipo == TipoConcepto.REMUNERATIVO:
            remunerativos_variables = remunerativos_variables + variable.importe
        porcentaje_recargo = (
            Decimal(str(recargo_comida_pct)) if variable.codigo == "COMIDA_4_1_12"
            else Decimal(str(recargo_viatico_pct)) if variable.codigo == "VIATICO_ESPECIAL_4_1_13"
            else Decimal("0")
        )
        if porcentaje_recargo:
            recargo_pct = porcentaje_recargo
            if recargo_pct <= 0 or recargo_pct > Decimal("1"):
                raise ValueError("el recargo de viáticos Camioneros no es válido")
            recargo = variable.importe.porcentaje(recargo_pct).redondear()
            tipo_variable = "COMIDA" if variable.codigo == "COMIDA_4_1_12" else "VIATICO"
            conceptos.append(Concepto(
                f"RECARGO_{tipo_variable}_{recargo_codigo}",
                f"Adicional de {tipo_variable.casefold()} · {recargo_descripcion}",
                TipoConcepto.NO_REMUNERATIVO, recargo,
                cantidad=variable.cantidad, base_calculo=variable.importe,
                unidad=f"{recargo_pct * 100}% sobre comida",
            ))

    traslados = Decimal(str(traslados_unidad_descarga))
    if traslados < 0 or traslados != traslados.to_integral_value():
        raise ValueError("los traslados para descarga deben ser una cantidad entera no negativa")
    if traslados:
        jornal = basico_proporcional.dividir(Decimal("24")).redondear()
        importe_traslados = jornal.multiplicar(traslados).redondear()
        conceptos.append(Concepto(
            "TRASLADO_UNIDAD_DESCARGA_4_2_6",
            "Traslado de la unidad para descarga", TipoConcepto.REMUNERATIVO,
            importe_traslados, cantidad=traslados, base_calculo=jornal,
            unidad="jornal por traslado · ítem 4.2.6",
        ))
        remunerativos_variables = remunerativos_variables + importe_traslados

    viajes_autos = Decimal(str(viajes_transporte_automoviles))
    if viajes_autos < 0 or viajes_autos != viajes_autos.to_integral_value():
        raise ValueError("los viajes de transporte de automóviles deben ser enteros no negativos")
    if viajes_autos:
        factor_jornales = Decimal(str(jornales_por_viaje_automoviles))
        if factor_jornales <= 0:
            raise ValueError("la cantidad convencional de jornales por viaje no es válida")
        jornal_autos = basico_proporcional.dividir(Decimal("24")).redondear()
        importe_autos = jornal_autos.multiplicar(viajes_autos * factor_jornales).redondear()
        conceptos.append(Concepto(
            "TRANSPORTE_AUTOMOVILES_4_2_9",
            "Viaje de transporte de automóviles", TipoConcepto.REMUNERATIVO,
            importe_autos, cantidad=viajes_autos, base_calculo=jornal_autos,
            unidad=f"{factor_jornales} jornal por viaje · ítem 4.2.9",
        ))
        remunerativos_variables = remunerativos_variables + importe_autos

    dias_asfalto = Decimal(str(dias_asfalto_caliente))
    if dias_asfalto < 0 or dias_asfalto != dias_asfalto.to_integral_value():
        raise ValueError("los días de operación con asfalto deben ser enteros no negativos")
    if dias_asfalto:
        factor_asfalto = Decimal(str(jornales_por_dia_asfalto))
        if factor_asfalto <= 0:
            raise ValueError("la cantidad convencional de jornales de asfalto no es válida")
        jornal_asfalto = basico_proporcional.dividir(Decimal("24")).redondear()
        importe_asfalto = jornal_asfalto.multiplicar(dias_asfalto * factor_asfalto).redondear()
        conceptos.append(Concepto(
            "RECARGO_ASFALTO_5_5_2",
            "Operación con asfalto o producto caliente", TipoConcepto.REMUNERATIVO,
            importe_asfalto, cantidad=dias_asfalto, base_calculo=jornal_asfalto,
            unidad=f"{factor_asfalto} jornal por día · ítem 5.5.2",
        ))
        remunerativos_variables = remunerativos_variables + importe_asfalto

    base_antiguedad = (basico_proporcional + remunerativos_variables).redondear()
    antiguedad_pct = Decimal(int(anios_antiguedad)) / Decimal("100")
    antiguedad = base_antiguedad.porcentaje(antiguedad_pct).redondear()
    conceptos.append(Concepto(
        "ANTIGUEDAD", f"Antigüedad ({int(anios_antiguedad)} años)",
        TipoConcepto.REMUNERATIVO, antiguedad,
        cantidad=Decimal(int(anios_antiguedad)), base_calculo=base_antiguedad,
        unidad="1% por año · ítem 6.1.5",
    ))
    adicional_zafra = Dinero.cero()
    pct_zafra = Decimal(str(adicional_zafra_pct))
    if pct_zafra:
        if pct_zafra <= 0 or pct_zafra > Decimal("1"):
            raise ValueError("el adicional de zafra no es válido")
        no_remunerativos_variables = Dinero.cero()
        for variable in variables:
            if variable.codigo in CODIGOS_VIATICO_NO_REMUNERATIVO:
                no_remunerativos_variables = no_remunerativos_variables + variable.importe
        base_zafra = (
            base_antiguedad + antiguedad + no_remunerativos_variables
        ).redondear()
        adicional_zafra = base_zafra.porcentaje(pct_zafra).redondear()
        conceptos.append(Concepto(
            "ADICIONAL_ZAFRA_5_9_3", "Adicional transporte en zona de zafra",
            TipoConcepto.REMUNERATIVO, adicional_zafra,
            base_calculo=base_zafra,
            unidad=f"{pct_zafra * 100}% sobre total percibido · ítem 5.9.3",
        ))
    base_rem = (base_antiguedad + antiguedad + adicional_zafra).redondear()
    conceptos.extend([
        Concepto("APORTE_JUBILACION", "Jubilación", TipoConcepto.DEDUCCION,
                 base_rem.porcentaje(jubilacion_pct).redondear(), base_calculo=base_rem,
                 unidad="porcentaje versionado"),
        Concepto("APORTE_LEY19032", "Ley 19.032 - INSSJP", TipoConcepto.DEDUCCION,
                 base_rem.porcentaje(inssjp_pct).redondear(), base_calculo=base_rem,
                 unidad="porcentaje versionado"),
        Concepto("APORTE_OBRA_SOCIAL", "Obra social", TipoConcepto.DEDUCCION,
                 base_rem.porcentaje(obra_social_pct).redondear(), base_calculo=base_rem,
                 unidad="porcentaje versionado"),
        Concepto("CONTRIB_SEGURIDAD_SOCIAL", "Contribuciones patronales seguridad social",
                 TipoConcepto.CONTRIBUCION,
                 base_rem.porcentaje(contrib_seguridad_pct).redondear(), base_calculo=base_rem),
        Concepto("CONTRIB_OBRA_SOCIAL", "Contribución patronal obra social",
                 TipoConcepto.CONTRIBUCION,
                 base_rem.porcentaje(contrib_obra_social_pct).redondear(), base_calculo=base_rem),
    ])
    return ResultadoLiquidacion(empleado_cuil, periodo, "mensual", conceptos)
