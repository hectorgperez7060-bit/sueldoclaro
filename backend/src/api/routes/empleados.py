"""Rutas de empleados (ABM + import xlsx). Todas requieren tenant activo."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import Response

from api.dependencies.auth import Principal, require_rol, require_tenant
from application.dto.schemas import EmpleadoIn, EmpleadoOut, ImportResultado
from application.use_cases.importar_empleados import ImportarEmpleados
from domain.entities.encuadramiento import resolver_encuadramiento
from domain.value_objects.cuil import es_cuil_valido
from infrastructure.database.repositories import AuditRepo, EmpleadoRepo, EstablecimientoRepo, ParametrosRepo
from infrastructure.database.session import tenant_session
from infrastructure.excel.importer import generar_demo_excel, generar_plantilla

router = APIRouter(prefix="/empleados", tags=["empleados"])


def _to_out(e) -> EmpleadoOut:
    return EmpleadoOut(
        id=str(e.id), nombre=e.nombre, apellido=e.apellido, cuil=e.cuil,
        fecha_ingreso=e.fecha_ingreso, cct_numero=e.cct_numero, categoria=e.categoria,
        legajo=e.legajo, proporcion_jornada=e.proporcion_jornada or 1,
        afiliado_sindicato=e.afiliado_sindicato,
        fecha_nacimiento=e.fecha_nacimiento, sexo=e.sexo, estado_civil=e.estado_civil,
        domicilio=e.domicilio, cantidad_hijos=e.cantidad_hijos or 0,
        conyuge_a_cargo=e.conyuge_a_cargo or False, obra_social=e.obra_social,
        modalidad_contrato=e.modalidad_contrato, cbu=e.cbu, forma_pago=e.forma_pago,
        lugar_trabajo=e.lugar_trabajo, localidad=e.localidad,
        establecimiento_id=str(e.establecimiento_id) if e.establecimiento_id else None,
        filial_sindical=e.filial_sindical, perfil_arca=e.perfil_arca or {},
    )


@router.get("/plantilla")
async def descargar_plantilla(principal: Principal = Depends(require_tenant)):
    async with tenant_session(principal.tenant_id) as s:
        existentes = await EmpleadoRepo(s).listar()
        cuils_existentes = {str(e.cuil).replace("-", "").strip() for e in existentes}
    data = generar_plantilla(cuils_existentes)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_empleados.xlsx"},
    )



@router.get("/demo-excel")
async def obtener_demo_excel(principal: Principal = Depends(require_tenant)):
    async with tenant_session(principal.tenant_id) as s:
        existentes = await EmpleadoRepo(s).listar()
        cuils_existentes = {str(e.cuil).replace("-", "").strip() for e in existentes}
    data = generar_demo_excel(cuils_existentes)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=demo_empleados_prueba.xlsx"},
    )




@router.post("", response_model=EmpleadoOut, status_code=201)
async def crear(body: EmpleadoIn, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    if not es_cuil_valido(body.cuil):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "CUIL inválido")
    tid = uuid.UUID(principal.tenant_id)
    async with tenant_session(principal.tenant_id) as s:
        datos = body.model_dump()
        establecimiento_id = datos.pop("establecimiento_id", None)
        lugar_desde = datos.pop("lugar_trabajo_desde", None) or body.fecha_ingreso
        if lugar_desde < body.fecha_ingreso:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La fecha del lugar no puede ser anterior al ingreso")
        datos["cuil"] = body.cuil.replace("-", "")
        try:
            datos["cct_numero"], datos["categoria"] = resolver_encuadramiento(
                body.cct_numero, body.categoria,
                await ParametrosRepo(s).catalogo_encuadramientos(),
            )
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        establecimiento = None
        if establecimiento_id:
            try:
                establecimiento = await EstablecimientoRepo(s).obtener(tid, uuid.UUID(establecimiento_id))
            except ValueError:
                establecimiento = None
            if establecimiento is None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El establecimiento no pertenece a esta empresa")
            if not establecimiento.activo:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El establecimiento está inactivo")
            datos["lugar_trabajo"] = None
        repo = EmpleadoRepo(s)
        emp = await repo.crear(tid, datos)
        if establecimiento:
            await repo.asignar_establecimiento(tid, emp, establecimiento, lugar_desde)
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


@router.put("/{empleado_id}", response_model=EmpleadoOut)
async def actualizar(empleado_id: str, body: EmpleadoIn, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    if not es_cuil_valido(body.cuil):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "CUIL inválido")
    async with tenant_session(principal.tenant_id) as s:
        emp = await EmpleadoRepo(s).obtener(uuid.UUID(empleado_id))
        if emp is None:  # RLS: si es de otro tenant, no existe para este
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Empleado no encontrado")
        establecimiento_actual_id = emp.establecimiento_id
        datos = body.model_dump()
        establecimiento_id = datos.pop("establecimiento_id", None)
        lugar_desde = datos.pop("lugar_trabajo_desde", None) or body.fecha_ingreso
        if lugar_desde < body.fecha_ingreso:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "La fecha del cambio no puede ser anterior al ingreso")
        datos["cuil"] = body.cuil.replace("-", "")
        try:
            datos["cct_numero"], datos["categoria"] = resolver_encuadramiento(
                body.cct_numero, body.categoria,
                await ParametrosRepo(s).catalogo_encuadramientos(),
            )
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        establecimiento = None
        if establecimiento_id:
            try:
                establecimiento = await EstablecimientoRepo(s).obtener(
                    uuid.UUID(principal.tenant_id), uuid.UUID(establecimiento_id),
                )
            except ValueError:
                establecimiento = None
            if establecimiento is None:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El establecimiento no pertenece a esta empresa")
            if not establecimiento.activo and establecimiento.id != establecimiento_actual_id:
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El establecimiento está inactivo")
            if establecimiento.id != establecimiento_actual_id:
                datos["lugar_trabajo"] = None
            else:
                # Editar otro dato no debe borrar el domicilio estructurado vigente.
                datos.pop("lugar_trabajo", None)
        elif establecimiento_actual_id is None and body.lugar_trabajo is None:
            # Conserva el texto libre de legajos anteriores a establecimientos.
            datos.pop("lugar_trabajo", None)
        for k, v in datos.items():
            setattr(emp, k, v)
        try:
            await EmpleadoRepo(s).asignar_establecimiento(
                uuid.UUID(principal.tenant_id), emp, establecimiento, lugar_desde,
            )
        except ValueError as exc:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        await AuditRepo(s).registrar(accion="actualizar", entidad="empleado", entidad_id=empleado_id,
                                     tenant_id=uuid.UUID(principal.tenant_id),
                                     usuario_id=uuid.UUID(principal.usuario_id))
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


@router.post("/preview-import")
async def vista_previa_importacion(archivo: UploadFile, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    contenido = await archivo.read()
    return await ImportarEmpleados().preview(principal.tenant_id, contenido)


@router.post("/import", response_model=ImportResultado)
async def importar(archivo: UploadFile, principal: Principal = Depends(require_rol("admin", "liquidador"))):
    contenido = await archivo.read()
    res = await ImportarEmpleados().ejecutar(principal.tenant_id, contenido, principal.usuario_id)
    return ImportResultado(**res)
