import pytest
from sqlalchemy import UniqueConstraint

from domain.entities.carpeta_mensual import PerfilContador, huella_carpeta, validar_transicion
from infrastructure.database.models import CarpetaMensual, RevisionProfesional, TABLAS_CON_RLS
from infrastructure.database.rls import enable_rls_sql


def test_huella_es_estable_y_detecta_cambios():
    a = {"periodo": "2026-08", "totales": {"neto": "100", "bruto": "120"}}
    b = {"totales": {"bruto": "120", "neto": "100"}, "periodo": "2026-08"}
    assert huella_carpeta(a) == huella_carpeta(b)
    b["totales"]["neto"] = "101"
    assert huella_carpeta(a) != huella_carpeta(b)


def test_flujo_exige_orden_y_comprobantes_externos():
    validar_transicion("borrador", "calculada")
    validar_transicion("calculada", "revisada")
    with pytest.raises(ValueError):
        validar_transicion("revisada", "aceptada", "acuse")
    with pytest.raises(ValueError, match="comprobante"):
        validar_transicion("revisada", "presentada")
    validar_transicion("revisada", "presentada", "acuse-presentacion")
    validar_transicion("presentada", "aceptada", "acuse-aceptacion")
    validar_transicion("aceptada", "pagada", "comprobante-pago")


def test_contador_solo_revisa_con_matricula_vigente_y_constancia():
    perfil = PerfilContador("Ana Pérez", "27123456780", "T1 F2", "CABA", "CPCECABA", True, "constancia.pdf")
    assert perfil.puede_revisar()
    sin_constancia = PerfilContador("Ana Pérez", "27123456780", "T1 F2", "CABA", "CPCECABA", True, "")
    assert not sin_constancia.puede_revisar()


def test_carpeta_versionada_y_tablas_protegidas_por_rls():
    uniques = [c for c in CarpetaMensual.__table__.constraints if isinstance(c, UniqueConstraint)]
    assert any([x.name for x in c.columns] == ["tenant_id", "periodo", "version"] for c in uniques)
    assert {"carpeta_mensual", "revision_profesional"} <= set(TABLAS_CON_RLS)
    sql = "\n".join(enable_rls_sql())
    assert "CREATE POLICY carpeta_mensual_tenant_isolation" in sql
    assert "CREATE POLICY revision_profesional_tenant_isolation" in sql


def test_revision_guarda_identidad_historica_y_hash():
    columnas = set(RevisionProfesional.__table__.columns.keys())
    assert {"nombre_apellido", "matricula", "jurisdiccion", "consejo_profesional", "hash_revisado", "firmado_at"} <= columnas
