"""SQL de Row-Level Security. Compartido por la migración Alembic y el bootstrap
de los tests de integración, para que ambos apliquen exactamente la misma política.

Política por tabla de negocio: una fila es visible/escribible solo si su
``tenant_id`` coincide con ``app.current_tenant`` (seteado por request desde el
JWT). ``NULLIF(..., '')`` evita el error de cast cuando el GUC no está seteado:
en ese caso la comparación da NULL => 0 filas (fail-closed).
"""
from __future__ import annotations

from typing import List

from .models import TABLAS_CON_RLS

_PRED = "tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid"


def enable_rls_sql() -> List[str]:
    stmts: List[str] = []
    for t in TABLAS_CON_RLS:
        stmts.append(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;")
        stmts.append(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY;")
        stmts.append(
            f"CREATE POLICY {t}_tenant_isolation ON {t} "
            f"USING ({_PRED}) WITH CHECK ({_PRED});"
        )
    return stmts


def disable_rls_sql() -> List[str]:
    stmts: List[str] = []
    for t in TABLAS_CON_RLS:
        stmts.append(f"DROP POLICY IF EXISTS {t}_tenant_isolation ON {t};")
        stmts.append(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY;")
        stmts.append(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY;")
    return stmts


def append_only_sql(role: str = "sueldoclaro") -> List[str]:
    """audit_log append-only: revoca UPDATE/DELETE al rol de la app si existe.
    (Best-effort: no aplica si el rol es superusuario.)"""
    return [
        f"""DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{role}') THEN
    REVOKE UPDATE, DELETE ON audit_log FROM {role};
  END IF;
END $$;"""
    ]
