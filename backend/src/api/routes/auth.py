"""Rutas de autenticación."""
from __future__ import annotations

import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from api.dependencies.auth import Principal, get_principal
from application.dto.schemas import (
    EmpresaIn, EmpresaOut, Login, ModoCuenta, PerfilCuenta, PerfilLaboralEmpresa,
    RefreshRequest, RegistroEstudio, SeleccionarEmpresa, TokenResponse,
)
from application.use_cases.registrar_estudio import RegistrarEstudio
from domain.entities.perfil_empresa import resolver_regimen_contribucion
from infrastructure.database import models as m
from infrastructure.database.repositories import AuditRepo, TenantRepo, UsuarioRepo
from infrastructure.database.session import plain_session
from infrastructure.security.passwords import verify_password
from infrastructure.security import refresh_store
from infrastructure.security.tokens import decode, emitir_access, emitir_refresh

router = APIRouter(prefix="/auth", tags=["auth"])


async def _emitir_par(usuario_id: str, tenant_id: str | None, rol: str | None) -> TokenResponse:
    access = emitir_access(usuario_id, tenant_id, rol)
    refresh, jti = emitir_refresh(usuario_id, tenant_id, rol)
    await refresh_store.guardar(jti, usuario_id)
    return TokenResponse(access_token=access, refresh_token=refresh,
                         tenant_id=tenant_id, rol=rol)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegistroEstudio):
    try:
        reg = await RegistrarEstudio().ejecutar(
            body.razon_social, body.cuit, body.email, body.password, body.modo_cuenta,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return await _emitir_par(reg.usuario_id, reg.tenant_id, reg.rol)


@router.post("/login", response_model=TokenResponse)
async def login(body: Login):
    async with plain_session() as s:
        repo = UsuarioRepo(s)
        usuario = await repo.por_email(body.email)
        if not usuario or not verify_password(body.password, usuario.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales inválidas")
        membresias = await repo.membresias(usuario.id)
        if not membresias:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "El usuario no pertenece a ninguna empresa")
        elegida = None
        if body.tenant_id:
            elegida = next((m for m in membresias if str(m.tenant_id) == body.tenant_id), None)
            if elegida is None:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "No pertenece a esa empresa")
        else:
            elegida = membresias[0]
        datos = str(usuario.id), str(elegida.tenant_id), elegida.rol
    # Fuera del bloque: emitir el par abre su propia sesion para guardar el jti.
    return await _emitir_par(*datos)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        payload = decode(body.refresh_token)
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh inválido")
    if payload.get("typ") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere un refresh token")
    jti, sub = payload.get("jti"), payload.get("sub")
    # Valida y quema el refresh viejo en un solo paso, y emite uno nuevo.
    if not await refresh_store.consumir(jti, sub):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh revocado o desconocido")
    return await _emitir_par(sub, payload.get("tid"), payload.get("rol"))


@router.get("/perfil", response_model=PerfilCuenta)
async def perfil_cuenta(principal: Principal = Depends(get_principal)):
    """Cómo se usa la cuenta: estudio contable con clientes, o una sola empresa."""
    usuario_id = uuid.UUID(principal.usuario_id)
    async with plain_session() as s:
        usuario = await s.get(m.Usuario, usuario_id)
        if usuario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
        empresas = await TenantRepo(s).listar_del_usuario(usuario_id)
        return PerfilCuenta(
            email=usuario.email,
            modo_cuenta=usuario.modo_cuenta or "ESTUDIO",
            empresas=len(empresas),
        )


@router.put("/perfil/modo", response_model=PerfilCuenta)
async def cambiar_modo_cuenta(
    body: ModoCuenta, principal: Principal = Depends(get_principal),
):
    """Pasar de empresa a estudio contable, o al revés.

    No toca ningún dato: solo cambia qué muestra la aplicación. Una empresa que
    empieza a llevar otras sociedades pasa a estudio sin recargar nada.
    """
    usuario_id = uuid.UUID(principal.usuario_id)
    async with plain_session() as s:
        usuario = await s.get(m.Usuario, usuario_id)
        if usuario is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")
        usuario.modo_cuenta = body.modo_cuenta
        empresas = await TenantRepo(s).listar_del_usuario(usuario_id)
        return PerfilCuenta(
            email=usuario.email, modo_cuenta=usuario.modo_cuenta, empresas=len(empresas),
        )


@router.get("/empresas", response_model=list[EmpresaOut])
async def listar_empresas(principal: Principal = Depends(get_principal)):
    """Empresas a las que pertenece el usuario; nunca expone clientes ajenos."""
    async with plain_session() as s:
        filas = await TenantRepo(s).listar_del_usuario(uuid.UUID(principal.usuario_id))
        return [
            EmpresaOut(
                id=str(empresa.id), razon_social=empresa.razon_social,
                cuit=empresa.cuit, grupo_cliente=empresa.grupo_cliente or "",
                modo_liquidacion=empresa.modo_liquidacion,
                actividad_sector=empresa.actividad_sector,
                condicion_mipyme=empresa.condicion_mipyme,
                certificado_mipyme_vigente_hasta=empresa.certificado_mipyme_vigente_hasta,
                respaldo_regimen_patronal=empresa.respaldo_regimen_patronal or "",
                regimen_contribucion_patronal=empresa.regimen_contribucion_patronal,
                fundamento_regimen_patronal=empresa.fundamento_regimen_patronal or "",
                rol=rol, activa=str(empresa.id) == principal.tenant_id,
            )
            for empresa, rol in filas
        ]


@router.post("/empresas", response_model=TokenResponse, status_code=201)
async def crear_empresa(body: EmpresaIn, principal: Principal = Depends(get_principal)):
    """Crea un cliente separado y devuelve una sesión limitada a ese cliente."""
    cuit = "".join(ch for ch in body.cuit if ch.isdigit())
    if len(cuit) != 11:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "El CUIT debe tener 11 dígitos")
    tenant_id = uuid.uuid4()
    async with plain_session() as s:
        repo = TenantRepo(s)
        existentes = await repo.listar_del_usuario(uuid.UUID(principal.usuario_id))
        if any("".join(ch for ch in empresa.cuit if ch.isdigit()) == cuit for empresa, _ in existentes):
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                "Esa empresa ya está agregada a tu cuenta",
            )
        await repo.crear(
            tenant_id, body.razon_social.strip(), cuit,
            grupo_cliente=body.grupo_cliente.strip(),
        )
        await repo.agregar_miembro(tenant_id, uuid.UUID(principal.usuario_id), "admin")
    return await _emitir_par(principal.usuario_id, str(tenant_id), "admin")


@router.delete("/empresas/{empresa_id}", status_code=200)
async def borrar_empresa(
    empresa_id: str,
    confirmacion_cuit: str = "",
    principal: Principal = Depends(get_principal),
):
    """Borra una empresa y todo lo que se cargo dentro de ella.

    Es irreversible, asi que pide el CUIT escrito a mano como confirmacion y
    exige ser administrador de esa empresa. No se puede borrar la ultima que
    queda: el usuario se quedaria sin ningun lugar donde trabajar.
    """
    try:
        tenant_id = uuid.UUID(empresa_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empresa inválida") from exc

    usuario_id = uuid.UUID(principal.usuario_id)
    async with plain_session() as s:
        repo = UsuarioRepo(s)
        membresia = await repo.membresia(usuario_id, tenant_id)
        if membresia is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No pertenecés a esa empresa")
        if membresia.rol != "admin":
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Solo un administrador de la empresa puede borrarla",
            )
        empresa = await TenantRepo(s).obtener(tenant_id)
        if empresa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa no encontrada")
        razon_social = empresa.razon_social
        cuit_real = "".join(ch for ch in empresa.cuit if ch.isdigit())
        propias = await TenantRepo(s).listar_del_usuario(usuario_id)

    if len(propias) <= 1:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Es la única empresa de tu cuenta. Creá otra antes de borrar esta.",
        )

    if "".join(ch for ch in confirmacion_cuit if ch.isdigit()) != cuit_real:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Para borrar la empresa hay que escribir su CUIT tal cual está cargado",
        )

    # El borrado entero vive en una funcion de la base (migracion 062). La
    # constancia de un cierre y la de una obligacion pagada no se pueden
    # borrar de a una: el rol de la aplicacion no tiene DELETE sobre esas
    # tablas, y esta funcion es la unica manera de sacarlas, completa y en
    # orden, cuando se borra la empresa entera.
    async with plain_session() as s:
        borradas = (await s.execute(
            text("SELECT public.borrar_empresa(:tid)"), {"tid": str(tenant_id)}
        )).scalar_one()
        await AuditRepo(s).registrar(
            accion="borrar", entidad="tenant", entidad_id=str(tenant_id),
            tenant_id=None, usuario_id=usuario_id,
            payload_diff={"razon_social": razon_social, "registros": borradas},
        )

    return {
        "borrada": True,
        "empresa": razon_social,
        "registros_borrados": borradas or {},
    }


@router.put("/empresas/activa/perfil-laboral", response_model=EmpresaOut)
async def actualizar_perfil_laboral(
    body: PerfilLaboralEmpresa,
    principal: Principal = Depends(get_principal),
):
    if principal.rol != "admin":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo un administrador puede cambiar este perfil")
    modos = {"PRUEBA", "PRODUCCION"}
    if body.modo_liquidacion not in modos:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Modo de liquidación inválido")
    try:
        regimen, fundamento = resolver_regimen_contribucion(
            body.actividad_sector, body.condicion_mipyme,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    respaldo = body.respaldo_regimen_patronal.strip()
    if body.condicion_mipyme == "CERTIFICADO_VIGENTE":
        if body.certificado_mipyme_vigente_hasta is None:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                "Informá hasta cuándo está vigente el Certificado MiPyME",
            )

    if body.modo_liquidacion == "PRODUCCION" and (
        regimen == "PENDIENTE" or not respaldo
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Producción requiere situación MiPyME resuelta y respaldo",
        )

    tenant_id = uuid.UUID(principal.tenant_id)
    async with plain_session() as s:
        repo = TenantRepo(s)
        empresa = await repo.obtener(tenant_id)
        if empresa is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa no encontrada")
        empresa = await repo.actualizar_perfil_laboral(
            empresa, body.modo_liquidacion, body.actividad_sector,
            body.condicion_mipyme, body.certificado_mipyme_vigente_hasta,
            respaldo, regimen, fundamento,
        )
        return EmpresaOut(
            id=str(empresa.id), razon_social=empresa.razon_social, cuit=empresa.cuit,
            grupo_cliente=empresa.grupo_cliente or "",
            modo_liquidacion=empresa.modo_liquidacion,
            actividad_sector=empresa.actividad_sector,
            condicion_mipyme=empresa.condicion_mipyme,
            certificado_mipyme_vigente_hasta=empresa.certificado_mipyme_vigente_hasta,
            respaldo_regimen_patronal=empresa.respaldo_regimen_patronal or "",
            regimen_contribucion_patronal=empresa.regimen_contribucion_patronal,
            fundamento_regimen_patronal=empresa.fundamento_regimen_patronal or "",
            rol=principal.rol or "", activa=True,
        )


@router.post("/seleccionar-empresa", response_model=TokenResponse)
async def seleccionar_empresa(
    body: SeleccionarEmpresa,
    principal: Principal = Depends(get_principal),
):
    try:
        tenant_id = uuid.UUID(body.tenant_id)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empresa inválida") from exc
    async with plain_session() as s:
        membresia = await UsuarioRepo(s).membresia(uuid.UUID(principal.usuario_id), tenant_id)
        if membresia is None:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No pertenecés a esa empresa")
    return await _emitir_par(principal.usuario_id, str(tenant_id), membresia.rol)
