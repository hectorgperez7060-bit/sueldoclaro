"""Repositorios concretos (implementan los puertos del dominio con el ORM).

El filtrado por tenant lo enforcea RLS a nivel de PostgreSQL: la sesión ya trae
``app.current_tenant`` seteado, así que estas consultas no repiten el filtro
(defensa en profundidad: además se podría filtrar en app).
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.jornada import horas_desde_reglas
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
from domain.entities.fatfa_659_13 import configurar_adicionales_fatfa
from domain.entities.zonificacion_salarial import normalizar_provincia
from domain.payroll_engine.config import CctConfig, ReglaAdicionalConfig
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

    async def crear(self, email: str, password_hash: str,
                    modo_cuenta: str = "ESTUDIO") -> m.Usuario:
        u = m.Usuario(email=email.lower(), password_hash=password_hash,
                      modo_cuenta=modo_cuenta)
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

    async def crear(
        self, tenant_id: uuid.UUID, razon_social: str, cuit: str,
        grupo_cliente: str = "",
    ) -> m.Tenant:
        t = m.Tenant(
            id=tenant_id, razon_social=razon_social, cuit=cuit,
            grupo_cliente=grupo_cliente,
        )
        self.s.add(t)
        await self.s.flush()
        return t

    async def agregar_miembro(self, tenant_id: uuid.UUID, usuario_id: uuid.UUID, rol: str) -> None:
        self.s.add(m.UsuarioTenant(tenant_id=tenant_id, usuario_id=usuario_id, rol=rol))
        await self.s.flush()

    async def obtener(self, tenant_id: uuid.UUID) -> Optional[m.Tenant]:
        return await self.s.get(m.Tenant, tenant_id)

    async def actualizar_perfil_laboral(
        self,
        tenant: m.Tenant,
        modo_liquidacion: str,
        actividad_sector: str,
        condicion_mipyme: str,
        certificado_mipyme_vigente_hasta: Optional[date],
        respaldo_regimen_patronal: str,
        regimen_contribucion_patronal: str,
        fundamento_regimen_patronal: str,
    ) -> m.Tenant:
        tenant.modo_liquidacion = modo_liquidacion
        tenant.actividad_sector = actividad_sector
        tenant.condicion_mipyme = condicion_mipyme
        tenant.certificado_mipyme_vigente_hasta = certificado_mipyme_vigente_hasta
        tenant.respaldo_regimen_patronal = respaldo_regimen_patronal
        tenant.regimen_contribucion_patronal = regimen_contribucion_patronal
        tenant.fundamento_regimen_patronal = fundamento_regimen_patronal
        await self.s.flush()
        return tenant

    async def listar_del_usuario(self, usuario_id: uuid.UUID) -> list[tuple[m.Tenant, str]]:
        r = await self.s.execute(
            select(m.Tenant, m.UsuarioTenant.rol)
            .join(m.UsuarioTenant, m.UsuarioTenant.tenant_id == m.Tenant.id)
            .where(
                m.UsuarioTenant.usuario_id == usuario_id,
                m.Tenant.estado == "activo",
            )
            .order_by(m.Tenant.razon_social)
        )
        return [(tenant, rol) for tenant, rol in r.all()]


# --------------------------------------------------------------------------- #
# Empleado (RLS)
# --------------------------------------------------------------------------- #
class EstablecimientoRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def crear(self, tenant_id: uuid.UUID, datos: dict) -> m.Establecimiento:
        establecimiento = m.Establecimiento(tenant_id=tenant_id, **datos)
        self.s.add(establecimiento)
        await self.s.flush()
        return establecimiento

    async def listar(self, incluir_inactivos: bool = False) -> list[m.Establecimiento]:
        query = select(m.Establecimiento)
        if not incluir_inactivos:
            query = query.where(m.Establecimiento.activo.is_(True))
        r = await self.s.execute(query.order_by(m.Establecimiento.nombre))
        return list(r.scalars().all())

    async def obtener(
        self, tenant_id: uuid.UUID, establecimiento_id: uuid.UUID,
    ) -> Optional[m.Establecimiento]:
        r = await self.s.execute(
            select(m.Establecimiento).where(
                m.Establecimiento.id == establecimiento_id,
                m.Establecimiento.tenant_id == tenant_id,
            )
        )
        return r.scalar_one_or_none()


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

    async def asignar_establecimiento(
        self, tenant_id: uuid.UUID, empleado: m.Empleado,
        establecimiento: Optional[m.Establecimiento], vigente_desde: date,
    ) -> None:
        if empleado.establecimiento_id == (establecimiento.id if establecimiento else None):
            return
        r = await self.s.execute(
            select(m.EmpleadoEstablecimientoHistorial).where(
                m.EmpleadoEstablecimientoHistorial.tenant_id == tenant_id,
                m.EmpleadoEstablecimientoHistorial.empleado_id == empleado.id,
                m.EmpleadoEstablecimientoHistorial.vigente_hasta.is_(None),
            )
        )
        actual = r.scalar_one_or_none()
        if actual:
            if vigente_desde <= actual.vigente_desde:
                raise ValueError("La fecha del cambio debe ser posterior a la asignación vigente")
            actual.vigente_hasta = vigente_desde - timedelta(days=1)
        empleado.establecimiento_id = establecimiento.id if establecimiento else None
        empleado.lugar_trabajo = (
            f"{establecimiento.nombre} - {establecimiento.domicilio}"
            + (f", {establecimiento.localidad}" if establecimiento.localidad else "")
            if establecimiento else None
        )
        if establecimiento:
            self.s.add(m.EmpleadoEstablecimientoHistorial(
                tenant_id=tenant_id, empleado_id=empleado.id,
                establecimiento_id=establecimiento.id,
                vigente_desde=vigente_desde,
            ))
        await self.s.flush()


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

    async def horas_jornada_por_cct(self) -> dict[str, Decimal]:
        """Horas de jornada completa que declara la regla JORNADA de cada CCT.

        Sin esto, la importación prorratearía toda jornada contra 48 horas y
        recortaría el sueldo de un trabajador de jornada completa en cualquier
        convenio de 44 o 45 horas.
        """
        filas = await self.s.execute(
            select(m.CctReglaEstructural).where(
                m.CctReglaEstructural.codigo == "JORNADA",
                m.CctReglaEstructural.activa.is_(True),
            )
        )
        horas: dict[str, Decimal] = {}
        for regla in filas.scalars().all():
            valor = horas_desde_reglas([regla])
            if valor is not None:
                horas[regla.cct_numero] = valor
        return horas

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
            select(m.CctCategoria.cct_numero, m.CctCategoria.nombre)
            .where(
                m.CctCategoria.cct_numero.in_(catalogo),
                m.CctCategoria.activa.is_(True),
            )
            .distinct()
        )
        for cct_numero, categoria in r.all():
            catalogo[cct_numero].add(categoria)
        # Compatibilidad durante el despliegue: una escala histórica también
        # hace visible su categoría aunque la migración estructural todavía no
        # se haya ejecutado. La fuente principal sigue siendo cct_categoria.
        r = await self.s.execute(
            select(m.EscalaSalarial.cct_numero, m.EscalaSalarial.categoria)
            .where(m.EscalaSalarial.cct_numero.in_(catalogo))
            .distinct()
        )
        for cct_numero, categoria in r.all():
            catalogo[cct_numero].add(categoria)
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

    async def zona_escala(
        self, cct_numero: str, establecimiento_id: Optional[uuid.UUID], fecha: date,
    ) -> tuple[str, Optional[str]]:
        """Resuelve una zona solo si el CCT declara una regla de zonificación."""
        r = await self.s.execute(select(m.CctReglaEstructural).where(
            m.CctReglaEstructural.cct_numero == cct_numero,
            m.CctReglaEstructural.codigo == "ZONIFICACION",
            m.CctReglaEstructural.activa.is_(True),
            m.CctReglaEstructural.is_verified.is_(True),
        ).order_by(m.CctReglaEstructural.version.desc()))
        regla = r.scalars().first()
        if regla is None:
            return "", None
        if establecimiento_id is None:
            return "", "El trabajador no tiene establecimiento laboral asignado para resolver la zona salarial"
        establecimiento = await self.s.get(m.Establecimiento, establecimiento_id)
        if establecimiento is None or not (establecimiento.provincia or "").strip():
            return "", "El establecimiento no tiene provincia informada para resolver la zona salarial"
        # Las zonas son históricas: nunca se resuelven desde un mapa fijo.
        filas = (await self.s.execute(select(m.CctZonaVigencia).where(
            m.CctZonaVigencia.cct_numero == cct_numero,
            m.CctZonaVigencia.is_verified.is_(True),
            m.CctZonaVigencia.valid_from <= fecha,
            (m.CctZonaVigencia.valid_to.is_(None))
            | (m.CctZonaVigencia.valid_to >= fecha),
        ).order_by(m.CctZonaVigencia.valid_from.desc()))).scalars().all()
        buscada = normalizar_provincia(establecimiento.provincia)
        zona = next((f.zona for f in filas if normalizar_provincia(f.provincia) == buscada), None)
        if zona is None:
            return "", (
                f"La provincia {establecimiento.provincia} no tiene una zona salarial "
                f"verificada para {fecha:%Y-%m}"
            )
        return zona, None

    async def escala(
        self, cct_numero: str, categoria: str, fecha: date, zona: str = "",
    ) -> Optional[EscalaDom]:
        r = await self.s.execute(
            select(m.EscalaSalarial).where(
                m.EscalaSalarial.cct_numero == cct_numero,
                m.EscalaSalarial.categoria == categoria,
                m.EscalaSalarial.zona == zona,
                m.EscalaSalarial.valid_from <= fecha,
                (m.EscalaSalarial.valid_to.is_(None)) | (m.EscalaSalarial.valid_to >= fecha),
            ).order_by(m.EscalaSalarial.valid_from.desc())
        )
        e = r.scalars().first()
        if not e:
            return None
        basico_puro = getattr(e, "basico_puro", None)
        adicional_zona = getattr(e, "adicional_zona", None)
        return EscalaDom(
            e.cct_numero, e.categoria, Dinero(Decimal(e.basico)),
            e.valid_from, e.valid_to, e.is_verified, e.fuente,
            getattr(e, "provisoria", False), getattr(e, "zona", ""),
            getattr(e, "unidad_escala", "MENSUAL"),
            getattr(e, "habilitada_liquidacion", True),
            getattr(e, "estado_fuente", "VERIFICADA_OFICIAL"),
            Dinero(Decimal(basico_puro)) if basico_puro is not None else None,
            Dinero(Decimal(adicional_zona)) if adicional_zona is not None else None,
        )


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
        elif cct_numero == "659/13":
            fecha = fecha or date.today()
            r = await self.s.execute(select(m.CctReglaEstructural).where(
                m.CctReglaEstructural.cct_numero == cct_numero,
                m.CctReglaEstructural.activa.is_(True),
                m.CctReglaEstructural.codigo.in_((
                    "ANTIGUEDAD_ESCALONADA", "TITULOS_FARMACEUTICOS_2026_08",
                )),
            ))
            reglas = {regla.codigo: regla for regla in r.scalars().all()}
            regla_antiguedad = reglas.get("ANTIGUEDAD_ESCALONADA")
            configuracion = (
                regla_antiguedad.configuracion or {}
                if regla_antiguedad and regla_antiguedad.is_verified else {}
            )
            if configuracion.get("escalones"):
                escalones = tuple(
                    (int(item["desde"]), Decimal(str(item["porcentaje"])))
                    for item in configuracion["escalones"]
                )
            regla_titulos = reglas.get("TITULOS_FARMACEUTICOS_2026_08")
            config_titulos = (regla_titulos.configuracion or {}) if regla_titulos else {}
            vigente_titulos = (
                config_titulos.get("vigencia_desde", "") <= fecha.isoformat()
                <= config_titulos.get("vigencia_hasta", "")
            )
            escala_aprendiz = (await self.s.execute(
                select(m.EscalaSalarial).where(
                    m.EscalaSalarial.cct_numero == cct_numero,
                    m.EscalaSalarial.categoria == "Aprendiz Ayudante",
                    m.EscalaSalarial.valid_from <= fecha,
                    (m.EscalaSalarial.valid_to.is_(None))
                    | (m.EscalaSalarial.valid_to >= fecha),
                ).order_by(m.EscalaSalarial.valid_from.desc())
            )).scalars().first()
            claves_titulo = (
                "BLOQUEO_DT", "BLOQUEO_DT_NR", "AUX_BLOQUEO",
                "AUX_BLOQUEO_NR", "TITULO_60", "TITULO_60_NR",
            )
            if escala_aprendiz is not None and vigente_titulos and all(
                clave in config_titulos for clave in claves_titulo
            ):
                adicionales, referencias = configurar_adicionales_fatfa(
                    Decimal(escala_aprendiz.basico),
                    {clave: Decimal(str(config_titulos[clave])) for clave in claves_titulo},
                )
        elif cct_numero == "389/04":
            r = await self.s.execute(select(m.CctReglaEstructural).where(
                m.CctReglaEstructural.cct_numero == cct_numero,
                m.CctReglaEstructural.activa.is_(True),
                m.CctReglaEstructural.is_verified.is_(True),
                m.CctReglaEstructural.codigo.in_((
                    "ANTIGUEDAD_ESCALONADA", "ASISTENCIA_PERFECTA",
                    "COMPLEMENTO_SERVICIO",
                )),
            ))
            reglas = {regla.codigo: (regla.configuracion or {})
                      for regla in r.scalars().all()}
            ant = reglas.get("ANTIGUEDAD_ESCALONADA", {})
            if ant.get("escalones"):
                escalones = tuple(
                    (int(item["desde"]), Decimal(str(item["porcentaje"])))
                    for item in ant["escalones"]
                )
            adicionales_uthgra = []
            for codigo, descripcion, articulo in (
                ("ASISTENCIA_PERFECTA", "Asistencia perfecta", "11.5"),
                ("COMPLEMENTO_SERVICIO", "Complemento de servicio", "11.6"),
            ):
                configuracion = reglas.get(codigo)
                if configuracion and configuracion.get("porcentaje") is not None:
                    adicionales_uthgra.append(ReglaAdicionalConfig(
                        codigo=codigo,
                        descripcion=descripcion,
                        porcentaje=Decimal(str(configuracion["porcentaje"])),
                        base="basico_categoria",
                        articulo=articulo,
                        # El complemento de servicio corresponde a todo el
                        # personal. La asistencia perfecta sólo se agrega si
                        # fue confirmada en la novedad mensual.
                        aplica_automaticamente=(
                            codigo == "COMPLEMENTO_SERVICIO"
                        ),
                    ))
            adicionales = tuple(adicionales_uthgra)

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

    async def descartar(self, liquidacion: m.Liquidacion) -> None:
        """Elimina un intento incompleto sin dejar detalles huérfanos."""
        await self.s.execute(
            delete(m.LiquidacionDetalle).where(
                m.LiquidacionDetalle.liquidacion_id == liquidacion.id
            )
        )
        await self.s.delete(liquidacion)
        await self.s.flush()

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

    async def ultima(
        self, tenant_id: uuid.UUID, periodo: str,
    ) -> Optional[m.CarpetaMensual]:
        r = await self.s.execute(
            select(m.CarpetaMensual).where(
                m.CarpetaMensual.tenant_id == tenant_id,
                m.CarpetaMensual.periodo == periodo,
            ).order_by(m.CarpetaMensual.version.desc()).limit(1)
        )
        return r.scalar_one_or_none()

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

    async def listar_todas(
        self, tenant_id: uuid.UUID,
    ) -> List[m.CarpetaMensual]:
        r = await self.s.execute(
            select(m.CarpetaMensual).where(
                m.CarpetaMensual.tenant_id == tenant_id,
            ).order_by(
                m.CarpetaMensual.periodo.desc(),
                m.CarpetaMensual.version.desc(),
            )
        )
        return list(r.scalars().all())

    async def crear_obligaciones(
        self, tenant_id: uuid.UUID, carpeta_id: uuid.UUID, obligaciones: list[dict],
    ) -> List[m.ObligacionPagoMensual]:
        creadas = []
        for datos in obligaciones:
            fila = m.ObligacionPagoMensual(
                tenant_id=tenant_id, carpeta_id=carpeta_id, **datos
            )
            self.s.add(fila)
            creadas.append(fila)
        await self.s.flush()
        return creadas

    async def listar_obligaciones(
        self, tenant_id: uuid.UUID, carpeta_id: uuid.UUID,
    ) -> List[m.ObligacionPagoMensual]:
        r = await self.s.execute(
            select(m.ObligacionPagoMensual).where(
                m.ObligacionPagoMensual.tenant_id == tenant_id,
                m.ObligacionPagoMensual.carpeta_id == carpeta_id,
            ).order_by(m.ObligacionPagoMensual.tipo, m.ObligacionPagoMensual.destino_pago)
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
