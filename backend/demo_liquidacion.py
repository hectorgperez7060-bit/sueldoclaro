"""Demo de SUELDOCLARO - Fase 1 (motor de cálculo).

No necesita base de datos, ni Docker, ni instalar nada: solo Python.
Ejecuta una liquidación de ejemplo (Comercio 130/75) y muestra el recibo por
pantalla, con y sin el amparo judicial FAECYS, para ver la diferencia.

Uso:
    cd C:\\Users\\usuario\\OneDrive\\Favoritos\\sueldoClaeo\\backend
    python demo_liquidacion.py
"""
import os
import sys
from datetime import date
from decimal import Decimal

# Deja que Python encuentre el código del dominio y el seed.
BASE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(BASE, "src"))
sys.path.insert(0, os.path.join(BASE, "seed"))

from domain.entities.empleado import Empleado
from domain.entities.concepto import TipoConcepto
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.periodo import Periodo
from parametros_seed import (
    parametros_ejemplo, cct_comercio_13075, escala_comercio,
    amparos_faecys, sin_amparos,
)


def money(d):
    return f"$ {d.redondear().monto:>14,.2f}"


def mostrar(titulo, resultado):
    print("\n" + "=" * 60)
    print(f"  {titulo}")
    print("=" * 60)
    print(f"  {'CONCEPTO':32} {'IMPORTE':>16}")
    print("  " + "-" * 50)
    for c in resultado.conceptos:
        if c.tipo in (TipoConcepto.REMUNERATIVO, TipoConcepto.DEDUCCION):
            signo = "-" if c.tipo == TipoConcepto.DEDUCCION else " "
            marca = ""
            if c.regimen.value == "previa":
                marca = "  <-- SUSPENDIDO POR AMPARO"
            elif c.regimen.value == "ley_27802":
                marca = "  (Ley 27.802)"
            print(f"  {c.descripcion[:32]:32} {signo}{money(c.importe)}{marca}")
    print("  " + "-" * 50)
    print(f"  {'REMUNERATIVO (bruto)':32}  {money(resultado.total_remunerativo)}")
    print(f"  {'DEDUCCIONES':32} -{money(resultado.total_deducciones)}")
    print(f"  {'NETO A COBRAR':32}  {money(resultado.neto)}")


def main():
    empleado = Empleado(
        nombre="Juan", apellido="Pérez", cuil=Cuil("20123456786"),
        fecha_ingreso=date(2021, 7, 1), cct_numero="130/75",
        categoria="Administrativo A", legajo="0001",
    )
    periodo = Periodo.desde_texto("2026-07")
    params = parametros_ejemplo()
    cct = cct_comercio_13075()
    escala = escala_comercio("Administrativo A", "500000.00")

    print("\nSUELDOCLARO — Demo de liquidación (valores de EJEMPLO)")
    print(f"Empleado: {empleado.nombre} {empleado.apellido}  |  CUIL {empleado.cuil}")
    print(f"Convenio: Comercio 130/75  |  Categoría: {empleado.categoria}")
    print(f"Período: {periodo}  |  Antigüedad: {empleado.antiguedad_anios(date(2026,7,28))} años")

    sin = MotorLiquidacion(params, sin_amparos()).liquidar_mensual(empleado, periodo, escala, cct)
    con = MotorLiquidacion(params, amparos_faecys()).liquidar_mensual(empleado, periodo, escala, cct)

    mostrar("SIN amparo (rige la Ley 27.802)", sin)
    mostrar("CON amparo FAECYS (art. 131 suspendido)", con)

    dif = (con.neto - sin.neto).redondear()
    print("\n" + "=" * 60)
    print(f"  Diferencia de neto por el amparo: {money(dif)}")
    print("  (con el amparo, el trabajador cobra más porque no se le")
    print("   retiene el aporte de modernización)")
    print("=" * 60)

    # --- Media jornada (contrato a tiempo parcial, LCT art. 92 ter) ---
    empleado_media = Empleado(
        nombre="Ana", apellido="Gómez", cuil=Cuil("27123456780"),
        fecha_ingreso=date(2021, 7, 1), cct_numero="130/75",
        categoria="Administrativo A", legajo="0002",
        proporcion_jornada=Decimal("0.5"),  # media jornada
    )
    media = MotorLiquidacion(params, sin_amparos()).liquidar_mensual(
        empleado_media, periodo, escala, cct
    )
    mostrar("MEDIA JORNADA (proporción 0,5) — mismo cargo", media)
    print("\n  Nota: todo el recibo se prorratea por la jornada (0,5).")
    print("  Las cargas patronales también bajan a la mitad, porque se")
    print("  calculan sobre la misma base reducida.")
    print("  Recordatorio legal: el tiempo parcial no puede superar 2/3 de")
    print("  la jornada completa; y debe reflejar la jornada REAL trabajada.")
    print("\n⚠  Recordá: los valores son de EJEMPLO (is_verified=False).")
    print("   No usar para liquidaciones reales sin verificación de un contador.\n")


if __name__ == "__main__":
    main()
