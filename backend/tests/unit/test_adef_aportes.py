from datetime import date
from decimal import Decimal as D

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo

CANAL_ADEF = {
    "canal_pago": "Sistema de Aportes en Linea ADEF",
    "url_pago": "https://www.adef.org.ar/sistema-de-aportes-en-linea",
    "regla_vencimiento": "Fecha exacta segun la boleta emitida por ADEF",
    "fuente_pago": "CCT 414/05 art. 46 y Sistema de Aportes en Linea ADEF",
}


def _resultado(mes: int, afiliado: bool = False, cuota: D | None = None):
    desde = date(2026, 1, 1)
    params = [
        ParametroLegal("APORTE_JUBILACION", D("0"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0"), "%", "empleador", desde),
        ParametroLegal(
            "APORTE_ADEF_REM_414/05", D("0.02"), "%", "ded_todos", desde,
            cct_numero="414/05", incidencias={
                "base_deduccion": "remunerativa", "destino_pago": "ADEF",
                "codigo_boleta": "ADEF_APORTES", **CANAL_ADEF,
            },
        ),
        ParametroLegal(
            "APORTE_ADEF_ASISTENCIA_414/05", D("0.01"), "%", "ded_todos", desde,
            cct_numero="414/05", incidencias={
                "base_deduccion": "remunerativa", "meses_aplicacion": [6, 12],
                "destino_pago": "ADEF", "codigo_boleta": "ADEF_APORTES",
                **CANAL_ADEF,
            },
        ),
    ]
    if cuota is not None:
        params.append(ParametroLegal(
            "CUOTA_SINDICAL_ART47_414/05", cuota, "%", "ded_afil", desde,
            cct_numero="414/05", incidencias={
                "base_deduccion": "sindical", "destino_pago": "ADEF",
                "codigo_boleta": "ADEF_APORTES",
                "absorbe_codigos": ["APORTE_ADEF_REM_414/05"],
            },
        ))
    emp = Empleado(
        "Ana", "Farmacia", Cuil("27307324666"), date(2025, 1, 1),
        "414/05", "Empleado de Farmacia", "1", afiliado_sindicato=afiliado,
    )
    escala = EscalaSalarial(
        "414/05", emp.categoria, Dinero(D("1000000")), desde, is_verified=True,
    )
    config = CctConfig(
        "414/05", D("0"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
    )
    return MotorLiquidacion(ParametroSet(params), AmparoSet()).liquidar_mensual(
        emp, Periodo(2026, mes), escala, config, a_fecha=date(2026, mes, 28),
    )


def _concepto(resultado, codigo):
    return next((c for c in resultado.conceptos if c.codigo == codigo), None)


def test_adef_dos_por_ciento_se_aplica_todos_los_meses():
    aporte = _concepto(_resultado(7), "APORTE_ADEF_REM_414/05")
    assert aporte.importe.monto == D("20000.00")
    assert aporte.destino_pago == "ADEF"
    assert aporte.codigo_boleta == "ADEF_APORTES"
    assert aporte.canal_pago == "Sistema de Aportes en Linea ADEF"
    assert aporte.url_pago == "https://www.adef.org.ar/sistema-de-aportes-en-linea"
    assert aporte.regla_vencimiento == "Fecha exacta segun la boleta emitida por ADEF"
    assert aporte.fuente_pago.startswith("CCT 414/05 art. 46")


def test_asistencia_uno_por_ciento_solo_junio_y_diciembre():
    assert _concepto(_resultado(7), "APORTE_ADEF_ASISTENCIA_414/05") is None
    assert _concepto(_resultado(6), "APORTE_ADEF_ASISTENCIA_414/05").importe.monto == D("10000.00")
    assert _concepto(_resultado(12), "APORTE_ADEF_ASISTENCIA_414/05").importe.monto == D("10000.00")


def test_cuota_afiliado_absorbe_el_aporte_ordinario_del_dos_por_ciento():
    resultado = _resultado(7, afiliado=True, cuota=D("0.03"))
    aporte = _concepto(resultado, "APORTE_ADEF_REM_414/05")
    diferencia = _concepto(resultado, "CUOTA_SINDICAL_ART47_414/05")
    assert aporte.importe.monto == D("20000.00")
    assert diferencia.importe.monto == D("10000.00")
