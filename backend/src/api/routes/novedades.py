"""CRUD de novedades mensuales, aislado por empresa mediante JWT + RLS."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies.auth import Principal, require_rol, require_tenant
from application.dto.schemas import (
    NovedadCopiaIn,
    NovedadLoteIn,
    NovedadMensualIn,
    NovedadMensualOut,
    NovedadMensualUpdate,
    ResultadoLoteNovedades,
)
from domain.entities.novedad import DatosNovedadMensual
from infrastructure.database.repositories import (
    AuditRepo,
    EmpleadoRepo,
    NovedadMensualRepo,
)
from infrastructure.database.session import tenant_session

router = APIRouter(prefix="/novedades", tags=["novedades"])


def _uuid(valor: str, nombre: str) -> uuid.UUID:
    try:
        return uuid.UUID(valor)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Identificador de {nombre} inválido",
        ) from exc


def _to_out(novedad, bloqueada: bool = False) -> NovedadMensualOut:
    return NovedadMensualOut(
        id=str(novedad.id),
        empleado_id=str(novedad.empleado_id),
        periodo=novedad.periodo,
        dias_trabajados=novedad.dias_trabajados,
        faltas_justificadas=novedad.faltas_justificadas,
        faltas_injustificadas=novedad.faltas_injustificadas,
        horas_extra_50=novedad.horas_extra_50,
        horas_extra_100=novedad.horas_extra_100,
        feriados_trabajados=novedad.feriados_trabajados,
        feriados_no_trabajados=novedad.feriados_no_trabajados,
        licencias=novedad.licencias,
        vacaciones=novedad.vacaciones,
        premios=novedad.premios,
        tipo_premio=novedad.tipo_premio,
        descuentos_adicionales=novedad.descuentos_adicionales,
        observaciones=novedad.observaciones,
        adicionales_convencionales=novedad.adicionales_convencionales or [],
        cantidades_adicionales=novedad.cantidades_adicionales or {},
        horas_normales_q1=novedad.horas_normales_q1,
        horas_normales_q2=novedad.horas_normales_q2,
        asistencia_perfecta_q1=novedad.asistencia_perfecta_q1,
        asistencia_perfecta_q2=novedad.asistencia_perfecta_q2,
        feriados_habilitados_q1=novedad.feriados_habilitados_q1,
        feriados_habilitados_q2=novedad.feriados_habilitados_q2,
        feriados_uocra_detalle=novedad.feriados_uocra_detalle or [],
        fcl_criterio_aniversario=novedad.fcl_criterio_aniversario,
        fcl_aprobado_por=novedad.fcl_aprobado_por,
        fcl_fundamento=novedad.fcl_fundamento,
        base_contribucion_uocra_mes_anterior=novedad.base_contribucion_uocra_mes_anterior,
        horas_extra_uocra_detalle=novedad.horas_extra_uocra_detalle or [],
        horas_extra_uocra_acumuladas_anio=novedad.horas_extra_uocra_acumuladas_anio or 0,
        horas_hormigon_manual_uocra=novedad.horas_hormigon_manual_uocra or 0,
        horas_altura_uocra=novedad.horas_altura_uocra or 0,
        altura_metros_uocra=novedad.altura_metros_uocra,
        camioneros_detalle=novedad.camioneros_detalle or {},
        uom_detalle=novedad.uom_detalle or {},
        bloqueada=bloqueada,
    )


@router.post("", response_model=NovedadMensualOut, status_code=201)
async def crear(
    body: NovedadMensualIn,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    tid = _uuid(principal.tenant_id, "empresa")
    empleado_id = _uuid(body.empleado_id, "empleado")
    async with tenant_session(principal.tenant_id) as s:
        try:
            novedad = await NovedadMensualRepo(s).crear(
                tid, empleado_id, body.datos_dominio()
            )
        except LookupError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        await AuditRepo(s).registrar(
            accion="crear", entidad="novedad_mensual", entidad_id=str(novedad.id),
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
            payload_diff={"empleado_id": body.empleado_id, "periodo": body.periodo},
        )
        return _to_out(novedad)


# Campos que se copian tal cual de un período a otro. El período NO está en la
# lista: es justamente lo que cambia. Se enumeran a mano en vez de barrer el ORM
# para que agregar una columna nueva no se cuele en la copia sin que nadie lo
# decida.
_CAMPOS_COPIABLES = (
    "dias_trabajados", "faltas_justificadas", "faltas_injustificadas",
    "horas_extra_50", "horas_extra_100", "feriados_trabajados",
    "feriados_no_trabajados", "licencias", "vacaciones", "premios",
    "tipo_premio", "descuentos_adicionales", "observaciones",
    "horas_normales_q1", "horas_normales_q2", "asistencia_perfecta_q1",
    "asistencia_perfecta_q2", "feriados_habilitados_q1", "feriados_habilitados_q2",
    "fcl_criterio_aniversario", "fcl_aprobado_por", "fcl_fundamento",
    "base_contribucion_uocra_mes_anterior", "horas_extra_uocra_acumuladas_anio",
    "horas_hormigon_manual_uocra", "horas_altura_uocra", "altura_metros_uocra",
)
_CAMPOS_TUPLA = (
    "adicionales_convencionales", "feriados_uocra_detalle", "horas_extra_uocra_detalle",
)
_CAMPOS_DICT = ("camioneros_detalle", "uom_detalle")


def _copia_al_periodo(novedad, periodo: str) -> DatosNovedadMensual:
    """Misma novedad, otro período. Los valores no se recalculan ni se ajustan."""
    datos = {"periodo": periodo}
    for campo in _CAMPOS_COPIABLES:
        valor = getattr(novedad, campo, None)
        if valor is not None:
            datos[campo] = valor
    for campo in _CAMPOS_TUPLA:
        datos[campo] = tuple(getattr(novedad, campo, None) or ())
    datos["cantidades_adicionales"] = tuple(
        (getattr(novedad, "cantidades_adicionales", None) or {}).items()
    )
    for campo in _CAMPOS_DICT:
        datos[campo] = dict(getattr(novedad, campo, None) or {})
    return DatosNovedadMensual(**datos)


async def _empleados_destino(s, tid, empleado_ids):
    """Los empleados elegidos, o todo el plantel si no se eligió ninguno."""
    if empleado_ids:
        return [_uuid(valor, "empleado") for valor in empleado_ids]
    return [e.id for e in await EmpleadoRepo(s).listar()]


async def _aplicar(repo, tid, empleado_id, datos, detalle):
    """Crea una novedad y anota el resultado sin cortar el lote."""
    try:
        await repo.crear(tid, empleado_id, datos)
    except (LookupError, ValueError) as exc:
        detalle.append({"empleado_id": str(empleado_id), "estado": "omitido",
                        "motivo": str(exc)})
        return False
    detalle.append({"empleado_id": str(empleado_id), "estado": "creada"})
    return True


@router.post("/lote", response_model=ResultadoLoteNovedades, status_code=201)
async def crear_en_lote(
    body: NovedadLoteIn,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    """Aplica la misma novedad a varios empleados de una sola vez.

    Un empleado que ya tenga novedades del período, o que esté en una liquidación
    confirmada, se omite con su motivo: el lote no pisa nada de lo ya cargado ni
    se cae entero por uno.
    """
    tid = _uuid(principal.tenant_id, "empresa")
    datos = body.datos_dominio()
    detalle: list[dict] = []
    async with tenant_session(principal.tenant_id) as s:
        repo = NovedadMensualRepo(s)
        destinos = await _empleados_destino(s, tid, body.empleado_ids)
        creadas = sum([await _aplicar(repo, tid, eid, datos, detalle) for eid in destinos])
        await AuditRepo(s).registrar(
            accion="crear_lote", entidad="novedad_mensual",
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
            payload_diff={"periodo": body.periodo, "creadas": creadas,
                          "omitidas": len(detalle) - creadas},
        )
    return ResultadoLoteNovedades(
        creadas=creadas, omitidas=len(detalle) - creadas, detalle=detalle
    )


@router.post("/copiar", response_model=ResultadoLoteNovedades, status_code=201)
async def copiar_periodo(
    body: NovedadCopiaIn,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    """Trae al período destino las novedades ya cargadas en otro período.

    Copia los valores tal como quedaron, sin recalcular nada. Si un empleado ya
    tiene novedades en el destino se lo deja como está.
    """
    tid = _uuid(principal.tenant_id, "empresa")
    detalle: list[dict] = []
    async with tenant_session(principal.tenant_id) as s:
        repo = NovedadMensualRepo(s)
        origen = await repo.listar_periodo(tid, body.periodo_origen)
        elegidos = {str(v) for v in (body.empleado_ids or [])}
        creadas = 0
        for novedad in origen:
            if elegidos and str(novedad.empleado_id) not in elegidos:
                continue
            datos = _copia_al_periodo(novedad, body.periodo_destino)
            creadas += await _aplicar(repo, tid, novedad.empleado_id, datos, detalle)
        await AuditRepo(s).registrar(
            accion="copiar_periodo", entidad="novedad_mensual",
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
            payload_diff={"origen": body.periodo_origen, "destino": body.periodo_destino,
                          "creadas": creadas, "omitidas": len(detalle) - creadas},
        )
    return ResultadoLoteNovedades(
        creadas=creadas, omitidas=len(detalle) - creadas, detalle=detalle
    )


@router.get("", response_model=list[NovedadMensualOut])
async def listar(
    periodo: str = Query(..., description="Período AAAA-MM"),
    principal: Principal = Depends(require_tenant),
):
    # Valida período antes de abrir la consulta.
    DatosNovedadMensual(periodo=periodo)
    tid = _uuid(principal.tenant_id, "empresa")
    async with tenant_session(principal.tenant_id) as s:
        repo = NovedadMensualRepo(s)
        novedades = await repo.listar_periodo(tid, periodo)
        return [
            _to_out(
                n,
                await repo.esta_bloqueada(tid, n.empleado_id, n.periodo),
            )
            for n in novedades
        ]


@router.get("/{novedad_id}", response_model=NovedadMensualOut)
async def obtener(
    novedad_id: str,
    principal: Principal = Depends(require_tenant),
):
    tid = _uuid(principal.tenant_id, "empresa")
    async with tenant_session(principal.tenant_id) as s:
        novedad = await NovedadMensualRepo(s).obtener(
            tid, _uuid(novedad_id, "novedad")
        )
        if not novedad:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Novedad no encontrada")
        return _to_out(novedad)


@router.put("/{novedad_id}", response_model=NovedadMensualOut)
async def editar(
    novedad_id: str,
    body: NovedadMensualUpdate,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    tid = _uuid(principal.tenant_id, "empresa")
    nid = _uuid(novedad_id, "novedad")
    async with tenant_session(principal.tenant_id) as s:
        try:
            novedad = await NovedadMensualRepo(s).editar(tid, nid, body.datos_dominio())
        except LookupError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        await AuditRepo(s).registrar(
            accion="actualizar", entidad="novedad_mensual", entidad_id=novedad_id,
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
            payload_diff={"periodo": body.periodo},
        )
        return _to_out(novedad)


@router.delete("/{novedad_id}", status_code=204)
async def eliminar(
    novedad_id: str,
    principal: Principal = Depends(require_rol("admin", "liquidador")),
):
    tid = _uuid(principal.tenant_id, "empresa")
    nid = _uuid(novedad_id, "novedad")
    async with tenant_session(principal.tenant_id) as s:
        try:
            eliminado = await NovedadMensualRepo(s).eliminar(tid, nid)
        except ValueError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
        if not eliminado:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Novedad no encontrada")
        await AuditRepo(s).registrar(
            accion="eliminar", entidad="novedad_mensual", entidad_id=novedad_id,
            tenant_id=tid, usuario_id=_uuid(principal.usuario_id, "usuario"),
        )
    return None
