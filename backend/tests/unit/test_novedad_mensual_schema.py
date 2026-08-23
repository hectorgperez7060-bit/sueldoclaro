"""Etapa 0: contrato de persistencia y aislamiento de novedades."""
from __future__ import annotations

from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from infrastructure.database.models import NovedadMensual, TABLAS_CON_RLS
from infrastructure.database.rls import enable_rls_sql


def test_novedad_mensual_tiene_columnas_y_claves_esperadas():
    tabla = NovedadMensual.__table__
    esperadas = {
        "id", "tenant_id", "empleado_id", "periodo", "dias_trabajados",
        "faltas_justificadas", "faltas_injustificadas", "horas_extra_50",
        "horas_extra_100", "feriados_trabajados", "feriados_no_trabajados",
        "licencias", "vacaciones", "premios",
        "tipo_premio", "descuentos_adicionales", "observaciones",
        "adicionales_convencionales", "cantidades_adicionales",
        "horas_normales_q1", "horas_normales_q2",
        "asistencia_perfecta_q1", "asistencia_perfecta_q2",
        "feriados_habilitados_q1", "feriados_habilitados_q2",
        "feriados_uocra_detalle", "fcl_criterio_aniversario",
        "fcl_aprobado_por", "fcl_fundamento",
        "created_at", "updated_at",
    }
    assert esperadas == set(tabla.columns.keys())
    assert {fk.target_fullname for fk in tabla.c.empleado_id.foreign_keys} == {"empleado.id"}


def test_unicidad_es_por_tenant_empleado_y_periodo():
    uniques = [c for c in NovedadMensual.__table__.constraints if isinstance(c, UniqueConstraint)]
    assert any(
        [col.name for col in constraint.columns] == ["tenant_id", "empleado_id", "periodo"]
        for constraint in uniques
    )


def test_periodo_y_dias_tienen_controles_en_postgres():
    checks = [c for c in NovedadMensual.__table__.constraints if isinstance(c, CheckConstraint)]
    nombres = {c.name for c in checks}
    assert {
        "ck_novedad_mensual_periodo_yyyy_mm",
        "ck_novedad_mensual_dias_no_negativos",
        "ck_novedad_mensual_dias_segun_periodo",
    } <= nombres
    ddl = str(CreateTable(NovedadMensual.__table__).compile(dialect=postgresql.dialect()))
    assert "TO_DATE(periodo || '-01'" in ddl
    assert "EXTRACT(DAY FROM" in ddl


def test_novedad_mensual_esta_protegida_por_rls():
    assert "novedad_mensual" in TABLAS_CON_RLS
    sql = "\n".join(enable_rls_sql())
    assert "ALTER TABLE novedad_mensual ENABLE ROW LEVEL SECURITY" in sql
    assert "CREATE POLICY novedad_mensual_tenant_isolation" in sql
    assert "WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid)" in sql
