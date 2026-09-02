import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.parametros import EscalaSalarial
from domain.payroll_engine.uom import (
    armar_recibo_uom, calcular_adicional_uom, calcular_base_uom,
    calcular_compensacion_abril_julio_uom, calcular_complemento_imgr,
    calcular_gratificacion_uom,
)
from domain.value_objects.periodo import Periodo
from domain.entities.novedad import DatosNovedadMensual
from domain.value_objects.dinero import Dinero
from ui_page import HTML


ROOT = Path(__file__).parents[2]
DATA = json.loads((ROOT / "normativa/uom_260_75_2026_2027.json").read_text(encoding="utf-8"))


def escala(valor, unidad):
    return EscalaSalarial("260/75", "Prueba", Dinero(Decimal(valor)), date(2026, 8, 1),
                          date(2026, 8, 31), True, "ADIMRA/UOMRA", False, "", unidad, False)


def test_matriz_uom_tiene_conteos_fuente_y_trazabilidad():
    assert DATA["conteos"] == {"CATEGORIA": 247, "IMGR": 5, "ADICIONAL": 75}
    assert len(DATA["filas"]) == 327
    assert DATA["fuente_sha256"] == "132ff1b0696593efcc136b27145dbc86edf76d4247d63875bde33c6d9bc44f45"
    assert DATA["expediente"] == "RE-2026-79536710-APN-CGDTEYS#MCH"
    assert all("2026-08-01" in fila["valores"] for fila in DATA["filas"])


def test_agosto_tiene_cinco_grupos_y_modalidades_declaradas():
    categorias = [f for f in DATA["filas"] if f["tipo"] == "CATEGORIA"]
    assert len({f["grupo_codigo"] for f in categorias}) == 5
    assert {f["modalidad"] for f in categorias} == {"HORA", "MENSUAL"}
    assert all(Decimal(f["valores"]["2026-08-01"]) > 0 for f in categorias)


def test_motor_uom_distingue_jornalizado_y_mensualizado():
    jornal = calcular_base_uom(escala("4485.97", "HORA"), Decimal("176"))
    mensual = calcular_base_uom(escala("866587.78", "MENSUAL"), proporcion_jornada=Decimal("0.75"))
    assert jornal.basico.monto == Decimal("789530.72")
    assert mensual.basico.monto == Decimal("649940.84")
    with pytest.raises(ValueError, match="requiere horas"):
        calcular_base_uom(escala("4485.97", "HORA"))
    with pytest.raises(ValueError, match="no liquida el básico por horas"):
        calcular_base_uom(escala("866587.78", "MENSUAL"), Decimal("160"))


def test_imgr_es_garantia_y_excluye_el_parametro_de_horas_extra():
    resultado = calcular_complemento_imgr(Dinero(Decimal("1117862")), Dinero(Decimal("900000")))
    assert resultado.complemento.monto == Decimal("217862.00")
    assert calcular_complemento_imgr(Dinero(Decimal("1117862")), Dinero(Decimal("1200000"))).complemento.monto == 0


def test_adicionales_exigen_hecho_segun_modalidad():
    assert calcular_adicional_uom(Dinero(Decimal("71.58")), "POR_HORA", Decimal("3")).importe.monto == Decimal("214.74")
    assert calcular_adicional_uom(Dinero(Decimal("3482.23")), "POR_EVENTO", Decimal("2")).importe.monto == Decimal("6964.46")
    with pytest.raises(ValueError, match="cantidad positiva"):
        calcular_adicional_uom(Dinero(Decimal("71.58")), "POR_HORA")


def test_migracion_carga_agosto_y_bloquea_hasta_homologacion():
    sql = (ROOT / "migrations/031_uom_260_75_completo_agosto_2026.sql").read_text(encoding="utf-8")
    assert sql.count("'260/75'") > 300
    assert "DATE '2026-08-01'" in sql and "DATE '2026-08-31'" in sql
    assert "'HORA',false" in sql and "'MENSUAL',false" in sql
    assert "DELETE FROM public.escala_salarial" in sql
    assert "ADD COLUMN IF NOT EXISTS uom_detalle" in sql
    assert "GRATIFICACION_NR_UOM_2026_08" in sql and "30000" in sql
    assert "COMPENSACION_ABR_JUL_UOM_CUOTA1" in sql and "70000" in sql
    assert "'no_remunerativo'" not in sql
    assert "30000,'ARS','empleado'" in sql
    assert sql.count("8045.65") == 2


def test_acuerdo_oficial_no_remunerativos_y_recibo_uom():
    gratificacion = calcular_gratificacion_uom(Dinero(Decimal("30000")), Decimal("0.5"))
    compensacion = calcular_compensacion_abril_julio_uom(
        Dinero(Decimal("70000")), 61, Decimal("0.5"), True, Dinero(Decimal("1000")),
    )
    assert gratificacion.monto == Decimal("15000.00")
    assert compensacion.monto == Decimal("16500.00")
    base = calcular_base_uom(escala("4485.97", "HORA"), Decimal("176"))
    imgr = calcular_complemento_imgr(Dinero(Decimal("1117862")), Dinero(Decimal("900000")))
    recibo = armar_recibo_uom(
        "20323243315", Periodo(2026, 8), base, gratificacion, compensacion, imgr,
        Decimal("0.11"), Decimal("0.03"), Decimal("0.03"), Decimal("0.18"), Decimal("0.06"),
        Dinero(Decimal("8045.65")), Dinero(Decimal("8045.65")),
    )
    assert recibo.concepto("GRATIFICACION_NR_UOM").importe.monto == Decimal("15000.00")
    assert recibo.concepto("APORTE_OBRA_SOCIAL").base_calculo.monto == Decimal("1038892.72")
    assert recibo.concepto("SEGURO_VIDA_SEPELIO_UOM").importe.monto == Decimal("8045.65")


def test_adicional_uom_integra_remunerativo_y_bases_de_aportes():
    base = calcular_base_uom(escala("5000", "HORA"), Decimal("160"))
    adicional = calcular_adicional_uom(Dinero(Decimal("1000")), "POR_EVENTO", Decimal("2"))
    recibo = armar_recibo_uom(
        "20323243315", Periodo(2026, 8), base, Dinero.cero(), Dinero.cero(),
        calcular_complemento_imgr(Dinero(Decimal("800000")), Dinero(Decimal("800000"))),
        Decimal("0.11"), Decimal("0.03"), Decimal("0.03"), Decimal("0.18"), Decimal("0.06"),
        Dinero.cero(), Dinero.cero(),
        [("UOM_ADIC_PRUEBA", "Adicional de prueba", adicional)],
    )
    assert recibo.concepto("UOM_ADIC_PRUEBA").importe.monto == Decimal("2000.00")
    assert recibo.total_remunerativo.monto == Decimal("802000.00")
    assert recibo.concepto("APORTE_JUBILACION").base_calculo.monto == Decimal("802000.00")


def test_fuentes_oficiales_uom_quedan_identificadas_por_hash():
    fuentes = json.loads((ROOT / "normativa/uom_260_75_fuentes_2026.json").read_text(encoding="utf-8"))
    assert {f["tipo"] for f in fuentes["fuentes"]} == {
        "acta_acuerdo", "planillas_salariales", "seguro_vida_sepelio"
    }
    assert all(len(f["sha256"]) == 64 and f["url"].startswith("https://www.adimra.org.ar/")
               for f in fuentes["fuentes"])


def test_uom_calcula_como_borrador_pendiente_de_contador():
    caso = (ROOT / "src/application/use_cases/liquidar_periodo.py").read_text(encoding="utf-8")
    pdf = (ROOT / "src/infrastructure/pdf/recibo.py").read_text(encoding="utf-8")
    convenios = (ROOT / "src/api/routes/convenios.py").read_text(encoding="utf-8")
    assert 'emp.cct_numero == "260/75"' in caso
    assert '"pendiente_aprobacion_contador": bool(' in caso
    assert "vista_previa_contador or escala_provisoria" in caso
    assert '"APROBACION_PROFESIONAL_PENDIENTE"' in caso
    assert "PENDIENTE DE REVISIÓN Y APROBACIÓN POR CONTADOR PÚBLICO" in pdf
    assert 'cct.numero in {"260/75", "40/89"}' in convenios


def test_habilitacion_uom_exige_matriz_completa_sin_cambiar_importes():
    sql = (ROOT / "migrations/040_habilitar_motor_uom_agosto_2026.sql").read_text(encoding="utf-8")
    assert "categorias_activas <> 247" in sql
    assert "escalas_verificadas <> 247" in sql
    assert "parametros_uom < 84" in sql
    assert "SET habilitada_liquidacion=true" in sql
    assert "SET basico" not in sql and "INSERT INTO" not in sql


def test_novedad_uom_valida_persiste_y_se_edita_desde_interfaz():
    novedad = DatosNovedadMensual(
        periodo="2026-08",
        uom_detalle={"horas_normales": "176", "ingresos_computables_imgr": "900000", "adicionales": {}},
    )
    assert novedad.para_persistir()["uom_detalle"]["horas_normales"] == "176"
    assert 'id="novUom"' in HTML
    assert "emp.cct_numero==='260/75'" in HTML
    assert "uom_detalle:datosUom()" in HTML
    assert "cargarUom(n.uom_detalle||{})" in HTML


@pytest.mark.parametrize("detalle", [
    {"horas_normales": -1},
    {"ingresos_computables_imgr": -1},
    {"adicionales": []},
    {"adicionales": {"CODIGO": 0}},
    {"dias_trabajados_abril_julio": 123},
    {"campo_inventado": 1},
])
def test_novedad_uom_rechaza_entradas_inseguras(detalle):
    with pytest.raises(ValueError):
        DatosNovedadMensual(periodo="2026-08", uom_detalle=detalle)
