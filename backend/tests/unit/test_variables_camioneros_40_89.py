from decimal import Decimal
from pathlib import Path

import pytest

from domain.payroll_engine.camioneros import (
    NovedadesVariablesCamioneros, ValoresVariablesCamioneros,
    armar_recibo_camioneros_general, calcular_variables_camioneros,
    tramo_transporte_pesado,
)
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from domain.entities.parametros import ParametroLegal, ParametroSet
from datetime import date


ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/029_variables_y_ramas_camioneros_40_89.sql").read_text(encoding="utf-8")


def valores():
    return ValoresVariablesCamioneros(
        Dinero.de("16033.49"), Dinero.de("8045.57"), Dinero.de("18674.56"),
        Decimal("83.82825"), Decimal("83.82825"), Dinero.de("56584.48"),
        Dinero.de("29659.77"), Dinero.de("68014.08"), Dinero.de("35629.54"),
        Dinero.de("38967.57"), Dinero.de("44433.39"), Dinero.de("24476.52"),
        Dinero.de("677108.16"),
    )


def test_valores_fijos_coinciden_con_hoja_2():
    for valor in ("16033.49", "8045.57", "18674.56", "83.82825", "56584.48",
                  "29659.77", "68014.08", "35629.54", "38967.57", "44433.39",
                  "329895.37", "24476.52", "677108.16"):
        assert valor in SQL
    assert SQL.count("('CAM_") == 14


def test_calcula_fijos_y_coeficiente_territorial():
    r = calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros(
        zona="COEF_1_20", dias_comida=2, dias_viatico_especial=1, pernoctadas=1,
    ))
    por_codigo = {x.codigo: x for x in r}
    assert por_codigo["COMIDA_4_1_12"].importe.monto == Decimal("38480.38")
    assert por_codigo["VIATICO_ESPECIAL_4_1_13"].importe.monto == Decimal("9654.68")
    assert por_codigo["PERNOCTADA_4_1_14"].importe.monto == Decimal("22409.47")


def test_viatico_respeta_minimo_350_km_por_dia():
    r = calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros(
        dias_en_viaje=2, kilometros_viatico=100,
    ))
    item = next(x for x in r if x.codigo == "VIATICO_KM_4_2_4")
    assert item.cantidad == Decimal("700")
    assert item.importe.monto == Decimal("58679.78")


def test_garantia_cordillerana_700_km_por_viaje():
    r = calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros(
        viajes_cordilleranos=2, kilometros_viatico=900,
    ))
    assert next(x for x in r if x.codigo == "VIATICO_KM_4_2_4").cantidad == 1400


def test_no_inventa_conceptos_sin_novedad():
    assert calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros()) == ()


def test_bloquea_zona_y_cantidades_invalidas():
    with pytest.raises(ValueError, match="zona Camioneros"):
        calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros(zona="SUR"))
    with pytest.raises(ValueError, match="no pueden ser negativas"):
        calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros(dias_comida=-1))


def test_registra_16_reglas_de_rama_sin_habilitar_recibo():
    bloque = SQL.split("WITH reglas(codigo,descripcion,articulo,configuracion) AS (VALUES", 1)[1].split(")\nINSERT INTO", 1)[0]
    assert bloque.count("('RAMA_") == 16
    assert '"motor":"VISTA_PREVIA"' in SQL
    assert "captura de novedades por rama e integración al recibo" in SQL


def test_parametros_variables_nunca_se_suman_como_haber_automatico():
    p = ParametroLegal(
        "CAM_COMIDA_4_1_12", Decimal("16033.49"), "ARS", "variable",
        date(2026, 8, 1), date(2026, 8, 31), True, "Planilla 8/26", "40/89", {},
    )
    conjunto = ParametroSet([p])
    assert conjunto.conceptos_convenio("40/89") == []
    assert conjunto.variables_convenio("40/89") == [p]
    assert "'ARS','variable'" in SQL


def test_recibo_general_separa_viaticos_de_remuneracion_y_cargas():
    variables = calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros(
        dias_comida=1, kilometros_extra=10,
    ))
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8),
        Dinero.de("1000000"), 2, Decimal("1"), variables,
        Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"),
    )
    comida = recibo.concepto("COMIDA_4_1_12")
    extra = recibo.concepto("HORAS_EXTRA_KM_4_2_3")
    assert comida.tipo.value == "no_remunerativo"
    assert extra.tipo.value == "remunerativo"
    # 1.000.000 + 838,28 de extras; antigüedad 2% sobre ambos.
    assert recibo.concepto("ANTIGUEDAD").importe.monto == Decimal("20016.77")
    assert recibo.concepto("APORTE_JUBILACION").base_calculo.monto == Decimal("1020855.05")


def test_bitrenes_no_se_liquida_hasta_documentar_hecho_generador():
    variables = calcular_variables_camioneros(valores(), NovedadesVariablesCamioneros(
        unidades_bitrenes=1,
    ))
    with pytest.raises(ValueError, match="bitrenes"):
        armar_recibo_camioneros_general(
            "20123456789", Periodo(2026, 8),
            Dinero.de("1000000"), 0, Decimal("1"), variables,
            Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
            Decimal("0.18"), Decimal("0.05"),
        )


def test_larga_distancia_suma_un_jornal_remunerativo_por_traslado():
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1200000"), 0,
        Decimal("1"), (), Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("2"),
    )
    traslado = recibo.concepto("TRASLADO_UNIDAD_DESCARGA_4_2_6")
    assert traslado.importe.monto == Decimal("100000.00")
    assert traslado.tipo.value == "remunerativo"
    assert recibo.concepto("APORTE_JUBILACION").base_calculo.monto == Decimal("1300000.00")


def test_adicional_porcentual_de_rama_integra_antiguedad_y_aportes():
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1000000"), 2,
        Decimal("1"), (), Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("0"),
        (("CAM_RAMA_COMBUSTIBLES_PCT", "Adicional combustibles", Decimal("0.15")),),
    )
    assert recibo.concepto("CAM_RAMA_COMBUSTIBLES_PCT").importe.monto == Decimal("150000.00")
    assert recibo.concepto("ANTIGUEDAD").importe.monto == Decimal("23000.00")
    assert recibo.concepto("APORTE_JUBILACION").base_calculo.monto == Decimal("1173000.00")


def test_residuos_aplica_adicional_remunerativo_y_recargo_nr_sobre_comida():
    variables = calcular_variables_camioneros(
        valores(), NovedadesVariablesCamioneros(dias_comida=2)
    )
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1000000"), 0,
        Decimal("1"), variables, Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("0"),
        (("CAM_RESIDUOS_OPERATIVO_PCT", "Adicional residuos", Decimal("0.15")),),
        Decimal("0.15"),
    )
    assert recibo.concepto("CAM_RESIDUOS_OPERATIVO_PCT").importe.monto == Decimal("150000.00")
    assert recibo.concepto("RECARGO_COMIDA_RESIDUOS_5_3_11").importe.monto == Decimal("4810.05")
    assert recibo.concepto("RECARGO_COMIDA_RESIDUOS_5_3_11").tipo.value == "no_remunerativo"


def test_expreso_recarga_basico_comida_y_viatico_sin_volverlos_remunerativos():
    variables = calcular_variables_camioneros(
        valores(), NovedadesVariablesCamioneros(dias_comida=2, dias_viatico_especial=1)
    )
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1000000"), 0,
        Decimal("1"), variables, Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("0"),
        (("CAM_EXPRESO_PCT", "Adicional expreso", Decimal("0.16")),),
        Decimal("0.16"), Decimal("0.16"), "EXPRESO_5_10", "expreso y mudanzas",
    )
    assert recibo.concepto("CAM_EXPRESO_PCT").importe.monto == Decimal("160000.00")
    assert recibo.concepto("RECARGO_COMIDA_EXPRESO_5_10").importe.monto == Decimal("5130.72")
    assert recibo.concepto("RECARGO_VIATICO_EXPRESO_5_10").importe.monto == Decimal("1287.29")
    assert recibo.concepto("RECARGO_VIATICO_EXPRESO_5_10").tipo.value == "no_remunerativo"


def test_aguas_gaseosas_adicional_integra_antiguedad_y_aportes():
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1000000"), 2,
        Decimal("1"), (), Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("0"),
        (("CAM_AGUAS_GASEOSAS_20_PCT", "Adicional aguas gaseosas", Decimal("0.20")),),
    )
    assert recibo.concepto("CAM_AGUAS_GASEOSAS_20_PCT").importe.monto == Decimal("200000.00")
    assert recibo.concepto("ANTIGUEDAD").importe.monto == Decimal("24000.00")
    assert recibo.concepto("APORTE_JUBILACION").base_calculo.monto == Decimal("1224000.00")


def test_transporte_automoviles_paga_un_jornal_por_viaje():
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1200000"), 0,
        Decimal("1"), (), Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("0"), (), Decimal("0"),
        Decimal("0"), "AUTOS_4_2_9", "transporte de automóviles", Decimal("3"), Decimal("1"),
    )
    concepto = recibo.concepto("TRANSPORTE_AUTOMOVILES_4_2_9")
    assert concepto.importe.monto == Decimal("150000.00")
    assert concepto.tipo.value == "remunerativo"
    assert recibo.concepto("APORTE_JUBILACION").base_calculo.monto == Decimal("1350000.00")


def test_logistica_recarga_basico_comida_y_viatico():
    variables = calcular_variables_camioneros(
        valores(), NovedadesVariablesCamioneros(dias_comida=1, dias_viatico_especial=1)
    )
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1000000"), 0,
        Decimal("1"), variables, Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("0"),
        (("CAM_LOGISTICA_PCT", "Adicional logística", Decimal("0.20")),),
        Decimal("0.20"), Decimal("0.20"), "LOGISTICA_5_12", "operaciones logísticas",
    )
    assert recibo.concepto("CAM_LOGISTICA_PCT").importe.monto == Decimal("200000.00")
    assert recibo.concepto("RECARGO_COMIDA_LOGISTICA_5_12").tipo.value == "no_remunerativo"
    assert recibo.concepto("RECARGO_VIATICO_LOGISTICA_5_12").tipo.value == "no_remunerativo"


def test_asfalto_suma_un_jornal_por_dia_sobre_adicional_combustibles():
    recibo = armar_recibo_camioneros_general(
        "20123456789", Periodo(2026, 8), Dinero.de("1200000"), 0,
        Decimal("1"), (), Decimal("0.11"), Decimal("0.03"), Decimal("0.03"),
        Decimal("0.18"), Decimal("0.05"), Decimal("0"),
        (("CAM_RAMA_COMBUSTIBLES_PCT", "Adicional combustibles", Decimal("0.15")),),
        Decimal("0"), Decimal("0"), "ASFALTO_5_5_2", "asfalto", Decimal("0"),
        Decimal("1"), Decimal("2"), Decimal("1"),
    )
    assert recibo.concepto("CAM_RAMA_COMBUSTIBLES_PCT").importe.monto == Decimal("180000.00")
    assert recibo.concepto("RECARGO_ASFALTO_5_5_2").importe.monto == Decimal("100000.00")
    assert recibo.concepto("APORTE_JUBILACION").base_calculo.monto == Decimal("1480000.00")


@pytest.mark.parametrize(("toneladas", "codigo"), [
    ("1", "CAM_PESADO_HASTA_50_PCT"),
    ("50", "CAM_PESADO_HASTA_50_PCT"),
    ("50.01", "CAM_PESADO_50_100_PCT"),
    ("100", "CAM_PESADO_50_100_PCT"),
    ("100.01", "CAM_PESADO_MAS_100_PCT"),
])
def test_transporte_pesado_selecciona_tramo_por_carga_util(toneladas, codigo):
    assert tramo_transporte_pesado(Decimal(toneladas)) == codigo


def test_transporte_pesado_rechaza_carga_no_positiva():
    with pytest.raises(ValueError, match="mayor que cero"):
        tramo_transporte_pesado(Decimal("0"))
