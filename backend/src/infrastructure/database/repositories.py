
"""Repositorios concretos (implementan los puertos del dominio con el ORM)."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.parametros import (
    Amparo as AmparoDom,
    AmparoSet,
    EscalaSalarial as EscalaDom,
    ParametroLegal as ParamDom,
    ParametroSet,
)
from domain.payroll_engine.config import CctConfig
from domain.value_objects.dinero import Dinero

from . import models as m


class UsuarioRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def por_email(self, email: str) -> Optional[m.Usuario]:
        r = await self.s.execute(select(m.Usuario).where(m.Usuario.email == email.lower()))
        return r.scalar_one_or_none()

    async def crear(self, email: str, password_hash: str) -> m.Usuario:
        u = m.Usuario(email=email.lower(), password_hash=password_hash)
        self.s.add(u)
        await self.s.flush()
        return u

    async def membresias(self, usuario_id: uuid.UUID) -> List[m.UsuarioTenant]:
        r = await self.s.execute(
            select(m.UsuarioTenant).where(m.UsuarioTenant.usuario_id == usuario_id)
        )
        return list(r.scalars().all())

    async def membresia(self, usuario_id: uuid.UUID, tenant_id: uuid.UUID) -> Optional[m.UsuarioTenant]:
        r = await self.s.execute(
            select(m.UsuarioTenant).where(
                m.UsuarioTenant.usuario_id == usuario_id,
                m.UsuarioTenant.tenant_id == tenant_id,
            )
        )
        return r.scalar_one_or_none()


class TenantRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def crear(self, tenant_id: uuid.UUID, razon_social: str, cuit: str) -> m.Tenant:
        t = m.Tenant(id=tenant_id, razon_social=razon_social, cuit=cuit)
        self.s.add(t)
        await self.s.flush()
        return t

    async def agregar_miembro(self, tenant_id: uuid.UUID, usuario_id: uuid.UUID, rol: str) -> None:
        self.s.add(m.UsuarioTenant(tenant_id=tenant_id, usuario_id=usuario_id, rol=rol))
        await self.s.flush()


class EmpleadoRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def crear(self, tenant_id: uuid.UUID, datos: dict) -> m.Empleado:
        emp = m.Empleado(tenant_id=tenant_id, **datos)
        self.s.add(emp)
        await self.s.flush()
        return emp

    async def obtener(self, empleado_id: uuid.UUID) -> Optional[m.Empleado]:
        return await self.s.get(m.Empleado, empleado_id)

    async def listar(self) -> List[m.Empleado]:
        r = await self.s.execute(select(m.Empleado).order_by(m.Empleado.apellido))
        return list(r.scalars().all())


class ParametrosRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def parametro_set(self, fecha: date) -> ParametroSet:
        r = await self.s.execute(
            select(m.ParametroLegal).where(
                m.ParametroLegal.valid_from <= fecha,
                (m.ParametroLegal.valid_to.is_(None)) | (m.ParametroLegal.valid_to >= fecha),
            )
        )
        params = [
            ParamDom(p.codigo, Decimal(p.valor), p.unidad, p.ambito, p.valid_from,
                     p.valid_to, p.is_verified, p.fuente, p.cct_numero, p.incidencias or {})
            for p in r.scalars().all()
        ]
        return ParametroSet(params)

    async def escala(self, cct_numero: str, categoria: str, fecha: date) -> Optional[EscalaDom]:
        r = await self.s.execute(
            select(m.EscalaSalarial).where(
                m.EscalaSalarial.cct_numero == cct_numero,
                m.EscalaSalarial.categoria == categoria,
                m.EscalaSalarial.valid_from <= fecha,
                (m.EscalaSalarial.valid_to.is_(None)) | (m.EscalaSalarial.valid_to >= fecha),
            ).order_by(m.EscalaSalarial.valid_from.desc())
        )
        e = r.scalars().first()
        if not e:
            return None
        return EscalaDom(e.cct_numero, e.categoria, Dinero(Decimal(e.basico)),
                         e.valid_from, e.valid_to, e.is_verified, e.fuente)

    async def amparos(self, cct_numero: str) -> AmparoSet:
        r = await self.s.execute(
            select(m.AmparoCct).where(m.AmparoCct.cct_numero == cct_numero)
        )
        amps = [
            AmparoDom(a.cct_numero, a.articulo_suspendido, a.concepto_afectado, a.estado,
                      a.valid_from, a.valid_to, a.juzgado, a.is_verified)
            for a in r.scalars().all()
        ]
        return AmparoSet(amps)

    async def cct_config(self, cct_numero: str) -> Optional[CctConfig]:
        r = await self.s.execute(select(m.Cct).where(m.Cct.numero == cct_numero))
        c = r.scalar_one_or_none()
        if not c:
            return None
        return CctConfig(
            cct_numero=c.numero,
            antiguedad_pct_por_anio=Decimal(c.antiguedad_pct_por_anio),
            presentismo_divisor=Decimal(c.presentismo_divisor),
            divisor_horas=Decimal(c.divisor_horas),
            aplica_presentismo=c.aplica_presentismo,
            aplica_cuota_sindical=c.aplica_cuota_sindical,
            cuota_sindical_pct=Decimal(c.cuota_sindical_pct) if c.cuota_sindical_pct is not None else None,
        )


class LiquidacionRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def crear(self, tenant_id: uuid.UUID, periodo: str, tipo: str,
                    snapshot: dict) -> m.Liquidacion:
        liq = m.Liquidacion(tenant_id=tenant_id, periodo=periodo, tipo=tipo,
                            snapshot_parametros=snapshot)
        self.s.add(liq)
        await self.s.flush()
        return liq

    async def agregar_detalle(self, tenant_id: uuid.UUID, liquidacion_id: uuid.UUID,
                              empleado_id: uuid.UUID, conceptos: list,
                              bruto: Decimal, deducciones: Decimal, neto: Decimal) -> m.LiquidacionDetalle:
        det = m.LiquidacionDetalle(
            tenant_id=tenant_id, liquidacion_id=liquidacion_id, empleado_id=empleado_id,
            conceptos=conceptos, bruto=bruto, total_deducciones=deducciones, neto=neto,
        )
        self.s.add(det)
        await self.s.flush()
        return det

    async def obtener(self, liquidacion_id: uuid.UUID) -> Optional[m.Liquidacion]:
        return await self.s.get(m.Liquidacion, liquidacion_id)


class AuditRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def registrar(self, *, accion: str, entidad: str, entidad_id: Optional[str] = None,
                        tenant_id: Optional[uuid.UUID] = None, usuario_id: Optional[uuid.UUID] = None,
                        payload_diff: Optional[dict] = None, ip: Optional[str] = None,
                        user_agent: Optional[str] = None) -> None:
        self.s.add(m.AuditLog(
            accion=accion, entidad=entidad, entidad_id=entidad_id, tenant_id=tenant_id,
            usuario_id=usuario_id, payload_diff=payload_diff or {}, ip=ip, user_agent=user_agent,
        ))
        await self.s.flush()
