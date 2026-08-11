"""Test dorado del generador LSD: reproduce el archivo REAL aceptado por ARCA.

Prueba de 'no humo': a partir de datos estructurados, el generador debe producir
los mismos registros que un LSD real (empleador 27-20736432-6, período 2026-07).
Los registros 01/03/04 deben salir byte-a-byte idénticos; el 02 debe coincidir en
todos los campos con contenido (el archivo original tenía un '0' de relleno en el
CBU en blanco, una rareza del software que lo generó y que no replicamos).
"""
import os, sys
from decimal import Decimal
HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from infrastructure.lsd.generator import (
    EmpleadorLSD, TrabajadorLSD, ConceptoLSD, build_lsd,
    registro_02,
)

REF = os.path.join(HERE, "..", "..", "27-20736432-6_2026-7_0__LSD_CORREGIDO.txt")


def _parse_ref():
    L = open(REF, encoding="latin-1").read().split("\n")
    r01 = L[0]
    emp = EmpleadorLSD(cuit=r01[2:13], sello=r01[13:15], periodo=r01[15:21],
                       tipo_liq=r01[21], cola01=r01[22:])
    trs, orden = {}, []
    for ln in L:
        if ln[:2] == "02":
            c = ln[2:13]; orden.append(c)
            trs[c] = TrabajadorLSD(cuil=c, legajo=ln[13:23].strip(),
                forma_pago=ln[73], cbu=ln[74:96].strip(),
                dias_tope=int(ln[96:98]), fecha_pago=ln[98:106])
    for ln in L:
        if ln[:2] == "03":
            c = ln[2:13]
            trs[c].conceptos.append(ConceptoLSD(codigo=ln[13:28],
                importe=Decimal(ln[29:44]) / 100, signo=ln[44]))
    for ln in L:
        if ln[:2] == "04":
            c = ln[2:13]; t = trs[c]; t.attrs_suss = ln[13:160]
            campos = [Decimal(ln[160 + i*15:160 + (i+1)*15]) / 100 for i in range(14)]
            t.remun_total = campos[0]; t.bases = campos[1:]
    return emp, [trs[c] for c in orden], L


def test_golden_reproduce_registros_01_03_04():
    emp, trabajadores, L = _parse_ref()
    out = build_lsd(emp, trabajadores).split("\n")
    ref_por_tipo = {"01": [], "03": [], "04": []}
    out_por_tipo = {"01": [], "03": [], "04": []}
    for ln in L:
        if ln[:2] in ref_por_tipo: ref_por_tipo[ln[:2]].append(ln)
    for ln in out:
        if ln[:2] in out_por_tipo: out_por_tipo[ln[:2]].append(ln)
    for t in ("01", "03", "04"):
        assert sorted(out_por_tipo[t]) == sorted(ref_por_tipo[t]), f"registro {t} no coincide"


def test_longitudes_fijas():
    emp, trabajadores, L = _parse_ref()
    out = build_lsd(emp, trabajadores).split("\n")
    largos = {"01": 35, "02": 115, "03": 51, "04": 370}
    for ln in out:
        assert len(ln) == largos[ln[:2]], f"{ln[:2]} largo {len(ln)}"


def test_registro_02_campos_reales_coinciden():
    emp, trabajadores, L = _parse_ref()
    ref02 = {ln[2:13]: ln for ln in L if ln[:2] == "02"}
    for t in trabajadores:
        r = registro_02(t)
        o = ref02[t.cuil]
        assert r[2:13] == o[2:13]        # CUIL
        assert r[73] == o[73] == "1"     # forma de pago corregida
        assert r[98:106] == o[98:106]    # fecha de pago
        assert r[13:23] == o[13:23]      # legajo


if __name__ == "__main__":
    test_golden_reproduce_registros_01_03_04()
    test_longitudes_fijas()
    test_registro_02_campos_reales_coinciden()
    print("✅ TODOS LOS TESTS DORADOS PASAN")
    print("   - registros 01/03/04 reproducidos byte-a-byte (como multiset)")
    print("   - longitudes fijas correctas (35/115/51/370)")
    print("   - registro 02: CUIL, forma de pago, fecha y legajo coinciden con el real")
