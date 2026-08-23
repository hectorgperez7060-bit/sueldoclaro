from datetime import date
from decimal import Decimal

import pytest

from domain.entities.parametros import EscalaSalarial
from domain.payroll_engine.uocra import HechosQuincenalesUocra, calcular_base_quincenal
from domain.value_objects.dinero import Dinero


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
