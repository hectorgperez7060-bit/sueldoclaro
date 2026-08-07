"""init: tablas + Row-Level Security

Revision ID: 0001_init
Revises:
Create Date: 2026-07-29
"""
from alembic import op

from infrastructure.database.base import Base
import infrastructure.database.models  # noqa: F401 (registra tablas en el metadata)
from infrastructure.database.rls import append_only_sql, disable_rls_sql, enable_rls_sql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Crea todas las tablas definidas en los modelos.
    Base.metadata.create_all(bind=bind)
    # Activa RLS y políticas de aislamiento por tenant.
    for stmt in enable_rls_sql():
        op.execute(stmt)
    # audit_log append-only (best-effort).
    for stmt in append_only_sql():
        op.execute(stmt)


def downgrade() -> None:
    bind = op.get_bind()
    for stmt in disable_rls_sql():
        op.execute(stmt)
    Base.metadata.drop_all(bind=bind)
