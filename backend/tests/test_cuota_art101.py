"""Resolución data-driven de la cuota Art. 101 por CCT + localidad/filial + vigencia.
El motor NO se toca: se prueba la función pura de resolución y que la cuota resuelta,
inyectada con ParametroSet.con_extra, la aplica el motor como ded_afil.
"""
import os, sys
from datetime import date
from decimal import Decimal as D
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from domain.entities.parametros import (
    CuotaArt101, resolver_cuota_art101, ParametroLegal as P, ParametroSet,
    EscalaSalarial, AmparoSet,
)
from domain.entities.empleado import Empleado
from domain.payroll_engine.engine import MotorLiquidacion
from domain.payroll_engine.config import CctConfig
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo

F = date(2026,7,28)
def c(pct, loc=None, fil=None, ver=True, vf=date(2026,1,1), vt=None, cct="130/75"):
    return CuotaArt101(cct, D(pct), vf, vt, "FAECYS", fil, loc, "acta filial", ver)

CANDS = [
    c("0.02", loc="CABA"),
    c("0.03", loc="Rosario"),
    c("0.05", loc="CABA", ver=False),                 # no verificada -> nunca
    c("0.04", loc="Córdoba", vt=date(2026,6,30)),      # vencida -> nunca en jul
    c("0.025", fil="Filial Norte"),
]

def test_match_por_localidad():
    r = resolver_cuota_art101(CANDS, "130/75", "CABA", None, F)
    assert r is not None and r.porcentaje == D("0.02")

def test_localidad_distinta():
    assert resolver_cuota_art101(CANDS, "130/75", "Rosario", None, F).porcentaje == D("0.03")

def test_sin_match_devuelve_none():
    assert resolver_cuota_art101(CANDS, "130/75", "Mendoza", None, F) is None

def test_no_verificada_no_se_elige():
    # CABA verificada 2% gana; la 5% no verificada nunca
    assert resolver_cuota_art101(CANDS, "130/75", "CABA", None, F).porcentaje == D("0.02")

def test_vencida_no_se_elige():
    assert resolver_cuota_art101(CANDS, "130/75", "Córdoba", None, F) is None

def test_prioridad_filial_sobre_localidad():
    r = resolver_cuota_art101(CANDS, "130/75", "CABA", "Filial Norte", F)
    assert r.porcentaje == D("0.025")   # filial gana

def test_cct_distinto_no_matchea():
    assert resolver_cuota_art101(CANDS, "999/99", "CABA", None, F) is None

# --- Integración: resolver -> con_extra -> motor (sin tocar el motor) ---
def _base():
    return ParametroSet([
        P("APORTE_JUBILACION", D("0.11"),"%","empleado",date(2026,1,1)),
        P("APORTE_LEY19032",  D("0.03"),"%","empleado",date(2026,1,1)),
        P("APORTE_OBRA_SOCIAL",D("0.03"),"%","empleado",date(2026,1,1)),
        P("APORTE_MODERNIZACION",D("0.01"),"%","empleado",date(2026,1,1)),
        P("CONTRIB_JUBILACION",D("0.18"),"%","empleador",date(2026,1,1)),
        P("CONTRIB_OBRA_SOCIAL",D("0.06"),"%","empleador",date(2026,1,1)),
        P("APORTE_SINDICAL_ART100_130/75",D("0.02"),"%","ded_todos",date(2026,3,1),None,True,"","130/75"),
        P("APORTE_FAECYS_ART100_130/75", D("0.005"),"%","ded_todos",date(2026,3,1),None,True,"","130/75"),
    ])
CCT = CctConfig("130/75",D("0.01"),D("12"),D("200"),aplica_presentismo=True,aplica_cuota_sindical=False,cuota_sindical_pct=None)
ESC = EscalaSalarial("130/75","Maestranza A",Dinero(D("1137023")),date(2026,7,1),None,True,"")
def emp(): return Empleado("Ana","D",Cuil("20111111112"),date(2021,7,1),"130/75","Maestranza A","1",afiliado_sindicato=True)
def find(r,cod): return next((x for x in r.conceptos if x.codigo==cod),None)

def test_sin_cuota_no_hay_art101_pero_si_art100():
    r = MotorLiquidacion(_base(), AmparoSet()).liquidar_mensual(emp(),Periodo(2026,7),ESC,CCT,a_fecha=F)
    assert find(r,"APORTE_SINDICAL_ART100_130/75") is not None   # art100 igual
    assert find(r,"CUOTA_SINDICAL_ART101_130/75") is None        # sin cuota: no inventa

def test_con_cuota_resuelta_se_aplica_art101():
    cuota = resolver_cuota_art101(CANDS,"130/75","CABA",None,F)
    ps = _base().con_extra(P(f"CUOTA_SINDICAL_ART101_130/75",cuota.porcentaje,"%","ded_afil",
                            cuota.valid_from,cuota.valid_to,True,cuota.fuente,"130/75",{}))
    r = MotorLiquidacion(ps, AmparoSet()).liquidar_mensual(emp(),Periodo(2026,7),ESC,CCT,a_fecha=F)
    from domain.entities.concepto import TipoConcepto
    art101 = find(r,"CUOTA_SINDICAL_ART101_130/75")
    assert art101 is not None
    base_sind = sum((x.importe.monto for x in r.conceptos if x.tipo==TipoConcepto.REMUNERATIVO), D("0"))
    assert art101.importe.monto == Dinero(base_sind).porcentaje(D("0.02")).redondear().monto

if __name__=="__main__":
    for name,fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok",name)
    print("OK resolver Art.101 (localidad/filial/vigencia) + integración motor")
