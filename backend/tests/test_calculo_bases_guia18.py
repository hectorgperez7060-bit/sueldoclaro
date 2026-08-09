"""Suite de pruebas unitarias para el calculador de Bases Imponibles ARCA (Guía N.º 18).

Verifica el cálculo de las 10 Bases Imponibles del Registro 04 en 3 escenarios:
1. Empleado mensual normal ($1.000.000, Full-time, Régimen General).
2. Mes con SAC de diciembre ($1.000.000 sueldo + $500.000 SAC).
3. Mes con Adelanto Vacacional (14 días $350.000 + $400.000 sueldo restante).
"""
from decimal import Decimal
import os, sys

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from datetime import date
from domain.entities.concepto import Concepto, TipoConcepto
from domain.entities.empleado import Empleado
from domain.entities.liquidacion import ResultadoLiquidacion
from domain.payroll_engine.config import CctConfig
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from infrastructure.lsd.calculator import ParametrosPeriodoLSD, calcular_bases_lsd
from infrastructure.lsd.catalogo_afip import ConceptoARCA, GrupoARCA


def _crear_empleado_demo(proporcion_jornada: Decimal = Decimal("1.0"), es_regimen_diferencial: bool = False) -> Empleado:
    emp = Empleado(
        nombre="Juan",
        apellido="Pérez",
        cuil=Cuil("27-30732466-6"),
        fecha_ingreso=date(2020, 1, 1),
        cct_numero="130/75",
        categoria="Administrativo A",
        legajo="EMP001",
        proporcion_jornada=proporcion_jornada,
    )
    # Atributo dinámico de régimen diferencial para Guía 18
    object.__setattr__(emp, "es_regimen_diferencial", es_regimen_diferencial)
    return emp


def _crear_parametros_demo() -> ParametrosPeriodoLSD:
    return ParametrosPeriodoLSD(
        periodo=Periodo(2026, 7),
        tope_min_sipa=Dinero("50000.00"),
        tope_max_sipa_mensual=Dinero("2000000.00"),
        tope_max_sipa_sac=Dinero("1000000.00"),
        piso_obra_social=Dinero("100000.00"),
        detraccion_ley27541_mensual=Dinero("7003.00"),
        detraccion_ley27541_sac=Dinero("3501.50"),
    )


def test_ejemplo_a_mensual_normal():
    emp = _crear_empleado_demo()
    params = _crear_parametros_demo()
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("BASICO", "Sueldo básico", TipoConcepto.REMUNERATIVO, Dinero("800000.00")),
        Concepto("ANTIGUEDAD", "Antigüedad", TipoConcepto.REMUNERATIVO, Dinero("100000.00")),
        Concepto("PRESENTISMO", "Presentismo", TipoConcepto.REMUNERATIVO, Dinero("100000.00")),
        Concepto("APORTE_JUBILACION", "Jubilación (11%)", TipoConcepto.DEDUCCION, Dinero("110000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo)

    # 10 Bases Imponibles esperadas
    assert bases[0] == Decimal("1000000.00")  # Base 1: SIPA Aportes
    assert bases[1] == Decimal("1000000.00")  # Base 2: SIPA Patronal
    assert bases[2] == Decimal("1000000.00")  # Base 3: AAFF/FNE/RENATRE Patronal
    assert bases[3] == Decimal("1000000.00")  # Base 4: OS Aportes
    assert bases[4] == Decimal("1000000.00")  # Base 5: INSSJP Aportes
    assert bases[5] == Decimal("0.00")        # Base 6: Reg. Diferencial Aportes
    assert bases[6] == Decimal("0.00")        # Base 7: Reg. Diferencial Contrib.
    assert bases[7] == Decimal("1000000.00")  # Base 8: OS Patronal
    assert bases[8] == Decimal("1000000.00")  # Base 9: LRT/ART Patronal
    assert bases[9] == Decimal("992997.00")   # Base 10: Neto Ley 27.541 ($1.000.000 - $7.003)


def test_ejemplo_b_mes_sac_diciembre():
    emp = _crear_empleado_demo()
    params = _crear_parametros_demo()
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("BASICO", "Sueldo básico", TipoConcepto.REMUNERATIVO, Dinero("1000000.00")),
        Concepto("SAC", "SAC Diciembre", TipoConcepto.REMUNERATIVO, Dinero("500000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, Periodo(2026, 12), "sac", conceptos)

    bases = calcular_bases_lsd(resultado, emp, cct, params, Periodo(2026, 12))

    assert bases[0] == Decimal("1500000.00")  # Base 1: SIPA Aportes ($1.000.000 sueldo + $500.000 SAC)
    assert bases[1] == Decimal("1500000.00")  # Base 2: SIPA Patronal
    assert bases[3] == Decimal("1500000.00")  # Base 4: OS Aportes
    assert bases[4] == Decimal("1500000.00")  # Base 5: INSSJP Aportes
    assert bases[8] == Decimal("1500000.00")  # Base 9: LRT/ART
    # Base 10: $1.500.000 - ($7.003 + $3.501.50) = $1.489.495.50
    assert bases[9] == Decimal("1489495.50")  # Base 10: Neto Ley 27.541


def test_ejemplo_c_vacaciones_y_sueldo():
    emp = _crear_empleado_demo()
    params = _crear_parametros_demo()
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("BASICO", "Sueldo básico", TipoConcepto.REMUNERATIVO, Dinero("400000.00")),
        Concepto("VACACIONES", "Adelanto vacaciones (14 días)", TipoConcepto.REMUNERATIVO, Dinero("350000.00"), cantidad=Decimal("14")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo)

    assert bases[0] == Decimal("750000.00")  # Base 1: SIPA Aportes ($400.000 + $350.000)
    assert bases[1] == Decimal("750000.00")  # Base 2: SIPA Patronal
    assert bases[3] == Decimal("750000.00")  # Base 4: OS Aportes
    assert bases[8] == Decimal("750000.00")  # Base 9: LRT/ART
    assert bases[9] == Decimal("742997.00")  # Base 10: Neto Ley 27.541 ($750.000 - $7.003)


def test_ejemplo_d_jornada_parcial_guia14():
    emp = _crear_empleado_demo(proporcion_jornada=Decimal("0.5"))
    params = ParametrosPeriodoLSD(
        periodo=Periodo(2026, 7),
        tope_min_sipa=Dinero("50000.00"),
        tope_max_sipa_mensual=Dinero("2000000.00"),
        tope_max_sipa_sac=Dinero("1000000.00"),
        piso_obra_social=Dinero("600000.00"),  # Piso mínimo exigible Guía 14
        detraccion_ley27541_mensual=Dinero("7003.00"),
        detraccion_ley27541_sac=Dinero("3501.50"),
    )
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("BASICO", "Sueldo básico 4hs", TipoConcepto.REMUNERATIVO, Dinero("400000.00")),
        Concepto("SANIDAD_SUMA_NR_JUN_JUL", "Suma NR FATSA", TipoConcepto.NO_REMUNERATIVO, Dinero("50000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo)

    # Base 3 (AAFF/FNE): $400.000 (remunerativo sin piso forzado)
    assert bases[2] == Decimal("400000.00")
    # Base 4 (OS Aportes): $450.000 devengado + $150.000 base diferencial = $600.000
    assert bases[3] == Decimal("600000.00")
    # Base 8 (OS Patronal): $450.000 devengado + $150.000 base diferencial = $600.000
    assert bases[7] == Decimal("600000.00")


def test_ejemplo_e_regimen_diferencial():
    emp = _crear_empleado_demo(es_regimen_diferencial=True)
    params = _crear_parametros_demo()
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("BASICO", "Sueldo básico insalubre", TipoConcepto.REMUNERATIVO, Dinero("1000000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    override = {
        "BASICO": ConceptoARCA("110000", GrupoARCA.REMUNERATIVO, "Sueldo básico insalubre", admite_regimen_diferencial=True, verificado=True)
    }
    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo, overrides_empleador=override)

    # Bases 6 y 7 en Régimen Diferencial
    assert bases[5] == Decimal("1000000.00")  # Base 6 (Diferencial Aporte)
    assert bases[6] == Decimal("1000000.00")  # Base 7 (Diferencial Contribución)


def test_concepto_sin_incidencias_no_contamina_bases():
    emp = _crear_empleado_demo()
    params = ParametrosPeriodoLSD(
        periodo=Periodo(2026, 7),
        tope_min_sipa=Dinero("0.00"),
        tope_max_sipa_mensual=Dinero("2000000.00"),
        tope_max_sipa_sac=Dinero("1000000.00"),
        piso_obra_social=Dinero("0.00"),
        detraccion_ley27541_mensual=Dinero("0.00"),
        detraccion_ley27541_sac=Dinero("0.00"),
    )
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    # Concepto nuevo con incidencias por defecto (todas False)
    conceptos = [
        Concepto("NUEVO_CONCEPTO_DESCONOCIDO", "Suma experimental", TipoConcepto.NO_REMUNERATIVO, Dinero("500000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    from infrastructure.lsd.catalogo_afip import IncidenciasSubsistemasARCA
    override = {
        "NUEVO_CONCEPTO_DESCONOCIDO": ConceptoARCA(
            codigo_tipo_arca="540000",
            grupo=GrupoARCA.NO_REMUNERATIVO,
            descripcion="Suma experimental",
            incidencias=IncidenciasSubsistemasARCA(),  # Todas False por defecto
            verificado=True
        )
    }
    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo, overrides_empleador=override)

    # NINGUNA Base (1 a 10) debe incrementarse por este concepto
    for i in range(10):
        assert bases[i] == Decimal("0.00"), f"Base {i+1} fue contaminada: {bases[i]}"


def test_ejemplo_f_sac_proporcional_codigo_120003():
    emp = _crear_empleado_demo()
    params = _crear_parametros_demo()
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    # SAC proporcional (10 días)
    conceptos = [
        Concepto("SAC_PROP", "SAC Proporcional Desvinculación", TipoConcepto.REMUNERATIVO, Dinero("700000.00"), cantidad=Decimal("10")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "final", conceptos)

    from infrastructure.lsd.catalogo_afip import ClaseTopeARCA, IncidenciasSubsistemasARCA
    _INC_REM = IncidenciasSubsistemasARCA(integra_sipa=True, integra_inssjyp=True, integra_aaff_fne=True, integra_obra_social=True, integra_lrt=True)
    override = {
        "SAC_PROP": ConceptoARCA("120003", GrupoARCA.REMUNERATIVO, "SAC Proporcional", incidencias=_INC_REM, clase_tope=ClaseTopeARCA.SAC_PROPORCIONAL, requiere_cantidad_dias=True, verificado=True)
    }
    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo, overrides_empleador=override)

    # Tope SAC proporcional: ($2.000.000 / 30) * 10 = $666.666,67 (evaluado de forma independiente sin mezclarse con SAC semestral)
    assert bases[0] == Decimal("666666.67")  # Base 1 (SIPA Aportes topada en $666.666,67)
    assert bases[1] == Decimal("700000.00")  # Base 2 (SIPA Patronal sin tope máx)


def test_ejemplo_g_no_remunerativo_solo_obra_social():
    emp = _crear_empleado_demo()
    params = _crear_parametros_demo()
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("BASICO", "Sueldo básico", TipoConcepto.REMUNERATIVO, Dinero("500000.00")),
        Concepto("SANIDAD_SUMA_NR_JUN_JUL", "Suma NR FATSA (Solo OS)", TipoConcepto.NO_REMUNERATIVO, Dinero("100000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo)

    assert bases[0] == Decimal("500000.00")  # Base 1 (SIPA Aportes: solo remunerativos)
    assert bases[2] == Decimal("500000.00")  # Base 3 (AAFF/FNE: solo remunerativos)
    assert bases[3] == Decimal("600000.00")  # Base 4 (OS Aportes: $500k Rem + $100k NR OS)
    assert bases[7] == Decimal("600000.00")  # Base 8 (OS Patronal: $500k Rem + $100k NR OS)


def test_ejemplo_h_base10_detraccion_y_piso_minimo():
    emp = _crear_empleado_demo()
    params = ParametrosPeriodoLSD(
        periodo=Periodo(2026, 7),
        tope_min_sipa=Dinero("50000.00"),
        tope_max_sipa_mensual=Dinero("2000000.00"),
        tope_max_sipa_sac=Dinero("1000000.00"),
        piso_obra_social=Dinero("50000.00"),
        detraccion_ley27541_mensual=Dinero("7003.00"),
        detraccion_ley27541_sac=Dinero("3501.50"),
    )
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("BASICO", "Sueldo básico muy bajo", TipoConcepto.REMUNERATIVO, Dinero("10000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo)

    assert bases[1] == Decimal("50000.00")  # Base 2 (SIPA Patronal topada al piso mínimo de $50.000)
    # Base 10: $50.000 - $7.003 = $42.997, pero no puede quedar por debajo del tope_min_sipa de $50.000
    assert bases[9] == Decimal("50000.00")  # Base 10 retenida en el piso previsional mínimo de $50.000


def test_ejemplo_i_descuento_no_contamina_ninguna_base():
    emp = _crear_empleado_demo()
    params = ParametrosPeriodoLSD(
        periodo=Periodo(2026, 7),
        tope_min_sipa=Dinero("0.00"),
        tope_max_sipa_mensual=Dinero("2000000.00"),
        tope_max_sipa_sac=Dinero("1000000.00"),
        piso_obra_social=Dinero("0.00"),
        detraccion_ley27541_mensual=Dinero("0.00"),
        detraccion_ley27541_sac=Dinero("0.00"),
    )
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    conceptos = [
        Concepto("APORTE_JUBILACION", "Aporte jubilatorio (descuento)", TipoConcepto.DEDUCCION, Dinero("110000.00")),
        Concepto("CUOTA_SINDICAL", "Cuota sindical (descuento)", TipoConcepto.DEDUCCION, Dinero("20000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, params.periodo, "mensual", conceptos)

    bases = calcular_bases_lsd(resultado, emp, cct, params, params.periodo)

    # NINGUN descuento del trabajador suma a las Bases Imponibles de haberes (1 a 10)
    for i in range(10):
        assert bases[i] == Decimal("0.00"), f"Base {i+1} fue contaminada por un descuento: {bases[i]}"


if __name__ == "__main__":
    test_ejemplo_a_mensual_normal()
    test_ejemplo_b_mes_sac_diciembre()
    test_ejemplo_c_vacaciones_y_sueldo()
    test_ejemplo_d_jornada_parcial_guia14()
    test_ejemplo_e_regimen_diferencial()
    test_concepto_sin_incidencias_no_contamina_bases()
    test_ejemplo_f_sac_proporcional_codigo_120003()
    test_ejemplo_g_no_remunerativo_solo_obra_social()
    test_ejemplo_h_base10_detraccion_y_piso_minimo()
    test_ejemplo_i_descuento_no_contamina_ninguna_base()
    print("✅ TODOS LOS TESTS DE GUIA 18 Y GUIA 14 (10 BASES ARCA) PASAN PERFECTAMENTE")
