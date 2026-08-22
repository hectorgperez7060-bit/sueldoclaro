from datetime import date
from decimal import Decimal
from pathlib import Path

from domain.entities.escala_verificada import (
    MENSAJE_MOTOR_NO_HABILITADO,
    evaluar_escala,
)
from domain.entities.parametros import EscalaSalarial
from domain.entities.zonificacion_salarial import normalizar_provincia
from domain.value_objects.dinero import Dinero


ROOT = Path(__file__).resolve().parents[2]
MIGRACION = ROOT / "migrations" / "019_uocra_escalas_y_fuentes.sql"


def test_migracion_registra_sesenta_escalas_y_preserva_totales_oficiales():
    sql = MIGRACION.read_text(encoding="utf-8")
    bloque = sql.split("WITH datos(", 1)[1].split(")\nINSERT INTO", 1)[0]
    assert bloque.count("(DATE '2026-") == 60
    assert "'Oficial Especializado','B',7420,816,8237,'HORA'" in bloque
    assert "'Oficial','B',6348,702,7049,'HORA'" in bloque
    assert "'Sereno','C_AUSTRAL',980858,980858,1961716,'MENSUAL'" in bloque
    assert "true, false, false, 1" in sql  # verificada, no provisoria, motor bloqueado
    assert "SELECT gen_random_uuid(), '76/75'" in sql


def test_escala_documentada_puede_quedar_bloqueada_para_el_motor():
    escala = EscalaSalarial(
        cct_numero="76/75",
        categoria="Oficial",
        basico=Dinero(Decimal("7049")),
        valid_from=date(2026, 8, 1),
        valid_to=date(2026, 8, 31),
        is_verified=True,
        fuente="Anexo I UOCRA",
        zona="B",
        unidad_escala="HORA",
        habilitada_liquidacion=False,
        estado_fuente="PUBLICADA_POR_PARTE_SIGNATARIA",
    )
    resultado = evaluar_escala(escala)
    assert not resultado.puede_liquidar
    assert resultado.motivo == MENSAJE_MOTOR_NO_HABILITADO


def test_zona_es_historica_y_no_un_mapa_fijo_en_la_regla():
    sql = MIGRACION.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.cct_zona_vigencia" in sql
    assert "('La Pampa','A',DATE '1975-01-01'" in sql
    assert "('La Pampa','B',DATE '2008-02-22'" in sql
    assert "DATE '2008-02-21'" in sql
    assert '"resolucion":"cct_zona_vigencia"' in sql


def test_alias_de_provincia_se_normaliza_sin_asignar_zona():
    assert normalizar_provincia("Ciudad Autónoma de Buenos Aires") == "CABA"
    assert normalizar_provincia("Neuquén") == "NEUQUEN"
    assert normalizar_provincia("Tierra del Fuego, Antártida e Islas del Atlántico Sur") == "TIERRA DEL FUEGO"


def test_tablero_distingue_datos_completos_de_motor_habilitado():
    ruta = ROOT / "src" / "api" / "routes" / "convenios.py"
    codigo = ruta.read_text(encoding="utf-8")
    assert '"escalas_habilitadas"' in codigo
    assert '"motor_habilitado"' in codigo
    assert "and motor_periodo_habilitado" in codigo


def test_estado_normativo_expone_fuente_y_bloqueo_del_motor():
    codigo = (ROOT / "src/api/routes/convenios.py").read_text(encoding="utf-8")
    assert '"estado_fuente": estado_fuente' in codigo
    assert '"habilitado_liquidacion": habilitado' in codigo
    assert "dato documentado, motor de liquidación pendiente" in codigo


def test_migracion_restringe_estados_y_unidades_admitidas():
    sql = MIGRACION.read_text(encoding="utf-8")
    for estado in (
        "VERIFICADA_OFICIAL", "HOMOLOGADA_NO_PUBLICADA_BORA",
        "PUBLICADA_POR_PARTE_SIGNATARIA", "PROVISORIA",
        "PENDIENTE_DOCUMENTACION", "RECHAZADA",
    ):
        assert estado in sql
    assert "CHECK (unidad_escala IN ('HORA','MENSUAL'))" in sql
