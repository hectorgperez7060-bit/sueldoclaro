"""Prueba End-to-End (E2E) de integración entre generator.py y calculator.py.

Demuestra que cuando generator.py arma el Registro 04 sin bases explícitas,
invoca dinámicamente a calculator.py y escribe en el archivo .txt las 10 Bases
Imponibles exactas en el formato numérico de ancho fijo de ARCA (posiciones 175..324).
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
from infrastructure.lsd.generator import TrabajadorLSD, registro_04


def test_e2e_registro_04_bases_dinamicas_calculator():
    emp = Empleado(
        nombre="Juan",
        apellido="Pérez",
        cuil=Cuil("27-30732466-6"),
        fecha_ingreso=date(2020, 1, 1),
        cct_numero="130/75",
        categoria="Administrativo A",
        legajo="EMP001",
    )
    periodo = Periodo(2026, 12)
    params_lsd = ParametrosPeriodoLSD(
        periodo=periodo,
        tope_min_sipa=Dinero("50000.00"),
        tope_max_sipa_mensual=Dinero("2000000.00"),
        tope_max_sipa_sac=Dinero("1000000.00"),
        piso_obra_social=Dinero("100000.00"),
        detraccion_ley27541_mensual=Dinero("7003.00"),
        detraccion_ley27541_sac=Dinero("3501.50"),
    )
    cct = CctConfig(
        cct_numero="130/75",
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
    )

    # Liquidación con Sueldo ($1.000.000) y SAC ($500.000)
    conceptos = [
        Concepto("BASICO", "Sueldo básico", TipoConcepto.REMUNERATIVO, Dinero("1000000.00")),
        Concepto("SAC", "SAC Diciembre", TipoConcepto.REMUNERATIVO, Dinero("500000.00")),
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, periodo, "sac", conceptos)

    # 1. Instanciar TrabajadorLSD SIN bases predefinidas (list vacía)
    trabajador_lsd = TrabajadorLSD(
        cuil=emp.cuil.valor,
        legajo=emp.legajo,
        remun_total=Decimal("1500000.00"),
        attrs_suss=" " * 147,
        bases=[],  # Vacio -> Obliga a resolver con calculator.py
        resultado_liquidacion=resultado,
        empleado=emp,
        cct=cct,
        parametros_lsd=params_lsd,
    )

    # 2. Generar Registro 04 en texto (370 posiciones)
    linea_reg04 = registro_04(trabajador_lsd)

    # 3. Validaciones E2E
    assert len(linea_reg04) == 370, f"Longitud de Registro 04 inválida: {len(linea_reg04)}"
    assert linea_reg04.startswith("04"), "El registro debe comenzar con 04"

    # Posiciones: 0..1 ("04"), 2..12 (CUIL 11 chars), 13..159 (attrs_suss 147 chars) = total 160 chars
    # Posición 160..174: Remuneración Total (15 chars)
    remun_total_str = linea_reg04[160:175]
    print(f"DEBUG: remun_total_str = {remun_total_str!r} (len={len(remun_total_str)})")
    assert remun_total_str == "000000150000000", f"remun_total_str fue {remun_total_str!r}"

    # Posiciones 175..324: Las 10 Bases Imponibles de ARCA (15 pos c/u en centavos)
    bloque_bases = linea_reg04[175:325]
    bases_centavos = [bloque_bases[i:i+15] for i in range(0, 150, 15)]

    # Decodificar centavos a Decimal
    bases_e2e = [Decimal(b) / Decimal("100") for b in bases_centavos]

    # Calcular directamente con calculator.py para verificar coincidencia 1:1
    bases_esperadas = calcular_bases_lsd(resultado, emp, cct, params_lsd, periodo)

    print("=== VERIFICACION E2E REGISTRO 04 vs CALCULATOR.PY ===")
    for idx, (obtenida, esperada) in enumerate(zip(bases_e2e, bases_esperadas), 1):
        print(f"Base {idx:2d}: generada en TXT = ${obtenida:12.2f} | esperada = ${esperada:12.2f}")
        assert obtenida == esperada, f"Descalce en Base {idx}: {obtenida} != {esperada}"

    # Validaciones específicas por base y posición exacta en Registro 04:
    # Base 4 (OS Aportes): pos 220..234 (15 chars)
    # Base 6 (Diferencial Aportes): pos 250..264
    # Base 7 (Diferencial Contrib): pos 265..279
    # Base 8 (OS Patronal): pos 280..294
    # Base 10 (Neto Ley 27.541): pos 310..324
    assert bases_e2e[3] == Decimal("1500000.00"), f"Base 4 invalida: {bases_e2e[3]}"
    assert bases_e2e[5] == Decimal("0.00"), f"Base 6 invalida: {bases_e2e[5]}"
    assert bases_e2e[6] == Decimal("0.00"), f"Base 7 invalida: {bases_e2e[6]}"
    assert bases_e2e[7] == Decimal("1500000.00"), f"Base 8 invalida: {bases_e2e[7]}"
    assert bases_e2e[9] == Decimal("1489495.50"), f"Base 10 invalida: {bases_e2e[9]}"

    print("✅ PRUEBA E2E EXITOSA: Las 10 bases impresas en Registro 04 provienen 100% de calculator.py")


def test_e2e_registro_04_jornada_parcial_guia14():
    emp = Empleado(
        nombre="María",
        apellido="Gómez",
        cuil=Cuil("27-30732466-6"),
        fecha_ingreso=date(2020, 1, 1),
        cct_numero="130/75",
        categoria="Administrativo A",
        legajo="EMP002",
        proporcion_jornada=Decimal("0.5"),
    )
    periodo = Periodo(2026, 7)
    params_lsd = ParametrosPeriodoLSD(
        periodo=periodo,
        tope_min_sipa=Dinero("50000.00"),
        tope_max_sipa_mensual=Dinero("2000000.00"),
        tope_max_sipa_sac=Dinero("1000000.00"),
        piso_obra_social=Dinero("600000.00"),  # Piso mínimo Guía 14
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
    ]
    resultado = ResultadoLiquidacion(emp.cuil.valor, periodo, "mensual", conceptos)

    trabajador_lsd = TrabajadorLSD(
        cuil=emp.cuil.valor,
        legajo=emp.legajo,
        remun_total=Decimal("400000.00"),
        attrs_suss=" " * 147,
        bases=[],
        resultado_liquidacion=resultado,
        empleado=emp,
        cct=cct,
        parametros_lsd=params_lsd,
    )

    linea_reg04 = registro_04(trabajador_lsd)

    # 370 posiciones en Registro 04
    assert len(linea_reg04) == 370

    bloque_bases = linea_reg04[175:325]
    bases_centavos = [bloque_bases[i:i+15] for i in range(0, 150, 15)]
    bases_e2e = [Decimal(b) / Decimal("100") for b in bases_centavos]

    # En Jornada Parcial, Base 4 y Base 8 deben incorporar los $200.000 de Base Diferencial OS (Guía 14)
    assert bases_e2e[3] == Decimal("600000.00"), f"Base 4 E2E falló: {bases_e2e[3]}"
    assert bases_e2e[7] == Decimal("600000.00"), f"Base 8 E2E falló: {bases_e2e[7]}"
    print("✅ PRUEBA E2E JORNADA PARCIAL EXITOSA: Base 4 y Base 8 impresas con Base Diferencial Guía 14")


if __name__ == "__main__":
    test_e2e_registro_04_bases_dinamicas_calculator()
    test_e2e_registro_04_jornada_parcial_guia14()
