"""Rutas de autenticación."""
from __future__ import annotations

import uuid

import jwt
from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies.auth import Principal, get_principal
from application.dto.schemas import (
    EmpresaIn, EmpresaOut, Login, RefreshRequest, RegistroEstudio,
    SeleccionarEmpresa, TokenResponse,
)
from application.use_cases.registrar_estudio import RegistrarEstudio
from infrastructure.database.repositories import TenantRepo, UsuarioRepo
from infrastructure.database.session import plain_session
from infrastructure.security.passwords import verify_password
from infrastructure.security.tokens import (
    decode,
    emitir_access,
    emitir_refresh,
    get_refresh_store,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _emitir_par(usuario_id: str, tenant_id: str | None, rol: str | None) -> TokenResponse:
    access = emitir_access(usuario_id, tenant_id, rol)
    refresh, jti = emitir_refresh(usuario_id, tenant_id, rol)
    get_refresh_store().guardar(jti, usuario_id)
    return TokenResponse(access_token=access, refresh_token=refresh,
                         tenant_id=tenant_id, rol=rol)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegistroEstudio):
    try:
        reg = await RegistrarEstudio().ejecutar(body.razon_social, body.cuit, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e))
    return _emitir_par(reg.usuario_id, reg.tenant_id, reg.rol)


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
        return _emitir_par(str(usuario.id), str(elegida.tenant_id), elegida.rol)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest):
    try:
        payload = decode(body.refresh_token)
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh inválido")
    if payload.get("typ") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Se requiere un refresh token")
    store = get_refresh_store()
    jti, sub = payload.get("jti"), payload.get("sub")
    if not store.es_valido(jti, sub):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh revocado o desconocido")
    # rotación: revoca el viejo, emite uno nuevo
    store.revocar(jti)
    return _emitir_par(sub, payload.get("tid"), payload.get("rol"))


@router.get("/empresas", response_model=list[EmpresaOut])
async def listar_empresas(principal: Principal = Depends(get_principal)):
    """Empresas a las que pertenece el usuario; nunca expone clientes ajenos."""
    async with plain_session() as s:
        filas = await TenantRepo(s).listar_del_usuario(uuid.UUID(principal.usuario_id))
        return [
            EmpresaOut(
                id=str(empresa.id), razon_social=empresa.razon_social,
                cuit=empresa.cuit, rol=rol,
                activa=str(empresa.id) == principal.tenant_id,
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
        await repo.crear(tenant_id, body.razon_social.strip(), cuit)
        await repo.agregar_miembro(tenant_id, uuid.UUID(principal.usuario_id), "admin")
    return _emitir_par(principal.usuario_id, str(tenant_id), "admin")


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
    return _emitir_par(principal.usuario_id, str(tenant_id), membresia.rol)
