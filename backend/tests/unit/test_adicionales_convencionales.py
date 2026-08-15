from datetime import date
from decimal import Decimal as D

import pytest

from domain.entities.empleado import Empleado
from domain.entities.farmacia_414_05 import configurar_adicionales_farmacia
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion, Novedades
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


def _motor():
    desde = date(2026, 1, 1)
    parametros = ParametroSet([
        ParametroLegal("APORTE_JUBILACION", D("0.11"), "%", "empleado", desde),
        ParametroLegal("APORTE_LEY19032", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", desde),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", desde),
        ParametroLegal("CONTRIB_JUBILACION", D("0.18"), "%", "empleador", desde),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", desde),
    ])
    return MotorLiquidacion(parametros, AmparoSet())


def _caso():
    reglas, referencias = configurar_adicionales_farmacia(
        D("1000000"), D("1100000"), D("1500000")
    )
    config = CctConfig(
        "414/05", D("0"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
        antiguedad_escalones=((1, D("0.05")), (5, D("0.20"))),
        adicionales=reglas, bases_referencia=referencias,
    )
    empleado = Empleado(
        "Ana", "Farmacia", Cuil("27307324666"), date(2020, 1, 1),
        "414/05", "Empleado Especializado de Farmacia", "1",
    )
    escala = EscalaSalarial(
        "414/05", empleado.categoria, Dinero(D("1800000")),
        date(2026, 7, 1), date(2026, 7, 31), True, "escala de prueba",
    )
    return empleado, escala, config


def test_adicional_categoria_mas_antiguedad_entra_en_recibo_y_aportes():
    empleado, escala, config = _caso()
    resultado = _motor().liquidar_mensual(
        empleado, Periodo(2026, 7), escala, config,
        Novedades(adicionales_convencionales=("TITULO_SECUNDARIO",)),
        a_fecha=date(2026, 7, 28),
    )
    adicional = next(c for c in resultado.conceptos if c.codigo == "TITULO_SECUNDARIO")
    # básico 1.800.000 + antigüedad 20% = 2.160.000; adicional 5%.
    assert adicional.importe.monto == D("108000.00")
    assert resultado.total_remunerativo.monto == D("2268000.00")


def test_direccion_tecnica_usa_basico_inicial_a_de_la_escala_del_periodo():
    empleado, escala, config = _caso()
    resultado = _motor().liquidar_mensual(
        empleado, Periodo(2026, 7), escala, config,
        Novedades(adicionales_convencionales=("DIRECCION_TECNICA",)),
        a_fecha=date(2026, 7, 28),
    )
    adicional = next(c for c in resultado.conceptos if c.codigo == "DIRECCION_TECNICA")
    assert adicional.importe.monto == D("880000.00")


def test_idioma_exige_cantidad_y_multiplica_por_cada_idioma():
    empleado, escala, config = _caso()
    with pytest.raises(ValueError, match="requiere una cantidad"):
        _motor().liquidar_mensual(
            empleado, Periodo(2026, 7), escala, config,
            Novedades(adicionales_convencionales=("IDIOMA",)),
            a_fecha=date(2026, 7, 28),
        )
    resultado = _motor().liquidar_mensual(
        empleado, Periodo(2026, 7), escala, config,
        Novedades(
            adicionales_convencionales=("IDIOMA",),
            cantidades_adicionales=(("IDIOMA", D("2")),),
        ),
        a_fecha=date(2026, 7, 28),
    )
    adicional = next(c for c in resultado.conceptos if c.codigo == "IDIOMA")
    assert adicional.importe.monto == D("432000.00")
    assert adicional.cantidad == D("2")


def test_rechaza_adicional_que_no_pertenece_al_convenio():
    empleado, escala, config = _caso()
    with pytest.raises(ValueError, match="no configurados"):
        _motor().liquidar_mensual(
            empleado, Periodo(2026, 7), escala, config,
            Novedades(adicionales_convencionales=("BONO_INVENTADO",)),
            a_fecha=date(2026, 7, 28),
        )
