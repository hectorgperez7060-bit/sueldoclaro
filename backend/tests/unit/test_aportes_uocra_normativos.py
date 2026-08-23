from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SQL = (ROOT / "migrations/021_aportes_uocra_2026.sql").read_text(encoding="utf-8")


def test_migracion_separa_aporte_trabajador_y_contribucion_empleador():
    assert "APORTE_SOLIDARIO_UOCRA_76/75" in SQL
    assert "CONTRIB_EMP_UOCRA_76/75" in SQL
    assert "'ded_noafil'" in SQL
    assert "'contrib_emp'" in SQL
    assert '"no_retener_trabajador":true' in SQL


def test_contribucion_empresaria_exige_mes_anterior_y_todo_el_plantel():
    assert '"base_contribucion":"remunerativa_mes_anterior"' in SQL
    assert '"requiere_base_mes_anterior":true' in SQL
    assert '"universo":"todo_el_plantel"' in SQL


def test_estados_documentales_no_exageran_la_fuente_disponible():
    assert "PUBLICADA_POR_PARTE_SIGNATARIA" in SQL
    assert "HOMOLOGADA_NO_PUBLICADA_BORA" in SQL
    assert "VERIFICADA_OFICIAL" not in SQL


def test_vigencia_desde_junio_es_abierta_e_idempotente():
    assert SQL.count("DATE '2026-06-01'") == 2
    assert "valid_to=NULL" in SQL
    assert "IF NOT FOUND THEN" in SQL
    assert "ON CONFLICT (cct_numero,codigo,version) DO UPDATE" in SQL
