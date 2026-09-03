"""Caso de uso: registrar un estudio contable (crea tenant + usuario admin)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from infrastructure.database.repositories import TenantRepo, UsuarioRepo
from infrastructure.database.session import plain_session
from infrastructure.security.passwords import hash_password


@dataclass(frozen=True)
class EstudioRegistrado:
    usuario_id: str
    tenant_id: str
    rol: str = "admin"
    modo_cuenta: str = "ESTUDIO"


class RegistrarEstudio:
    async def ejecutar(self, razon_social: str, cuit: str, email: str, password: str,
                       modo_cuenta: str = "ESTUDIO") -> EstudioRegistrado:
        async with plain_session() as s:
            usuarios = UsuarioRepo(s)
            if await usuarios.por_email(email):
                raise ValueError("El email ya está registrado")
            usuario = await usuarios.crear(email, hash_password(password), modo_cuenta)
            tenant_id = uuid.uuid4()
            tenants = TenantRepo(s)
            await tenants.crear(tenant_id, razon_social, cuit)
            await tenants.agregar_miembro(tenant_id, usuario.id, "admin")
            return EstudioRegistrado(str(usuario.id), str(tenant_id), "admin", modo_cuenta)
