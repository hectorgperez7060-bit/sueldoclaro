from datetime import date
from decimal import Decimal

import pytest

from domain.entities.parametros import EscalaSalarial
from domain.payroll_engine.uocra import (
    ComponentesFondoCese,
    HechosQuincenalesUocra,
    TasasAportesUocra,
    armar_recibo_prueba_uocra,
    calcular_aportes_y_contribuciones,
    calcular_base_quincenal,
    calcular_fondo_cese,
    evaluar_feriados_no_trabajados,
)
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo


def escala(unidad="HORA", total="7049", puro="6348"):
    return EscalaSalarial(
        "76/75", "Oficial" if unidad == "HORA" else "Sereno", Dinero.de(total),
        date(2026, 8, 1), date(2026, 8, 31), True, "Anexo I", False, "B",
        unidad, False, "PUBLICADA_POR_PARTE_SIGNATARIA", Dinero.de(puro),
    )


def test_jornal_usa_total_zona_y_asistencia_solo_basico_puro():
    resultado = calcular_base_quincenal(
        escala(), HechosQuincenalesUocra(Decimal("80"), Decimal("88"), True, False)
    )
    assert resultado.primera.basico.monto == Decimal("563920.00")
    assert resultado.segunda.basico.monto == Decimal("620312.00")
    assert resultado.primera.asistencia.monto == Decimal("101568.00")
    assert resultado.segunda.asistencia.monto == Decimal("0")
    assert resultado.remunerativo_total.monto == Decimal("1285800.00")


def test_asistencia_se_evalua_independiente_en_cada_quincena():
    resultado = calcular_base_quincenal(
        escala(), HechosQuincenalesUocra(Decimal("80"), Decimal("80"), False, True)
    )
    assert resultado.primera.asistencia.monto == 0
    assert resultado.segunda.asistencia.monto == Decimal("101568.00")


def test_sereno_mensual_divide_basico_y_presentismo_en_dos_quincenas():
    resultado = calcular_base_quincenal(
        escala("MENSUAL", "1092719", "980858"),
        HechosQuincenalesUocra(None, None, True, True),
    )
    assert resultado.primera.basico.monto == Decimal("546359.50")
    assert resultado.primera.asistencia.monto == Decimal("98085.80")
    assert resultado.remunerativo_total.monto == Decimal("1288890.60")


@pytest.mark.parametrize("hechos,mensaje", [
    (HechosQuincenalesUocra(None, Decimal("80"), True, True), "horas normales"),
    (HechosQuincenalesUocra(Decimal("80"), Decimal("80"), None, True), "asistencia perfecta"),
])
def test_bloquea_si_falta_un_dato_de_alguna_quincena(hechos, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        calcular_base_quincenal(escala(), hechos)


def test_sereno_rechaza_horas_para_no_mezclar_modalidades():
    with pytest.raises(ValueError, match="no debe informar horas"):
        calcular_base_quincenal(
            escala("MENSUAL", "1092719", "980858"),
            HechosQuincenalesUocra(Decimal("80"), Decimal("80"), True, True),
        )


def test_fondo_cese_incluye_remuneracion_y_excluye_sac_recargo_e_indemnizacion():
    resultado = calcular_fondo_cese(
        ComponentesFondoCese(
            basico=Dinero.de("1000000"), asistencia=Dinero.de("200000"),
            adicionales_remunerativos=Dinero.de("50000"),
            horas_extra_valor_normal=Dinero.de("30000"),
            sac=Dinero.de("100000"), recargos_legales_horas_extra=Dinero.de("15000"),
            indemnizaciones=Dinero.de("80000"),
        ),
        Decimal("0.12"),
    )
    assert resultado.base.monto == Decimal("1280000.00")
    assert resultado.importe.monto == Decimal("153600.00")
    assert resultado.sac_excluido.monto == Decimal("100000.00")
    assert resultado.recargos_extra_excluidos.monto == Decimal("15000.00")
    assert resultado.indemnizaciones_excluidas.monto == Decimal("80000.00")


@pytest.mark.parametrize("porcentaje,esperado", [("0.12", "120000.00"), ("0.08", "80000.00")])
def test_fondo_cese_admite_los_dos_tramos_verificados(porcentaje, esperado):
    resultado = calcular_fondo_cese(
        ComponentesFondoCese(basico=Dinero.de("1000000")), Decimal(porcentaje)
    )
    assert resultado.importe.monto == Decimal(esperado)


def test_fondo_cese_rechaza_alicuota_inventada():
    with pytest.raises(ValueError, match="12% u 8%"):
        calcular_fondo_cese(
            ComponentesFondoCese(basico=Dinero.de("1000000")), Decimal("0.10")
        )


def test_feriado_separa_habilitados_y_pendientes_sin_calcular_importe():
    evaluacion = evaluar_feriados_no_trabajados(2, 1, 0)
    assert evaluacion.habilitados_q1 == 1
    assert evaluacion.pendientes_requisito == 1
    assert evaluacion.importe_automatico_habilitado is False


def test_feriado_no_permite_habilitar_mas_que_los_informados():
    with pytest.raises(ValueError, match="no pueden superar"):
        evaluar_feriados_no_trabajados(1, 1, 1)


def tasas():
    return TasasAportesUocra(
        jubilacion=Decimal("0.11"), inssjp=Decimal("0.03"),
        obra_social_trabajador=Decimal("0.03"),
        seguridad_social_empleador=Decimal("0.18"),
        obra_social_empleador=Decimal("0.06"),
        aporte_solidario_no_afiliado=Decimal("0.02"),
        contribucion_empresaria_uocra=Decimal("0.02"),
    )


def test_no_afiliado_paga_solidario_y_empleador_contribuye_sobre_mes_anterior():
    resultado = calcular_aportes_y_contribuciones(
        Dinero.de("1000000"), Dinero.de("1050000"), Dinero.de("900000"),
        tasas(), False,
    )
    assert resultado.jubilacion.monto == Decimal("110000.00")
    assert resultado.obra_social_trabajador.monto == Decimal("31500.00")
    assert resultado.concepto_sindical == "APORTE_SOLIDARIO_UOCRA"
    assert resultado.aporte_sindical_trabajador.monto == Decimal("20000.00")
    assert resultado.contribucion_empresaria_uocra.monto == Decimal("18000.00")
    assert resultado.base_contribucion_uocra_mes_anterior.monto == Decimal("900000.00")


def test_afiliado_no_paga_solidario_y_exige_cuota_verificada():
    with pytest.raises(ValueError, match="cuota sindical UOCRA verificada"):
        calcular_aportes_y_contribuciones(
            Dinero.de("1000000"), Dinero.de("1000000"), Dinero.de("900000"),
            tasas(), True,
        )
    resultado = calcular_aportes_y_contribuciones(
        Dinero.de("1000000"), Dinero.de("1000000"), Dinero.de("900000"),
        tasas(), True, Decimal("0.025"),
    )
    assert resultado.concepto_sindical == "CUOTA_SINDICAL_UOCRA"
    assert resultado.aporte_sindical_trabajador.monto == Decimal("25000.00")


def test_bloquea_si_falta_afiliacion_o_base_del_mes_anterior():
    with pytest.raises(ValueError, match="afiliación"):
        calcular_aportes_y_contribuciones(
            Dinero.de("1"), Dinero.de("1"), Dinero.de("1"), tasas(), None,
        )
    with pytest.raises(ValueError, match="mes anterior"):
        calcular_aportes_y_contribuciones(
            Dinero.de("1"), Dinero.de("1"), None, tasas(), False,
        )


def test_recibo_prueba_cierra_bruto_neto_y_costo_sin_habilitar_produccion():
    base = calcular_base_quincenal(
        escala(), HechosQuincenalesUocra(Decimal("80"), Decimal("88"), True, False)
    )
    fondo = calcular_fondo_cese(
        ComponentesFondoCese(
            basico=base.basico_total, asistencia=base.asistencia_total,
        ), Decimal("0.12"),
    )
    aportes = calcular_aportes_y_contribuciones(
        base.remunerativo_total, base.remunerativo_total, Dinero.de("900000"),
        tasas(), False,
    )
    recibo = armar_recibo_prueba_uocra(
        "20-12345678-6", Periodo(2026, 8), base, fondo, aportes,
    )
    assert recibo.tipo == "mensual_uocra_prueba"
    assert recibo.bruto.monto == Decimal("1285800.00")
    assert recibo.total_deducciones.monto == Decimal("244302.00")
    assert recibo.neto.monto == Decimal("1041498.00")
    assert recibo.total_contribuciones.monto == Decimal("480888.00")
    assert recibo.concepto("CONTRIB_EMPRESARIA_UOCRA").base_calculo.monto == Decimal("900000.00")
