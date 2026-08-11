"""Caso de uso: importar empleados desde xlsx (con reporte por fila)."""
from __future__ import annotations

import uuid

from infrastructure.database.repositories import AuditRepo, EmpleadoRepo
from infrastructure.database.session import tenant_session
from infrastructure.excel.importer import parsear


class ImportarEmpleados:
    async def ejecutar(self, tenant_id: str, contenido: bytes, usuario_id: str) -> dict:
        validos, errores = parsear(contenido)
        importados = 0
        async with tenant_session(tenant_id) as s:
            repo = EmpleadoRepo(s)
            for datos in validos:
                await repo.crear(uuid.UUID(tenant_id), datos)
                importados += 1
            await AuditRepo(s).registrar(
                accion="import_empleados", entidad="empleado",
                tenant_id=uuid.UUID(tenant_id), usuario_id=uuid.UUID(usuario_id),
                payload_diff={"importados": importados, "con_error": len(errores)},
            )
        return {
            "importados": importados,
            "total_filas": importados + len(errores),
            "errores": errores,
        }
