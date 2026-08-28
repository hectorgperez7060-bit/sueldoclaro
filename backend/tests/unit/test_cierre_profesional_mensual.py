from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.carpeta_mensual import (
    faltantes_para_revision,
    obligaciones_desde_contenido,
    validar_transicion_obligacion,
)


ROOT = Path(__file__).resolve().parents[2]


def contenido_con_boletas():
    return {
        "control_normativo": {"apto_produccion": True, "pendientes": []},
        "obligaciones_sindicales": [
            {"cct_numero": "76/75", "destino_pago": "UOCRA", "codigo_boleta": "CUOTA",
             "importe": "100.25", "canal_pago": "Portal", "url_pago": "https://ejemplo.test"},
            {"cct_numero": "76/75", "destino_pago": "IERIC", "codigo_boleta": "FCL",
             "importe": "250.50", "canal_pago": "Banco"},
        ],
    }


def test_genera_f931_sin_inventar_importe_y_boletas_separadas():
    obligaciones = obligaciones_desde_contenido(contenido_con_boletas())
    assert len(obligaciones) == 3
    assert obligaciones[0]["tipo"] == "ARCA_F931"
    assert obligaciones[0]["importe"] is None
    assert {(o["destino_pago"], o["codigo_boleta"]) for o in obligaciones[1:]} == {
        ("UOCRA", "CUOTA"), ("IERIC", "FCL")
    }
    assert obligaciones[1]["importe"] == Decimal("100.25")


def test_no_firma_hasta_verificar_todas_las_salidas():
    contenido = contenido_con_boletas()
    pendientes = [{"estado": "verificada"}, {"estado": "pagada"}]
    assert "Hay F.931, boletas o pagos sin verificar" in faltantes_para_revision(contenido, pendientes)
    assert faltantes_para_revision(contenido, [{"estado": "verificada"}] * 3) == []


def test_regla_normativa_real_impide_revision_pero_aprobacion_uom_no_es_circular():
    contenido = contenido_con_boletas()
    contenido["control_normativo"]["pendientes"] = [{"codigo": "ESCALA_SIN_FUENTE"}]
    assert faltantes_para_revision(contenido, [{"estado": "verificada"}])
    contenido["control_normativo"]["pendientes"] = [{"codigo": "APROBACION_CONTADOR_UOM"}]
    assert faltantes_para_revision(contenido, [{"estado": "verificada"}]) == []


def test_transicion_de_obligaciones_es_secuencial_y_exige_comprobante():
    validar_transicion_obligacion("pendiente", "generada")
    validar_transicion_obligacion("generada", "pagada", "ticket-123")
    validar_transicion_obligacion("pagada", "verificada", "ticket-123")
    with pytest.raises(ValueError, match="No se puede pasar"):
        validar_transicion_obligacion("pendiente", "pagada", "ticket")
    with pytest.raises(ValueError, match="requiere comprobante"):
        validar_transicion_obligacion("generada", "pagada")


def test_migracion_tiene_rls_y_no_permite_borrado():
    sql = (ROOT / "migrations/032_cierre_profesional_mensual.sql").read_text(encoding="utf-8")
    assert "FORCE ROW LEVEL SECURITY" in sql
    assert "app.current_tenant" in sql
    assert "REVOKE DELETE, TRUNCATE" in sql
    assert "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_role')" in sql
    assert "importe IS NULL" in sql


def test_api_exige_contador_verificado_y_hash_inmutable():
    ruta = (ROOT / "src/api/routes/carpetas.py").read_text(encoding="utf-8")
    assert 'require_rol("admin", "contador_revisor")' in ruta
    assert "matricula_vigente" in ruta and "constancia_url" in ruta
    assert "hash_actual != carpeta.hash_sha256" in ruta
    assert "RevisionProfesional" in ruta
    assert "validar_transicion_obligacion" in ruta
    assert 'carpeta.estado != "calculada"' in ruta


def test_interfaz_expone_cierre_practico_sin_autocertificacion():
    ui = (ROOT / "src/ui_page.py").read_text(encoding="utf-8")
    for token in (
        "Revisar cierre", "Salida / boleta", "Confirmar importe", "Registrar pago",
        "Verificar comprobante", "Aprobar y firmar revisión profesional",
    ):
        assert token in ui
    assert "matricula_vigente=true" not in ui
