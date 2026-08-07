"""Modelos ORM (SQLAlchemy 2.0).

Tablas GLOBALES (parámetros legales, sin tenant_id) y tablas POR TENANT (con
tenant_id + RLS). Las políticas RLS se crean en la migración Alembic, no acá.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TenantMixin, new_uuid, now_utc

UUIDPK = lambda: mapped_column(PGUUID(as_uuid=True), primary_key=True, default=new_uuid)  # noqa: E731
MONEY = Numeric(18, 2)
PCT = Numeric(12, 8)


# --------------------------------------------------------------------------- #
# GLOBALES (parámetros legales) — sin tenant_id, compartidas entre tenants
# --------------------------------------------------------------------------- #
class Cct(Base):
    __tablename__ = "cct"
    id: Mapped[uuid.UUID] = UUIDPK()
    numero: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(200))
    sindicato: Mapped[str] = mapped_column(String(200), default="")
    cuota_sindical_pct: Mapped[Decimal] = mapped_column(PCT, default=Decimal("0"))
    # Parámetros de cálculo del convenio (para construir CctConfig)
    antiguedad_pct_por_anio: Mapped[Decimal] = mapped_column(PCT, default=Decimal("0.01"))
    presentismo_divisor: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("12"))
    divisor_horas: Mapped[Decimal] = mapped_column(Numeric(12, 4), default=Decimal("200"))
    aplica_presentismo: Mapped[bool] = mapped_column(Boolean, default=True)
    aplica_cuota_sindical: Mapped[bool] = mapped_column(Boolean, default=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class EscalaSalarial(Base):
    __tablename__ = "escala_salarial"
    id: Mapped[uuid.UUID] = UUIDPK()
    cct_numero: Mapped[str] = mapped_column(String(20), index=True)
    categoria: Mapped[str] = mapped_column(String(120))
    basico: Mapped[Decimal] = mapped_column(MONEY)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fuente: Mapped[str] = mapped_column(Text, default="")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)


class ParametroLegal(Base):
    __tablename__ = "parametro_legal"
    id: Mapped[uuid.UUID] = UUIDPK()
    codigo: Mapped[str] = mapped_column(String(60), index=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    unidad: Mapped[str] = mapped_column(String(8))       # "%" | "ARS"
    ambito: Mapped[str] = mapped_column(String(12))      # "empleado" | "empleador"
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fuente: Mapped[str] = mapped_column(Text, default="")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)


class AmparoCct(Base):
    __tablename__ = "amparo_cct"
    id: Mapped[uuid.UUID] = UUIDPK()
    cct_numero: Mapped[str] = mapped_column(String(20), index=True)
    articulo_suspendido: Mapped[str] = mapped_column(String(40))
    concepto_afectado: Mapped[str] = mapped_column(String(60))
    juzgado: Mapped[str] = mapped_column(String(200), default="")
    fecha_cautelar: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="vigente")
    fuente: Mapped[str] = mapped_column(Text, default="")
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)


# --------------------------------------------------------------------------- #
# USUARIOS (globales: un usuario puede pertenecer a varios tenants)
# --------------------------------------------------------------------------- #
class Usuario(Base):
    __tablename__ = "usuario"
    id: Mapped[uuid.UUID] = UUIDPK()
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Tenant(Base):
    __tablename__ = "tenant"
    id: Mapped[uuid.UUID] = UUIDPK()
    razon_social: Mapped[str] = mapped_column(String(200))
    cuit: Mapped[str] = mapped_column(String(13), index=True)
    plan: Mapped[str] = mapped_column(String(30), default="free")
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UsuarioTenant(TenantMixin, Base):
    __tablename__ = "usuario_tenant"
    id: Mapped[uuid.UUID] = UUIDPK()
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuario.id"), index=True
    )
    rol: Mapped[str] = mapped_column(String(20))  # admin | liquidador | consulta


# --------------------------------------------------------------------------- #
# POR TENANT (con tenant_id + RLS)
# --------------------------------------------------------------------------- #
class Empleado(TenantMixin, Base):
    __tablename__ = "empleado"
    id: Mapped[uuid.UUID] = UUIDPK()
    nombre: Mapped[str] = mapped_column(String(120))
    apellido: Mapped[str] = mapped_column(String(120))
    cuil: Mapped[str] = mapped_column(String(11), index=True)
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    fecha_egreso: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cct_numero: Mapped[str] = mapped_column(String(20))
    categoria: Mapped[str] = mapped_column(String(120))
    obra_social_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    remuneracion_pactada: Mapped[Optional[Decimal]] = mapped_column(MONEY, nullable=True)
    proporcion_jornada: Mapped[Decimal] = mapped_column(Numeric(6, 4), default=Decimal("1"))
    afiliado_sindicato: Mapped[bool] = mapped_column(Boolean, default=True)
    legajo: Mapped[str] = mapped_column(String(40), default="")
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    # --- datos adicionales para el recibo de sueldo (LCT art. 140 / Anexo III) ---
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sexo: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    estado_civil: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    domicilio: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    cantidad_hijos: Mapped[int] = mapped_column(Integer, default=0)
    conyuge_a_cargo: Mapped[bool] = mapped_column(Boolean, default=False)
    obra_social: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    modalidad_contrato: Mapped[str] = mapped_column(String(30), default="Tiempo indeterminado")
    cbu: Mapped[Optional[str]] = mapped_column(String(22), nullable=True)
    # Forma de pago exigida por ARCA (LSD): 1 efectivo, 2 cheque,
    # 3 acreditación en cuenta (exige CBU), 4 otra.
    forma_pago: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    lugar_trabajo: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Liquidacion(TenantMixin, Base):
    __tablename__ = "liquidacion"
    id: Mapped[uuid.UUID] = UUIDPK()
    periodo: Mapped[str] = mapped_column(String(7))       # YYYY-MM
    tipo: Mapped[str] = mapped_column(String(20))          # mensual | sac | vacaciones | final
    estado: Mapped[str] = mapped_column(String(20), default="borrador")  # borrador|confirmada|anulada
    # Copia inmutable de todos los parámetros usados (reproducibilidad histórica)
    snapshot_parametros: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    detalles: Mapped[list["LiquidacionDetalle"]] = relationship(
        back_populates="liquidacion", cascade="all, delete-orphan"
    )


class LiquidacionDetalle(TenantMixin, Base):
    __tablename__ = "liquidacion_detalle"
    id: Mapped[uuid.UUID] = UUIDPK()
    liquidacion_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("liquidacion.id"), index=True
    )
    empleado_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), index=True)
    # Conceptos como JSONB (código, descripción, tipo, importe, régimen, artículo).
    conceptos: Mapped[list] = mapped_column(JSONB, default=list)
    bruto: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    total_deducciones: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    neto: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    liquidacion: Mapped["Liquidacion"] = relationship(back_populates="detalles")


class Recibo(TenantMixin, Base):
    __tablename__ = "recibo"
    id: Mapped[uuid.UUID] = UUIDPK()
    liquidacion_detalle_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("liquidacion_detalle.id"), index=True
    )
    pdf_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hash_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    enviado_email_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    """Append-only. Sin tenant_id NOT NULL: registra también acciones sin tenant
    (login). Se protege con permisos de BD (sin UPDATE/DELETE) en la migración."""

    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = UUIDPK()
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    usuario_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    accion: Mapped[str] = mapped_column(String(60))
    entidad: Mapped[str] = mapped_column(String(60))
    entidad_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload_diff: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


# Tablas de datos de negocio sujetas a RLS (la migración crea las políticas).
# Las tablas de auth (tenant, usuario, usuario_tenant) se scopean en la capa de
# aplicación con chequeo explícito de membresía (ver DECISIONS D-14).
TABLAS_CON_RLS = (
    "empleado",
    "liquidacion",
    "liquidacion_detalle",
    "recibo",
)
