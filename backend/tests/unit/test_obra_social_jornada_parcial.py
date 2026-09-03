"""Obra social en jornada parcial (LCT art. 92 ter), abierta en dos líneas.

El art. 92 ter obliga a aportar y contribuir a la obra social sobre la
remuneración de un trabajador de jornada completa de la misma categoría. En una
media jornada eso significa retener el 3 % de un sueldo que la persona no
cobra: en plata, el 6 % de lo que sí cobra.

Ponerlo en un solo renglón que diga "3 %" deja el recibo matemáticamente
inconsistente contra el bruto que figura arriba: el trabajador multiplica y no
le da. Por eso se exponen dos renglones, cada uno con la base sobre la que se
calculó. Sumados retienen exactamente lo que exige la ley.
"""
from datetime import date
from decimal import Decimal as D

from domain.entities.empleado import Empleado
from domain.entities.parametros import AmparoSet, EscalaSalarial, ParametroLegal, ParametroSet
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import MotorLiquidacion
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo

DESDE = date(2026, 1, 1)
BASICO_COMPLETO = D("1000000")


def _resultado(proporcion: D):
    params = [
        ParametroLegal("APORTE_JUBILACION", D("0"), "%", "empleado", DESDE),
        ParametroLegal("APORTE_LEY19032", D("0"), "%", "empleado", DESDE),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0.03"), "%", "empleado", DESDE),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", DESDE),
        ParametroLegal("CONTRIB_JUBILACION", D("0"), "%", "empleador", DESDE),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0.06"), "%", "empleador", DESDE),
    ]
    emp = Empleado(
        "Claudia", "Gastronómica", Cuil("27307324666"), date(2025, 1, 1),
        "389/04", "Administrativo", "1", afiliado_sindicato=False,
        proporcion_jornada=proporcion,
    )
    escala = EscalaSalarial(
        "389/04", emp.categoria, Dinero(BASICO_COMPLETO), DESDE, is_verified=True,
    )
    config = CctConfig(
        "389/04", D("0"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
    )
    return MotorLiquidacion(ParametroSet(params), AmparoSet()).liquidar_mensual(
        emp, Periodo(2026, 8), escala, config, a_fecha=date(2026, 8, 28),
    )


def _concepto(resultado, codigo):
    return next((c for c in resultado.conceptos if c.codigo == codigo), None)


def test_media_jornada_retiene_el_tres_por_ciento_de_la_jornada_completa():
    """24 sobre 48 horas: el total retenido es el 3 % del sueldo completo."""
    resultado = _resultado(D("0.5"))
    sobre_lo_que_cobra = _concepto(resultado, "APORTE_OBRA_SOCIAL")
    diferencia = _concepto(resultado, "APORTE_OBRA_SOCIAL_ART92TER")

    # El básico prorrateado es el que la persona cobra de verdad.
    assert resultado.bruto.monto == D("500000.00")
    # Primera línea: 3 % de lo que cobra, y su base es ese mismo bruto.
    assert sobre_lo_que_cobra.base_calculo.monto == D("500000.00")
    assert sobre_lo_que_cobra.importe.monto == D("15000.00")
    # Segunda línea: 3 % de lo que falta para llegar a la jornada completa.
    assert diferencia is not None, "falta la línea de la diferencia del art. 92 ter"
    assert diferencia.base_calculo.monto == D("500000.00")
    assert diferencia.importe.monto == D("15000.00")
    # Sumadas: exactamente el 3 % del sueldo de jornada completa.
    total = sobre_lo_que_cobra.importe.monto + diferencia.importe.monto
    assert total == (BASICO_COMPLETO * D("0.03")).quantize(D("0.01"))
    # Y en la práctica es el 6 % de lo que la persona cobra.
    assert total == (resultado.bruto.monto * D("0.06")).quantize(D("0.01"))


def test_cada_linea_cierra_contra_la_base_que_muestra():
    """Lo que hacía inconsistente al recibo: un 3 % que no daba con el bruto."""
    for concepto in _resultado(D("0.5")).conceptos:
        if concepto.base_calculo is None:
            continue
        esperado = (concepto.base_calculo.monto * D("0.03")).quantize(D("0.01"))
        if concepto.codigo.startswith("APORTE_OBRA_SOCIAL"):
            assert concepto.importe.monto == esperado


def test_la_contribucion_patronal_se_abre_igual():
    resultado = _resultado(D("0.5"))
    patronal = _concepto(resultado, "CONTRIB_OBRA_SOCIAL")
    diferencia = _concepto(resultado, "CONTRIB_OBRA_SOCIAL_ART92TER")
    assert patronal.base_calculo.monto == D("500000.00")
    assert patronal.importe.monto == D("30000.00")
    assert diferencia.importe.monto == D("30000.00")
    total = patronal.importe.monto + diferencia.importe.monto
    assert total == (BASICO_COMPLETO * D("0.06")).quantize(D("0.01"))


def test_en_jornada_completa_no_aparece_ninguna_linea_de_diferencia():
    """Sin jornada parcial no hay nada que integrar: el recibo no cambia."""
    resultado = _resultado(D("1"))
    assert _concepto(resultado, "APORTE_OBRA_SOCIAL_ART92TER") is None
    assert _concepto(resultado, "CONTRIB_OBRA_SOCIAL_ART92TER") is None
    assert _concepto(resultado, "APORTE_OBRA_SOCIAL").importe.monto == D("30000.00")


# --------------------------------------------------------------------------- #
# La jornada, escrita como para que la lea quien firma el recibo.
# --------------------------------------------------------------------------- #
def _descripcion_del_basico(proporcion: D, horas: D | None):
    from domain.payroll_engine.config import CctConfig

    params = [
        ParametroLegal("APORTE_JUBILACION", D("0"), "%", "empleado", DESDE),
        ParametroLegal("APORTE_LEY19032", D("0"), "%", "empleado", DESDE),
        ParametroLegal("APORTE_OBRA_SOCIAL", D("0"), "%", "empleado", DESDE),
        ParametroLegal("APORTE_MODERNIZACION", D("0"), "%", "empleado", DESDE),
        ParametroLegal("CONTRIB_JUBILACION", D("0"), "%", "empleador", DESDE),
        ParametroLegal("CONTRIB_OBRA_SOCIAL", D("0"), "%", "empleador", DESDE),
    ]
    emp = Empleado(
        "Claudia", "Gastronómica", Cuil("27307324666"), date(2025, 1, 1),
        "389/04", "Administrativo", "1", afiliado_sindicato=False,
        proporcion_jornada=proporcion,
    )
    escala = EscalaSalarial(
        "389/04", emp.categoria, Dinero(BASICO_COMPLETO), DESDE, is_verified=True,
    )
    config = CctConfig(
        "389/04", D("0"), D("12"), D("200"),
        aplica_presentismo=False, aplica_cuota_sindical=False,
        horas_jornada_completa=horas,
    )
    resultado = MotorLiquidacion(ParametroSet(params), AmparoSet()).liquidar_mensual(
        emp, Periodo(2026, 8), escala, config, a_fecha=date(2026, 8, 28),
    )
    return _concepto(resultado, "BASICO").descripcion


def test_la_jornada_parcial_se_escribe_en_horas_y_no_en_una_fraccion():
    """El recibo lo firma el trabajador: "jornada 0.5000" no le dice nada."""
    assert _descripcion_del_basico(D("0.5"), D("48")) == "Sueldo básico (jornada parcial 24 de 48 h)"
    # Cada convenio tiene su jornada completa: 22 de 44 también es media.
    assert _descripcion_del_basico(D("0.5"), D("44")) == "Sueldo básico (jornada parcial 22 de 44 h)"


def test_sin_las_horas_del_convenio_al_menos_dice_el_porcentaje():
    assert _descripcion_del_basico(D("0.5"), None) == "Sueldo básico (jornada parcial (50%))"


def test_en_jornada_completa_el_basico_no_lleva_aclaracion():
    assert _descripcion_del_basico(D("1"), D("48")) == "Sueldo básico"
