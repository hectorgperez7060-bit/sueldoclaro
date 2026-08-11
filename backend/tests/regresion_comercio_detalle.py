"""Regresión Comercio 130/75 con DETALLE concepto por concepto (valores de producción).
Caso A: Maestranza A, jul-2026, 5 años, jornada completa, NO afiliado -> 2% + 0,5%, sin art.101.
Caso B: mismo empleado AFILIADO -> 2% + 0,5% + cuota art.101.
Parámetros idénticos a la BD (Supabase) al 06/08/2026.
"""
import os, sys
from datetime import date
from decimal import Decimal as D
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from domain.entities.empleado import Empleado
from domain.entities.parametros import ParametroLegal as P, ParametroSet, EscalaSalarial, AmparoSet, Amparo
from domain.entities.concepto import TipoConcepto
from domain.payroll_engine.engine import MotorLiquidacion
from domain.payroll_engine.config import CctConfig
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo

VF = date(2026,1,1)
INC_NR = {"integra_antiguedad":True,"integra_presentismo":True,"aporte_jubilacion":False,
          "aporte_obra_social":True,"aporte_sindicato":True}
INC_BONO = {"integra_antiguedad":False,"integra_presentismo":False,"aporte_jubilacion":False,
            "aporte_obra_social":False,"aporte_sindicato":False}

def params():
    return ParametroSet([
        P("APORTE_JUBILACION", D("0.11"), "%", "empleado", VF),
        P("APORTE_LEY19032",  D("0.03"), "%", "empleado", VF),
        P("APORTE_OBRA_SOCIAL",D("0.03"), "%", "empleado", VF),
        P("APORTE_MODERNIZACION",D("0.01"),"%","empleado", VF),
        P("TOPE_SIPA", D("9000000"), "ARS", "empleado", VF),
        P("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", VF),
        P("CONTRIB_OBRA_SOCIAL",D("0.06"), "%", "empleador", VF),
        P("CONTRIB_INSSJP", D("0.015"), "%", "empleador", VF),
        P("CONTRIB_ASIG_FAM", D("0.047"), "%", "empleador", VF),
        P("COMERCIO_NR1_130/75", D("100000"), "ARS","no_rem", date(2026,7,1), date(2026,11,30), True,"","130/75",INC_NR),
        P("COMERCIO_NR2_130/75", D("20000"),  "ARS","no_rem", date(2026,7,1), date(2026,11,30), True,"","130/75",INC_NR),
        P("COMERCIO_BONO_130/75",D("25000"),  "ARS","no_rem", date(2026,7,1), date(2026,8,31),  True,"","130/75",INC_BONO),
        P("APORTE_SINDICAL_ART100_130/75", D("0.02"),  "%","ded_todos", date(2026,3,1), None, True,"","130/75"),
        P("APORTE_FAECYS_ART100_130/75",   D("0.005"), "%","ded_todos", date(2026,3,1), None, True,"","130/75"),
        P("CUOTA_SINDICAL_ART101_130/75",  D("0.02"),  "%","ded_afil",  date(2026,1,1), None, False,"","130/75"),
    ])

AMP = AmparoSet([Amparo("130/75","L27802:131","APORTE_MODERNIZACION","vigente",date(2026,3,1),date(2026,9,30))])
CCT = CctConfig("130/75", D("0.01"), D("12"), D("200"), aplica_presentismo=True,
                aplica_cuota_sindical=False, cuota_sindical_pct=D("0.02"))
ESC = EscalaSalarial("130/75","Maestranza A", Dinero(D("1137023")), date(2026,7,1), None, True, "FAECYS 22/07/2026")

def emp(afil):
    return Empleado("Juan","Perez",Cuil("20111111112"),date(2021,7,1),"130/75","Maestranza A","1",afiliado_sindicato=afil)

ORDEN = ["BASICO","COMERCIO_NR1_130/75","COMERCIO_NR2_130/75","COMERCIO_BONO_130/75","ANTIGUEDAD","PRESENTISMO",
         "APORTE_JUBILACION","APORTE_LEY19032","APORTE_OBRA_SOCIAL",
         "APORTE_SINDICAL_ART100_130/75","APORTE_FAECYS_ART100_130/75","CUOTA_SINDICAL_ART101_130/75","APORTE_MODERNIZACION"]

def show(nombre, afil):
    r = MotorLiquidacion(params(), AMP).liquidar_mensual(emp(afil), Periodo(2026,7), ESC, CCT, a_fecha=date(2026,7,28))
    by = {c.codigo:c for c in r.conceptos}
    print("="*70); print(f"{nombre}  (afiliado={afil})"); print("="*70)
    rem=nr=ded=D("0")
    for cod in ORDEN:
        c = by.get(cod)
        if not c: 
            print(f"  {cod:<34}  --- (no aplica)"); continue
        signo = "-" if c.tipo==TipoConcepto.DEDUCCION else "+"
        print(f"  {c.descripcion:<40} {c.codigo:<30} {signo}{c.importe.monto:>14,.2f}")
        if c.tipo==TipoConcepto.REMUNERATIVO: rem+=c.importe.monto
        elif c.tipo==TipoConcepto.NO_REMUNERATIVO: nr+=c.importe.monto
        elif c.tipo==TipoConcepto.DEDUCCION: ded+=c.importe.monto
    neto = rem+nr-ded
    print("-"*70)
    print(f"  {'Total remunerativo':<40} {'':<30}  {rem:>15,.2f}")
    print(f"  {'Total no remunerativo':<40} {'':<30}  {nr:>15,.2f}")
    print(f"  {'Total deducciones':<40} {'':<30} -{ded:>14,.2f}")
    print(f"  {'NETO A PAGAR':<40} {'':<30}  {neto:>15,.2f}")
    return by, neto

byA, netoA = show("CASO A - NO AFILIADO", False)
byB, netoB = show("CASO B - AFILIADO", True)

# Asserts de regresión
def m(by,cod): 
    return by[cod].importe.monto if cod in by else None
BASE_SIND = D("1429863.66")
assert m(byA,"APORTE_SINDICAL_ART100_130/75")==Dinero(BASE_SIND).porcentaje(D("0.02")).redondear().monto
assert m(byA,"APORTE_FAECYS_ART100_130/75")==Dinero(BASE_SIND).porcentaje(D("0.005")).redondear().monto
assert "CUOTA_SINDICAL_ART101_130/75" not in byA, "A no debe tener art.101"
assert "CUOTA_SINDICAL" not in byA, "cuota vieja apagada"
assert m(byB,"APORTE_SINDICAL_ART100_130/75")==m(byA,"APORTE_SINDICAL_ART100_130/75")
assert m(byB,"APORTE_FAECYS_ART100_130/75")==m(byA,"APORTE_FAECYS_ART100_130/75")
assert m(byB,"CUOTA_SINDICAL_ART101_130/75")==Dinero(BASE_SIND).porcentaje(D("0.02")).redondear().monto
assert m(byB,"APORTE_MODERNIZACION")==D("0.00"), "modernizacion suspendida por amparo"
print("\nOK ambos casos: A=2%+0,5% sin art.101 ; B=2%+0,5%+art.101 ; modernizacion suspendida")
