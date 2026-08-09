"""Rutas de empleados (ABM + import xlsx). Todas requieren tenant activo."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response

from api.dependencies.auth import Principal, require_rol, require_tenant
from application.dto.schemas import EmpleadoIn, EmpleadoOut, ImportResultado
from application.use_cases.importar_empleados import ImportarEmpleados
from domain.value_objects.cuil import es_cuil_valido
from infrastructure.database.repositories import AuditRepo, EmpleadoRepo
from infrastructure.database.session import tenant_session
from infrastructure.excel.importer import generar_plantilla

router = APIRouter(prefix="/empleados", tags=["empleados"])


def _to_out(e) -> EmpleadoOut:
    return EmpleadoOut(
        id=str(e.id), nombre=e.nombre, apellido=e.apellido, cuil=e.cuil,
        fecha_ingreso=e.fecha_ingreso, cct_numero=e.cct_numero, categoria=e.categoria,
        legajo=e.legajo, afiliado_sindicato=e.afiliado_sindicato,
        fecha_nacimiento=e.fecha_nacimiento, sexo=e.sexo, estado_civil=e.estado_civil,
        domicilio=e.domicilio, cantidad_hijos=e.cantidad_hijos or 0,
        conyuge_a_cargo=e.conyuge_a_cargo or False, obra_social=e.obra_social,
        modalidad_contrato=e.modalidad_contrato, cbu=e.cbu, forma_pago=e.forma_pago,
        lugar_trabajo=e.lugar_trabajo, localidad=e.localidad,
        filial_sindical=e.filial_sindical,
    )


@router.get("/plantilla")
async def descargar_plantilla(_: Principal = Depends(require_tenant)):
    data = generar_plantilla()
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_empleados.xlsx"},
    )


@router.post("", response_model=EmpleadoOut, status_code=201)
async def crear(body: EmpleadoIn, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    if not es_cuil_valido(body.cuil):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "CUIL inválido")
    tid = uuid.UUID(principal.tenant_id)
    async with tenant_session(principal.tenant_id) as s:
        datos = body.model_dump()
        datos["cuil"] = body.cuil.replace("-", "")
        emp = await EmpleadoRepo(s).crear(tid, datos)
        await AuditRepo(s).registrar(accion="crear", entidad="empleado", entidad_id=str(emp.id),
                                     tenant_id=tid, usuario_id=uuid.UUID(principal.usuario_id))
        return _to_out(emp)


@router.get("", response_model=list[EmpleadoOut])
async def listar(principal: Principal = Depends(require_tenant)):
    async with tenant_session(principal.tenant_id) as s:
        return [_to_out(e) for e in await EmpleadoRepo(s).listar()]


@router.get("/{empleado_id}", response_model=EmpleadoOut)
async def obtener(empleado_id: str, principal: Principal = Depends(require_tenant)):
    async with tenant_session(principal.tenant_id) as s:
        emp = await EmpleadoRepo(s).obtener(uuid.UUID(empleado_id))
        if emp is None:  # RLS: si es de otro tenant, no existe para este
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Empleado no encontrado")
        return _to_out(emp)


@router.delete("/{empleado_id}", status_code=204)
async def eliminar(empleado_id: str, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    async with tenant_session(principal.tenant_id) as s:
        emp = await EmpleadoRepo(s).obtener(uuid.UUID(empleado_id))
        if emp is None:  # RLS: si es de otro tenant, no existe para este
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Empleado no encontrado")
        await s.delete(emp)
        await AuditRepo(s).registrar(accion="eliminar", entidad="empleado", entidad_id=empleado_id,
                                     tenant_id=uuid.UUID(principal.tenant_id),
                                     usuario_id=uuid.UUID(principal.usuario_id))
    return None


@router.post("/import", response_model=ImportResultado)
async def importar(archivo: UploadFile, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    contenido = await archivo.read()
    res = await ImportarEmpleados().ejecutar(principal.tenant_id, contenido, principal.usuario_id)
    return ImportResultado(**res)
