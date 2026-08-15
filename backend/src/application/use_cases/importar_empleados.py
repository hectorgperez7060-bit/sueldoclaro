"""Caso de uso: importar empleados desde xlsx (con reporte por fila)."""
from __future__ import annotations

import uuid

from domain.entities.encuadramiento import validar_filas_encuadramiento
from infrastructure.database.repositories import AuditRepo, EmpleadoRepo, ParametrosRepo
from infrastructure.database.session import tenant_session
from infrastructure.excel.importer import parsear


class ImportarEmpleados:
    async def preview(self, tenant_id: str, contenido: bytes) -> dict:
        async with tenant_session(tenant_id) as s:
            repo = EmpleadoRepo(s)
            existentes = await repo.listar()
            cuils_existentes = {str(e.cuil).replace("-", "").strip() for e in existentes}
            catalogo = await ParametrosRepo(s).catalogo_encuadramientos()
        validos, errores = parsear(contenido, cuils_existentes)
        validos, errores_encuadramiento = validar_filas_encuadramiento(validos, catalogo)
        errores.extend(errores_encuadramiento)
        # Convert date objects to isoformat string for JSON serialization
        validos_serializables = []
        for v in validos:
            item = dict(v)
            if "fecha_ingreso" in item and item["fecha_ingreso"]:
                item["fecha_ingreso"] = str(item["fecha_ingreso"])
            validos_serializables.append(item)
        return {
            "validos": validos_serializables,
            "errores": errores,
            "total_filas": len(validos) + len(errores),
        }

    async def ejecutar(self, tenant_id: str, contenido: bytes, usuario_id: str) -> dict:
        async with tenant_session(tenant_id) as s:
            repo = EmpleadoRepo(s)
            existentes = await repo.listar()
            cuils_existentes = {str(e.cuil).replace("-", "").strip() for e in existentes}
            validos, errores = parsear(contenido, cuils_existentes)
            validos, errores_encuadramiento = validar_filas_encuadramiento(
                validos, await ParametrosRepo(s).catalogo_encuadramientos()
            )
            errores.extend(errores_encuadramiento)
            importados = 0
            for datos in validos:
                # Quitar 'fila' key antes de pasar a repo.crear
                datos_db = {k: v for k, v in datos.items() if k != "fila"}
                await repo.crear(uuid.UUID(tenant_id), datos_db)
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
