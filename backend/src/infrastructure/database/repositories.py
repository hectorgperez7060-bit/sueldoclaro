"""Repositorios concretos (implementan los puertos del dominio con el ORM).

El filtrado por tenant lo enforcea RLS a nivel de PostgreSQL: la sesión ya trae
``app.current_tenant`` seteado, así que estas consultas no repiten el filtro
(defensa en profundidad: además se podría filtrar en app).
"""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.parametros import (
    Amparo as AmparoDom,
    AmparoSet,
    CuotaArt101 as CuotaArt101Dom,
    EscalaSalarial as EscalaDom,
    ParametroLegal as ParamDom,
    ParametroSet,
    resolver_cuota_art101,
)
from domain.entities.novedad import DatosNovedadMensual
from domain.entities.farmacia_414_05 import (
    CCT_FARMACIA,
    categoria_farmacia_canonica,
    configurar_adicionales_farmacia,
)
from domain.entities.sanidad_122_75 import CCT_SANIDAD, configurar_adicionales_sanidad
from domain.payroll_engine.config import CctConfig
from domain.value_objects.dinero import Dinero

from . import models as m


# --------------------------------------------------------------------------- #
# Auth (tablas scopeadas en la capa de aplicación)
# --------------------------------------------------------------------------- #
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


# --------------------------------------------------------------------------- #
# Empleado (RLS)
# --------------------------------------------------------------------------- #
class EmpleadoRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def crear(self, tenant_id: uuid.UUID, datos: dict) -> m.Empleado:
        emp = m.Empleado(tenant_id=tenant_id, **datos)
        self.s.add(emp)
        await self.s.flush()
        return emp

    async def obtener(self, empleado_id: uuid.UUID) -> Optional[m.Empleado]:
        # RLS garantiza que solo devuelve si pertenece al tenant activo
        return await self.s.get(m.Empleado, empleado_id)

    async def listar(self) -> List[m.Empleado]:
        r = await self.s.execute(select(m.Empleado).order_by(m.Empleado.apellido))
        return list(r.scalars().all())


# --------------------------------------------------------------------------- #
# Novedades mensuales (RLS + defensa explícita por tenant)
# --------------------------------------------------------------------------- #
class NovedadMensualRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def _empleado_del_tenant(
        self, tenant_id: uuid.UUID, empleado_id: uuid.UUID,
    ) -> Optional[m.Empleado]:
        r = await self.s.execute(
            select(m.Empleado).where(
                m.Empleado.id == empleado_id,
                m.Empleado.tenant_id == tenant_id,
            )
        )
        return r.scalar_one_or_none()

    async def _periodo_confirmado(
        self, tenant_id: uuid.UUID, empleado_id: uuid.UUID, periodo: str,
    ) -> bool:
        r = await self.s.execute(
            select(m.Liquidacion.id)
            .join(
                m.LiquidacionDetalle,
                m.LiquidacionDetalle.liquidacion_id == m.Liquidacion.id,
            )
            .where(
                m.Liquidacion.tenant_id == tenant_id,
                m.LiquidacionDetalle.tenant_id == tenant_id,
                m.LiquidacionDetalle.empleado_id == empleado_id,
                m.Liquidacion.periodo == periodo,
                m.Liquidacion.estado == "confirmada",
            )
            .limit(1)
        )
        return r.scalar_one_or_none() is not None

    async def esta_bloqueada(
        self, tenant_id: uuid.UUID, empleado_id: uuid.UUID, periodo: str,
    ) -> bool:
        """Indica si una novedad ya es inmutable por confirmación de la liquidación."""
        return await self._periodo_confirmado(tenant_id, empleado_id, periodo)

    async def crear(
        self, tenant_id: uuid.UUID, empleado_id: uuid.UUID, datos: DatosNovedadMensual,
    ) -> m.NovedadMensual:
        if not await self._empleado_del_tenant(tenant_id, empleado_id):
            raise LookupError("Empleado inexistente para la empresa activa")
        if await self.obtener_por_periodo(tenant_id, empleado_id, datos.periodo):
            raise ValueError("Ya existen novedades para ese empleado y período")
        if await self._periodo_confirmado(tenant_id, empleado_id, datos.periodo):
            raise ValueError("No se pueden cargar novedades en una liquidación confirmada")

        novedad = m.NovedadMensual(
            tenant_id=tenant_id,
            empleado_id=empleado_id,
            **datos.para_persistir(),
        )
        self.s.add(novedad)
        await self.s.flush()
        return novedad

    async def obtener(
        self, tenant_id: uuid.UUID, novedad_id: uuid.UUID,
    ) -> Optional[m.NovedadMensual]:
        r = await self.s.execute(
            select(m.NovedadMensual).where(
                m.NovedadMensual.id == novedad_id,
                m.NovedadMensual.tenant_id == tenant_id,
            )
        )
        return r.scalar_one_or_none()

    async def obtener_por_periodo(
        self, tenant_id: uuid.UUID, empleado_id: uuid.UUID, periodo: str,
    ) -> Optional[m.NovedadMensual]:
        r = await self.s.execute(
            select(m.NovedadMensual).where(
                m.NovedadMensual.tenant_id == tenant_id,
                m.NovedadMensual.empleado_id == empleado_id,
                m.NovedadMensual.periodo == periodo,
            )
        )
        return r.scalar_one_or_none()

    async def listar_periodo(
        self, tenant_id: uuid.UUID, periodo: str,
    ) -> List[m.NovedadMensual]:
        # Valida formato antes de consultar.
        DatosNovedadMensual(periodo=periodo)
        r = await self.s.execute(
            select(m.NovedadMensual)
            .where(
                m.NovedadMensual.tenant_id == tenant_id,
                m.NovedadMensual.periodo == periodo,
            )
            .order_by(m.NovedadMensual.empleado_id)
        )
        return list(r.scalars().all())

    async def editar(
        self, tenant_id: uuid.UUID, novedad_id: uuid.UUID, datos: DatosNovedadMensual,
    ) -> m.NovedadMensual:
        novedad = await self.obtener(tenant_id, novedad_id)
        if not novedad:
            raise LookupError("Novedad inexistente para la empresa activa")
        if datos.periodo != novedad.periodo:
            raise ValueError("El período de una novedad existente no se puede cambiar")
        if await self._periodo_confirmado(tenant_id, novedad.empleado_id, novedad.periodo):
            raise ValueError("No se puede editar una liquidación confirmada")
        for campo, valor in datos.para_persistir().items():
            setattr(novedad, campo, valor)
        await self.s.flush()
        return novedad

    async def eliminar(self, tenant_id: uuid.UUID, novedad_id: uuid.UUID) -> bool:
        novedad = await self.obtener(tenant_id, novedad_id)
        if not novedad:
            return False
        if await self._periodo_confirmado(tenant_id, novedad.empleado_id, novedad.periodo):
            raise ValueError("No se puede eliminar una liquidación confirmada")
        await self.s.delete(novedad)
        await self.s.flush()
        return True


# --------------------------------------------------------------------------- #
# Parámetros legales (globales) -> objetos de dominio para el motor
# --------------------------------------------------------------------------- #
class ParametrosRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def catalogo_encuadramientos(self, fecha: date | None = None) -> dict[str, set[str]]:
        """CCT activos y su padrón histórico de categorías.

        La vigencia monetaria se valida al liquidar. Editar el legajo no debe
        dejar de ser posible porque todavía falte cargar la escala de un mes.
        """
        r = await self.s.execute(select(m.Cct.numero).where(m.Cct.activo.is_(True)))
        catalogo = {numero: set() for numero in r.scalars().all()}
        if not catalogo:
            return catalogo
        r = await self.s.execute(
            select(m.EscalaSalarial.cct_numero, m.EscalaSalarial.categoria)
            .where(
                m.EscalaSalarial.cct_numero.in_(catalogo),
            )
            .distinct()
        )
        for cct_numero, categoria in r.all():
            catalogo[cct_numero].add(categoria)
        from domain.entities.farmacia_414_05 import CATEGORIAS_FARMACIA, CCT_FARMACIA
        catalogo.setdefault(CCT_FARMACIA, set()).update(CATEGORIAS_FARMACIA)
        return catalogo

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

    async def resolver_art101(
        self, cct_numero: str, localidad: Optional[str],
        filial: Optional[str], fecha: date,
    ) -> Optional[CuotaArt101Dom]:
        """Devuelve la cuota Art. 101 OFICIAL vigente que corresponde al afiliado
        (por CCT + filial/localidad), o None si no hay ninguna cargada/verificada.
        La decision de matching vive en la funcion pura ``resolver_cuota_art101``.
        """
        r = await self.s.execute(
            select(m.CuotaSindicalArt101).where(
                m.CuotaSindicalArt101.cct_numero == cct_numero,
                m.CuotaSindicalArt101.is_verified.is_(True),
                m.CuotaSindicalArt101.valid_from <= fecha,
                (m.CuotaSindicalArt101.valid_to.is_(None))
                | (m.CuotaSindicalArt101.valid_to >= fecha),
            )
        )
        candidatas = [
            CuotaArt101Dom(
                cct_numero=c.cct_numero, porcentaje=Decimal(c.porcentaje),
                valid_from=c.valid_from, valid_to=c.valid_to, sindicato=c.sindicato,
                filial=c.filial, localidad=c.localidad, fuente=c.fuente,
                is_verified=c.is_verified,
            )
            for c in r.scalars().all()
        ]
        return resolver_cuota_art101(candidatas, cct_numero, localidad, filial, fecha)

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

    async def cct_config(self, cct_numero: str, fecha: date | None = None) -> Optional[CctConfig]:
        r = await self.s.execute(select(m.Cct).where(m.Cct.numero == cct_numero))
        c = r.scalar_one_or_none()
        if not c:
            return None
        adicionales = ()
        referencias = ()
        escalones = None
        if cct_numero == CCT_FARMACIA:
            escalones = (
                (1, Decimal("0.05")), (2, Decimal("0.10")),
                (5, Decimal("0.20")), (10, Decimal("0.30")),
                (15, Decimal("0.35")), (20, Decimal("0.40")),
                (25, Decimal("0.50")),
            )
            fecha = fecha or date.today()
            escalas = (await self.s.execute(select(m.EscalaSalarial).where(
                m.EscalaSalarial.cct_numero == cct_numero,
                m.EscalaSalarial.valid_from <= fecha,
                (m.EscalaSalarial.valid_to.is_(None))
                | (m.EscalaSalarial.valid_to >= fecha),
            ))).scalars().all()
            por_categoria = {}
            for escala in escalas:
                try:
                    por_categoria[categoria_farmacia_canonica(escala.categoria)] = Decimal(escala.basico)
                except ValueError:
                    continue
            requeridas = {
                "Categoría Inicial A", "Categoría Inicial B", "Farmacéutico",
            }
            if requeridas <= set(por_categoria):
                adicionales, referencias = configurar_adicionales_farmacia(
                    por_categoria["Categoría Inicial A"],
                    por_categoria["Categoría Inicial B"],
                    por_categoria["Farmacéutico"],
                )
        elif cct_numero == CCT_SANIDAD:
            adicionales = configurar_adicionales_sanidad()

        return CctConfig(
            cct_numero=c.numero,
            antiguedad_pct_por_anio=Decimal(c.antiguedad_pct_por_anio),
            presentismo_divisor=Decimal(c.presentismo_divisor),
            divisor_horas=Decimal(c.divisor_horas),
            aplica_presentismo=c.aplica_presentismo,
            aplica_cuota_sindical=c.aplica_cuota_sindical,
            cuota_sindical_pct=Decimal(c.cuota_sindical_pct) if c.cuota_sindical_pct is not None else None,
            antiguedad_escalones=escalones,
            adicionales=adicionales,
            bases_referencia=referencias,
        )


# --------------------------------------------------------------------------- #
# Liquidación (RLS)
# --------------------------------------------------------------------------- #
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

    async def obtener_detalle(
        self, liquidacion_id: uuid.UUID, empleado_id: uuid.UUID
    ) -> Optional[m.LiquidacionDetalle]:
        r = await self.s.execute(
            select(m.LiquidacionDetalle).where(
                m.LiquidacionDetalle.liquidacion_id == liquidacion_id,
                m.LiquidacionDetalle.empleado_id == empleado_id,
            )
        )
        return r.scalar_one_or_none()

    async def ajustar_detalle(
        self, detalle: m.LiquidacionDetalle, conceptos: list,
        bruto: Decimal, deducciones: Decimal, neto: Decimal,
    ) -> m.LiquidacionDetalle:
        detalle.conceptos = conceptos
        detalle.bruto = bruto
        detalle.total_deducciones = deducciones
        detalle.neto = neto
        await self.s.flush()
        return detalle

# --------------------------------------------------------------------------- #
# Carpeta mensual versionada (RLS)
# --------------------------------------------------------------------------- #
class CarpetaMensualRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def siguiente_version(self, tenant_id: uuid.UUID, periodo: str) -> int:
        r = await self.s.execute(
            select(func.max(m.CarpetaMensual.version)).where(
                m.CarpetaMensual.tenant_id == tenant_id,
                m.CarpetaMensual.periodo == periodo,
            )
        )
        return int(r.scalar_one_or_none() or 0) + 1

    async def crear_calculada(
        self, tenant_id: uuid.UUID, periodo: str, liquidacion_id: uuid.UUID,
        contenido: dict, hash_sha256: str,
    ) -> m.CarpetaMensual:
        version = await self.siguiente_version(tenant_id, periodo)
        carpeta = m.CarpetaMensual(
            tenant_id=tenant_id, periodo=periodo, version=version,
            estado="calculada", contenido=contenido, hash_sha256=hash_sha256,
            liquidacion_id=liquidacion_id,
        )
        self.s.add(carpeta)
        await self.s.flush()
        return carpeta

    async def listar_periodo(
        self, tenant_id: uuid.UUID, periodo: str,
    ) -> List[m.CarpetaMensual]:
        r = await self.s.execute(
            select(m.CarpetaMensual).where(
                m.CarpetaMensual.tenant_id == tenant_id,
                m.CarpetaMensual.periodo == periodo,
            ).order_by(m.CarpetaMensual.version.desc())
        )
        return list(r.scalars().all())


# --------------------------------------------------------------------------- #
# Auditoría (append-only)
# --------------------------------------------------------------------------- #
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
