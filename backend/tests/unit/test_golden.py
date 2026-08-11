"""Golden tests del motor de cálculo.

Los casos viven en archivos YAML legibles por un contador (carpeta ``golden/``).
Cada archivo declara la entrada y la salida esperada concepto por concepto,
incluyendo el mismo caso con y sin amparo vigente (deben dar distinto y trazable).
"""
import glob
import os
from datetime import date
from decimal import Decimal

import pytest
import yaml

from domain.entities.empleado import Empleado
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from parametros_seed import (
    amparos_faecys,
    cct_comercio_13075,
    escala_comercio,
    parametros_ejemplo,
    sin_amparos,
)

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
CASOS = sorted(glob.glob(os.path.join(GOLDEN_DIR, "*.yaml")))


def _fecha(s: str) -> date:
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def _construir_empleado(d: dict) -> Empleado:
    return Empleado(
        nombre="Test",
        apellido="Golden",
        cuil=Cuil(d["cuil"]),
        fecha_ingreso=_fecha(d["fecha_ingreso"]),
        cct_numero=d["cct"],
        categoria=d["categoria"],
        legajo="1",
        afiliado_sindicato=d.get("afiliado", True),
    )


@pytest.mark.parametrize("ruta", CASOS, ids=[os.path.basename(c) for c in CASOS])
def test_golden(ruta):
    with open(ruta, encoding="utf-8") as f:
        caso = yaml.safe_load(f)

    empleado = _construir_empleado(caso["empleado"])
    periodo = Periodo.desde_texto(caso["periodo"])
    params = parametros_ejemplo()
    amparos = amparos_faecys() if caso.get("amparo_vigente") else sin_amparos()
    motor = MotorLiquidacion(params, amparos)
    cct = cct_comercio_13075()
    escala = escala_comercio(caso["empleado"]["categoria"], caso["escala_basico"])

    tipo = caso["tipo"]
    if tipo == "mensual":
        nv = caso.get("novedades", {}) or {}
        novedades = Novedades(
            horas_extra_50=Decimal(str(nv.get("horas_extra_50", "0"))),
            horas_extra_100=Decimal(str(nv.get("horas_extra_100", "0"))),
        )
        res = motor.liquidar_mensual(empleado, periodo, escala, cct, novedades)
    elif tipo == "sac":
        s = caso["sac"]
        res = motor.liquidar_sac(
            empleado, periodo,
            Dinero(Decimal(s["mejor_remuneracion"])),
            int(s.get("dias_trabajados", 181)),
        )
    elif tipo == "vacaciones":
        v = caso["vacaciones"]
        res = motor.liquidar_vacaciones(
            empleado, periodo, Dinero(Decimal(v["remuneracion_habitual"]))
        )
    else:
        pytest.fail(f"Tipo de liquidación desconocido: {tipo}")

    # Conceptos individuales
    for codigo, esperado in (caso.get("esperado_conceptos") or {}).items():
        c = res.concepto(codigo)
        assert c.importe.monto == Decimal(esperado), (
            f"[{os.path.basename(ruta)}] {codigo}: {c.importe.monto} != {esperado}"
        )

    # Totales
    tot = caso.get("esperado_totales") or {}
    if "remunerativo" in tot:
        assert res.total_remunerativo.monto == Decimal(tot["remunerativo"])
    if "deducciones" in tot:
        assert res.total_deducciones.monto == Decimal(tot["deducciones"])
    if "neto" in tot:
        assert res.neto.monto == Decimal(tot["neto"])

    # Régimen aplicado (trazabilidad de amparos)
    for codigo, reg in (caso.get("esperado_regimen") or {}).items():
        assert res.concepto(codigo).regimen.value == reg, (
            f"[{os.path.basename(ruta)}] régimen {codigo}"
        )
    for codigo, art in (caso.get("esperado_articulo") or {}).items():
        assert res.concepto(codigo).articulo_amparo == art


def test_hay_casos_golden():
    assert CASOS, "No se encontraron casos golden en la carpeta golden/"


def test_amparo_cambia_resultado():
    """El mismo empleado con y sin amparo debe dar netos distintos y trazables."""
    empleado = _construir_empleado({
        "cuil": "20123456786", "fecha_ingreso": "2021-07-01",
        "cct": "130/75", "categoria": "Administrativo A", "afiliado": True,
    })
    periodo = Periodo.desde_texto("2026-07")
    params = parametros_ejemplo()
    cct = cct_comercio_13075()
    escala = escala_comercio("Administrativo A", "500000.00")

    sin = MotorLiquidacion(params, sin_amparos()).liquidar_mensual(empleado, periodo, escala, cct)
    con = MotorLiquidacion(params, amparos_faecys()).liquidar_mensual(empleado, periodo, escala, cct)

    assert sin.neto.monto == Decimal("455000.00")
    assert con.neto.monto == Decimal("460687.50")
    assert con.neto.monto > sin.neto.monto  # el amparo suspende el aporte -> más neto
    assert con.concepto("APORTE_MODERNIZACION").regimen.value == "previa"
    assert sin.concepto("APORTE_MODERNIZACION").regimen.value == "ley_27802"
