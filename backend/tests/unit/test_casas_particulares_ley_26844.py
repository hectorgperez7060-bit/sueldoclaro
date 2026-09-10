from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.novedad import DatosNovedadMensual
from domain.entities.carpeta_mensual import obligaciones_desde_contenido
from domain.payroll_engine.casas_particulares import (
    ImportesArcaCasas,
    ValoresEscalaCasas,
    anios_antiguedad_computables,
    armar_recibo_casas,
    calcular_base_casas,
    calcular_sac_casas,
    datos_casas_desde_dict,
    dias_vacaciones_casas,
    tramo_horas_arca,
    validar_condicion_trabajador,
)
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from ui_page import HTML


ROOT = Path(__file__).parents[2]


def dinero(valor: str) -> Dinero:
    return Dinero(Decimal(valor))


def test_tramos_arca_respetan_limites_semanales():
    assert tramo_horas_arca(Decimal("11.99")) == "MENOS_12"
    assert tramo_horas_arca(Decimal("12")) == "12_A_15"
    assert tramo_horas_arca(Decimal("15.99")) == "12_A_15"
    assert tramo_horas_arca(Decimal("16")) == "16_O_MAS"
    assert tramo_horas_arca(Decimal("48")) == "16_O_MAS"
    with pytest.raises(ValueError):
        tramo_horas_arca(Decimal("0"))


def test_menos_de_24_horas_se_liquida_por_horas_reales():
    base = calcular_base_casas(
        ValoresEscalaCasas(dinero("480247.85"), dinero("3914.64")),
        Decimal("20"), Decimal("80"), valor_hora_pactado=dinero("4100"),
    )
    assert base.modalidad == "HORA"
    assert base.valor_unitario.monto == Decimal("4100")
    assert base.importe.monto == Decimal("328000.00")
    with pytest.raises(ValueError, match="horas normales"):
        calcular_base_casas(
            ValoresEscalaCasas(dinero("480247.85"), dinero("3914.64")),
            Decimal("20"), None,
        )


def test_desde_24_horas_se_prorratea_el_mensual():
    base = calcular_base_casas(
        ValoresEscalaCasas(dinero("480247.85"), dinero("3914.64")),
        Decimal("30"), None,
    )
    assert base.modalidad == "MENSUAL"
    assert base.importe.monto == Decimal("300154.91")
    completa = calcular_base_casas(
        ValoresEscalaCasas(dinero("480247.85"), dinero("3914.64")),
        Decimal("48"), None,
    )
    assert completa.importe.monto == Decimal("480247.85")


def test_antiguedad_empieza_en_septiembre_2020_sin_retroactividad():
    assert anios_antiguedad_computables(date(2010, 1, 1), date(2026, 8, 31)) == 5
    assert anios_antiguedad_computables(date(2010, 1, 1), date(2026, 9, 1)) == 6
    assert anios_antiguedad_computables(date(2024, 10, 15), date(2026, 9, 28)) == 1


def test_proteccion_especial_para_adolescentes():
    validar_condicion_trabajador(
        "ADOLESCENTE_16_17", date(2009, 4, 1), date(2026, 9, 28),
        Decimal("30"), "Personal para tareas generales · Con retiro",
    )
    with pytest.raises(ValueError, match="36 horas"):
        validar_condicion_trabajador(
            "ADOLESCENTE_16_17", date(2009, 4, 1), date(2026, 9, 28),
            Decimal("40"), "Personal para tareas generales · Con retiro",
        )
    with pytest.raises(ValueError, match="sin retiro"):
        validar_condicion_trabajador(
            "ADOLESCENTE_16_17", date(2009, 4, 1), date(2026, 9, 28),
            Decimal("30"), "Personal para tareas generales · Sin retiro",
        )


def test_recibo_usa_aportes_fijos_y_no_porcentajes_generales():
    base = calcular_base_casas(
        ValoresEscalaCasas(dinero("529261.78"), dinero("4185.94")),
        Decimal("48"), None,
    )
    recibo = armar_recibo_casas(
        "20323243315", Periodo(2026, 9), base,
        date(2010, 1, 1), date(2026, 9, 28), Decimal("0.01"),
        Decimal("2"), Decimal("1"),
        ImportesArcaCasas(dinero("25694.55"), dinero("2128.79"), dinero("15259.36")),
    )
    assert recibo.concepto("ANTIGUEDAD_CASAS").importe.monto == Decimal("31755.71")
    assert recibo.concepto("HORAS_EXTRA_50_CASAS").importe.monto == Decimal("12557.82")
    assert recibo.concepto("APORTE_OBRA_SOCIAL_CASAS").importe.monto == Decimal("25694.55")
    assert recibo.concepto("CONTRIBUCION_JUBILACION_CASAS").importe.monto == Decimal("2128.79")
    assert recibo.concepto("ART_CASAS_PARTICULARES").importe.monto == Decimal("15259.36")


def test_sac_y_vacaciones_del_regimen():
    assert calcular_sac_casas(dinero("600000")).monto == Decimal("300000.00")
    assert calcular_sac_casas(dinero("600000"), Decimal("4")).monto == Decimal("200000.00")
    assert dias_vacaciones_casas(0, 5, 80) == 4
    assert dias_vacaciones_casas(0, 7, 140) == 14
    assert dias_vacaciones_casas(6) == 21
    assert dias_vacaciones_casas(11) == 28
    assert dias_vacaciones_casas(21) == 35


def test_novedad_valida_condicion_y_persiste():
    datos = {"condicion_arca": "activo", "horas_normales_mes": "80"}
    detalle = datos_casas_desde_dict(datos)
    assert detalle.condicion_arca == "ACTIVO"
    novedad = DatosNovedadMensual(periodo="2026-09", casas_particulares_detalle=datos)
    assert novedad.para_persistir()["casas_particulares_detalle"] == {
        "condicion_arca": "ACTIVO", "horas_normales_mes": "80",
    }
    with pytest.raises(ValueError, match="condición ARCA"):
        DatosNovedadMensual(
            periodo="2026-09", casas_particulares_detalle={"condicion_arca": ""}
        )


def test_migracion_contiene_categorias_escalas_zonas_y_arca():
    sql = (ROOT / "migrations/066_casas_particulares_ley_26844.sql").read_text("utf-8")
    assert "Ley 26.844" in sql and "Resolución CNTCP 6/2026" in sql
    assert sql.count("gen_random_uuid(),'LEY 26844'") >= 17
    assert "valor_hora" in sql and "'MIXTA'" in sql
    assert "2026-08-01" in sql and "2026-12-01" in sql
    assert "DESFAVORABLE" in sql and "1.31" in sql
    assert "Partido de Patagones" in sql
    assert "CP_ARCA_" in sql and "F102RT" in sql
    assert "CP_SUMA_NR_16_O_MAS" in sql and "20000" in sql
    assert "repeat('0',64)" not in sql


def test_interfaz_carga_datos_especificos_sin_exponer_importes():
    assert 'id="novCasasParticulares"' in HTML
    assert "emp.cct_numero==='LEY 26844'" in HTML
    assert "casas_particulares_detalle:datosCasasParticulares()" in HTML
    assert "cargarCasasParticulares(n.casas_particulares_detalle||{})" in HTML
    assert "25694.55" not in HTML


def test_carpeta_genera_f102rt_y_no_f931_para_regimen_especial():
    obligaciones = obligaciones_desde_contenido({
        "detalles": [{
            "cct_numero": "LEY 26844",
            "conceptos": [
                {"codigo_boleta": "F102RT", "importe": "25694.55"},
                {"codigo_boleta": "F102RT", "importe": "2128.79"},
                {"codigo_boleta": "F102RT", "importe": "15259.36"},
                {"codigo_boleta": None, "importe": "500000"},
            ],
        }],
        "obligaciones_sindicales": [],
    })
    assert [o["tipo"] for o in obligaciones] == ["ARCA_F102RT"]
    assert obligaciones[0]["importe"] == Decimal("43082.70")


@pytest.mark.parametrize("detalle", [
    {"condicion_arca": "DESCONOCIDA"},
    {"condicion_arca": "ACTIVO", "horas_normales_mes": -1},
    {"condicion_arca": "ACTIVO", "horas_normales_mes": 301},
    {"condicion_arca": "ACTIVO", "campo_inventado": 1},
])
def test_novedad_rechaza_entradas_inseguras(detalle):
    with pytest.raises(ValueError):
        DatosNovedadMensual(periodo="2026-09", casas_particulares_detalle=detalle)
