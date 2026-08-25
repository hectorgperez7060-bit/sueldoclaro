from pathlib import Path
import re
from decimal import Decimal, ROUND_HALF_UP


ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/028_paquete_camioneros_40_89_agosto_2026.sql").read_text(encoding="utf-8")


def test_carga_43_categorias_oficiales_y_no_el_recorte_de_siete():
    bloque = SQL.split("WITH datos(codigo,nombre,orden) AS (VALUES", 1)[1].split(")\nINSERT INTO", 1)[0]
    assert bloque.count("('" ) == 43
    assert "Conductor de Primera Categoría" in bloque
    assert "Auxiliar Operativo de Segunda de Clearing y Correo Privado" in bloque


def test_genera_129_escalas_para_tres_coeficientes():
    bloque = SQL.split("WITH base(categoria,basico) AS (VALUES", 1)[1].split("), zonas", 1)[0]
    assert bloque.count("('" ) == 43
    assert "('BASE',1.00),('COEF_1_20',1.20),('COEF_1_40',1.40)" in SQL
    assert '"escalas":129' in SQL


def test_valores_extremos_y_muestras_coinciden_con_planilla_8_26():
    for literal in (
        "('Conductor de Primera Categoría',1047830.65)",
        "('Conductores de grúas de más de 300 toneladas',1909931.01)",
        "('Ayudantes Mayores de 18 Años',938655.67)",
        "('Auxiliar Operativo de Primera',1439898.83)",
        "('Maestranza y/o Serenos',947834.73)",
    ):
        assert literal in SQL


def test_coeficientes_reproducen_totales_impresos_de_control():
    dos = Decimal("0.01")
    casos = (
        ("1047830.65", "1257396.78", "1466962.91"),
        ("1909931.01", "2291917.21", "2673903.41"),
        ("938655.67", "1126386.80", "1314117.94"),
        ("947834.73", "1137401.68", "1326968.62"),
    )
    for base, sur20, sur40 in casos:
        valor = Decimal(base)
        assert (valor * Decimal("1.20")).quantize(dos, ROUND_HALF_UP) == Decimal(sur20)
        assert (valor * Decimal("1.40")).quantize(dos, ROUND_HALF_UP) == Decimal(sur40)


def test_no_habilita_motor_incompleto_y_registra_motivo():
    assert "true,false,false,1" in SQL  # verificada, no provisoria, motor apagado
    assert "'BLOQUEADO'" in SQL
    assert "cartilla ampliatoria y motor por rama" in SQL


def test_reglas_exigen_novedades_y_rama_sin_inventar_importes():
    for codigo in (
        "MODALIDAD_MENSUAL_DIARIA", "COEFICIENTES_TERRITORIALES", "ANTIGUEDAD",
        "VIATICOS_Y_KILOMETRAJE", "RAMAS_ESPECIALES",
    ):
        assert f"'40/89','{codigo}'" in SQL
    assert '"bloquear_si_aplica_y_falta_detalle":true' in SQL
    assert '"bloquear_rama_sin_regla_modelada":true' in SQL


def test_migracion_es_transaccional_y_reemplaza_solo_agosto():
    assert SQL.startswith("-- Paquete Camioneros")
    assert "BEGIN;" in SQL and SQL.rstrip().endswith("COMMIT;")
    patron = r"DELETE FROM public\.escala_salarial\s+WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01'"
    assert re.search(patron, SQL)


def test_alta_cct_completa_columnas_obligatorias_sin_inventar_cuota():
    assert "cuota_sindical_pct,antiguedad_pct_por_anio" in SQL
    assert "(gen_random_uuid(),'40/89','Camioneros','FedCam',0,0.01,12,200,false,false,true)" in SQL
    assert "aplica_presentismo=false,aplica_cuota_sindical=false" in SQL
