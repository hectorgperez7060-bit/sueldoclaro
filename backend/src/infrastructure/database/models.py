"""Modelos ORM (SQLAlchemy 2.0).

Tablas GLOBALES (parámetros legales, sin tenant_id) y tablas POR TENANT (con
tenant_id + RLS). Las políticas RLS se crean en la migración Alembic, no acá.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric,
    String, Text, UniqueConstraint,
)
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


class CctCategoria(Base):
    __tablename__ = "cct_categoria"
    id: Mapped[uuid.UUID] = UUIDPK()
    cct_numero: Mapped[str] = mapped_column(String(20), index=True)
    codigo: Mapped[str] = mapped_column(String(60))
    nombre: Mapped[str] = mapped_column(String(160))
    orden: Mapped[int] = mapped_column(Integer, default=0)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    fuente: Mapped[str] = mapped_column(Text, default="")
    estado_fuente: Mapped[str] = mapped_column(String(40), default="PENDIENTE_DOCUMENTACION")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (UniqueConstraint("cct_numero", "codigo", "version"),)


class CctReglaEstructural(Base):
    __tablename__ = "cct_regla_estructural"
    id: Mapped[uuid.UUID] = UUIDPK()
    cct_numero: Mapped[str] = mapped_column(String(20), index=True)
    codigo: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[str] = mapped_column(String(40))
    descripcion: Mapped[str] = mapped_column(Text)
    articulo: Mapped[str] = mapped_column(String(40), default="")
    configuracion: Mapped[dict] = mapped_column(JSONB, default=dict)
    fuente: Mapped[str] = mapped_column(Text, default="")
    estado_fuente: Mapped[str] = mapped_column(String(40), default="PENDIENTE_DOCUMENTACION")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("cct_numero", "codigo", "version"),)


class EscalaSalarial(Base):
    __tablename__ = "escala_salarial"
    id: Mapped[uuid.UUID] = UUIDPK()
    cct_numero: Mapped[str] = mapped_column(String(20), index=True)
    categoria: Mapped[str] = mapped_column(String(120))
    basico: Mapped[Decimal] = mapped_column(MONEY)
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fuente: Mapped[str] = mapped_column(Text, default="")
    estado_fuente: Mapped[str] = mapped_column(String(40), default="PENDIENTE_DOCUMENTACION")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    # Escala provisoria (reutilización acotada de un básico verificado anterior).
    provisoria: Mapped[bool] = mapped_column(Boolean, default=False)
    zona: Mapped[str] = mapped_column(String(20), default="")
    unidad_escala: Mapped[str] = mapped_column(String(12), default="MENSUAL")
    basico_puro: Mapped[Optional[Decimal]] = mapped_column(MONEY, nullable=True)
    adicional_zona: Mapped[Optional[Decimal]] = mapped_column(MONEY, nullable=True)
    habilitada_liquidacion: Mapped[bool] = mapped_column(Boolean, default=True)


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
    estado_fuente: Mapped[str] = mapped_column(String(40), default="PENDIENTE_DOCUMENTACION")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    # Concepto propio de un convenio (null = parámetro global de ley).
    cct_numero: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # Incidencias del concepto: qué bases integra y qué aportes dispara (data-driven).
    incidencias: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class CctZonaVigencia(Base):
    """Zona salarial determinada por provincia y vigencia histórica."""

    __tablename__ = "cct_zona_vigencia"
    id: Mapped[uuid.UUID] = UUIDPK()
    cct_numero: Mapped[str] = mapped_column(String(20), index=True)
    provincia: Mapped[str] = mapped_column(String(80), index=True)
    zona: Mapped[str] = mapped_column(String(20))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fuente: Mapped[str] = mapped_column(Text, default="")
    estado_fuente: Mapped[str] = mapped_column(String(40), default="PENDIENTE_DOCUMENTACION")
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        UniqueConstraint("cct_numero", "provincia", "valid_from", "version"),
    )


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


class CuotaSindicalArt101(Base):
    """Cuota sindical del Art. 101 (afiliados), configurable por filial/localidad.

    Tabla de CONFIGURACION (global): no hay valor nacional por defecto. Un afiliado
    solo tributa Art. 101 si existe aca una fila ``is_verified`` vigente que coincida
    con su CCT + filial/localidad. Art. 100 (2%) y FAECYS (0,5%) NO viven aca:
    siguen en parametro_legal como ded_todos para todos los comprendidos.
    """

    __tablename__ = "cuota_sindical_art101"
    id: Mapped[uuid.UUID] = UUIDPK()
    cct_numero: Mapped[str] = mapped_column(String(20), index=True)
    sindicato: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    filial: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    localidad: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    porcentaje: Mapped[Decimal] = mapped_column(Numeric(12, 8))
    valid_from: Mapped[date] = mapped_column(Date)
    valid_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    fuente: Mapped[str] = mapped_column(Text, default="")
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
    grupo_cliente: Mapped[str] = mapped_column(String(200), default="")
    plan: Mapped[str] = mapped_column(String(30), default="free")
    estado: Mapped[str] = mapped_column(String(20), default="activo")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UsuarioTenant(TenantMixin, Base):
    __tablename__ = "usuario_tenant"
    id: Mapped[uuid.UUID] = UUIDPK()
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuario.id"), index=True
    )
    rol: Mapped[str] = mapped_column(String(30))  # admin|liquidador|consulta|contador_revisor


class ContadorProfesional(Base):
    """Identidad profesional global vinculada a un usuario."""

    __tablename__ = "contador_profesional"
    __table_args__ = (
        UniqueConstraint("consejo_profesional", "matricula", name="uq_contador_consejo_matricula"),
    )
    id: Mapped[uuid.UUID] = UUIDPK()
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuario.id"), unique=True, index=True
    )
    nombre_apellido: Mapped[str] = mapped_column(String(200))
    cuit: Mapped[str] = mapped_column(String(11), index=True)
    matricula: Mapped[str] = mapped_column(String(60))
    jurisdiccion: Mapped[str] = mapped_column(String(120))
    consejo_profesional: Mapped[str] = mapped_column(String(200))
    matricula_vigente: Mapped[bool] = mapped_column(Boolean, default=False)
    constancia_url: Mapped[str] = mapped_column(Text, default="")
    verificado_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


# --------------------------------------------------------------------------- #
# POR TENANT (con tenant_id + RLS)
# --------------------------------------------------------------------------- #
class Establecimiento(TenantMixin, Base):
    __tablename__ = "establecimiento"
    id: Mapped[uuid.UUID] = UUIDPK()
    nombre: Mapped[str] = mapped_column(String(120))
    domicilio: Mapped[str] = mapped_column(String(200))
    localidad: Mapped[str] = mapped_column(String(120), default="")
    provincia: Mapped[str] = mapped_column(String(120), default="")
    actividad: Mapped[str] = mapped_column(String(120), default="")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


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
    establecimiento_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("establecimiento.id"), nullable=True, index=True
    )
    # Datos estructurados para resolver la cuota sindical de afiliado (Art. 101).
    # NO se derivan del domicilio de texto libre.
    localidad: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    filial_sindical: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class EmpleadoEstablecimientoHistorial(TenantMixin, Base):
    __tablename__ = "empleado_establecimiento_historial"
    __table_args__ = (
        CheckConstraint(
            "vigente_hasta IS NULL OR vigente_hasta >= vigente_desde",
            name="vigencia_establecimiento_valida",
        ),
    )
    id: Mapped[uuid.UUID] = UUIDPK()
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("empleado.id"), nullable=False, index=True
    )
    establecimiento_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("establecimiento.id"), nullable=False, index=True
    )
    vigente_desde: Mapped[date] = mapped_column(Date, nullable=False)
    vigente_hasta: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class NovedadMensual(TenantMixin, Base):
    """Novedades capturadas para un empleado y período, aún sin calcular."""

    __tablename__ = "novedad_mensual"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "empleado_id", "periodo",
            name="uq_novedad_mensual_tenant_empleado_periodo",
        ),
        CheckConstraint(
            "periodo ~ '^[0-9]{4}-(0[1-9]|1[0-2])$'",
            name="periodo_yyyy_mm",
        ),
        CheckConstraint(
            "dias_trabajados >= 0 AND faltas_justificadas >= 0 "
            "AND faltas_injustificadas >= 0 AND licencias >= 0 AND vacaciones >= 0 "
            "AND feriados_trabajados >= 0 AND feriados_no_trabajados >= 0",
            name="dias_no_negativos",
        ),
        CheckConstraint(
            "horas_extra_50 >= 0 AND horas_extra_100 >= 0 "
            "AND premios >= 0 AND descuentos_adicionales >= 0",
            name="importes_horas_no_negativos",
        ),
        CheckConstraint(
            "tipo_premio IN ('pendiente', 'remunerativo', 'no_remunerativo')",
            name="tipo_premio_valido",
        ),
        CheckConstraint(
            "dias_trabajados <= EXTRACT(DAY FROM "
            "(TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day')) "
            "AND faltas_justificadas <= EXTRACT(DAY FROM "
            "(TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day')) "
            "AND faltas_injustificadas <= EXTRACT(DAY FROM "
            "(TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day')) "
            "AND licencias <= EXTRACT(DAY FROM "
            "(TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day')) "
            "AND vacaciones <= EXTRACT(DAY FROM "
            "(TO_DATE(periodo || '-01', 'YYYY-MM-DD') + INTERVAL '1 month - 1 day'))",
            name="dias_segun_periodo",
        ),
    )

    id: Mapped[uuid.UUID] = UUIDPK()
    empleado_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("empleado.id"), nullable=False, index=True
    )
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    dias_trabajados: Mapped[int] = mapped_column(Integer, default=0)
    faltas_justificadas: Mapped[int] = mapped_column(Integer, default=0)
    faltas_injustificadas: Mapped[int] = mapped_column(Integer, default=0)
    horas_extra_50: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    horas_extra_100: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("0"))
    feriados_trabajados: Mapped[int] = mapped_column(Integer, default=0)
    feriados_no_trabajados: Mapped[int] = mapped_column(Integer, default=0)
    licencias: Mapped[int] = mapped_column(Integer, default=0)
    vacaciones: Mapped[int] = mapped_column(Integer, default=0)
    premios: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    tipo_premio: Mapped[str] = mapped_column(String(20), default="pendiente")
    descuentos_adicionales: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    observaciones: Mapped[str] = mapped_column(Text, default="")
    adicionales_convencionales: Mapped[list] = mapped_column(JSONB, default=list)
    cantidades_adicionales: Mapped[dict] = mapped_column(JSONB, default=dict)
    horas_normales_q1: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    horas_normales_q2: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    asistencia_perfecta_q1: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    asistencia_perfecta_q2: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    feriados_habilitados_q1: Mapped[int] = mapped_column(Integer, default=0)
    feriados_habilitados_q2: Mapped[int] = mapped_column(Integer, default=0)
    feriados_uocra_detalle: Mapped[list] = mapped_column(JSONB, default=list)
    fcl_criterio_aniversario: Mapped[Optional[str]] = mapped_column(String(24), nullable=True)
    fcl_aprobado_por: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    fcl_fundamento: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    base_contribucion_uocra_mes_anterior: Mapped[Optional[Decimal]] = mapped_column(
        MONEY, nullable=True
    )
    horas_extra_uocra_detalle: Mapped[list] = mapped_column(JSONB, default=list)
    horas_extra_uocra_acumuladas_anio: Mapped[Decimal] = mapped_column(
        Numeric(8, 2), default=Decimal("0")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc
    )


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


class CarpetaMensual(TenantMixin, Base):
    __tablename__ = "carpeta_mensual"
    __table_args__ = (
        UniqueConstraint("tenant_id", "periodo", "version", name="uq_carpeta_tenant_periodo_version"),
        CheckConstraint(
            "estado IN ('borrador','calculada','revisada','presentada','aceptada','pagada')",
            name="estado_valido",
        ),
    )
    id: Mapped[uuid.UUID] = UUIDPK()
    periodo: Mapped[str] = mapped_column(String(7), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    estado: Mapped[str] = mapped_column(String(20), default="borrador")
    contenido: Mapped[dict] = mapped_column(JSONB, default=dict)
    hash_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    liquidacion_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("liquidacion.id"), nullable=True, index=True
    )
    comprobante_presentacion: Mapped[str] = mapped_column(Text, default="")
    comprobante_aceptacion: Mapped[str] = mapped_column(Text, default="")
    comprobante_pago: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class RevisionProfesional(TenantMixin, Base):
    """Constancia inmutable del profesional y contenido revisado."""

    __tablename__ = "revision_profesional"
    id: Mapped[uuid.UUID] = UUIDPK()
    carpeta_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("carpeta_mensual.id"), index=True
    )
    contador_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("contador_profesional.id"), index=True
    )
    usuario_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("usuario.id"))
    nombre_apellido: Mapped[str] = mapped_column(String(200))
    matricula: Mapped[str] = mapped_column(String(60))
    jurisdiccion: Mapped[str] = mapped_column(String(120))
    consejo_profesional: Mapped[str] = mapped_column(String(200))
    hash_revisado: Mapped[str] = mapped_column(String(64))
    alcance: Mapped[str] = mapped_column(Text, default="Revisión mensual de liquidación laboral")
    observaciones: Mapped[str] = mapped_column(Text, default="")
    firmado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


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
    "establecimiento",
    "empleado",
    "empleado_establecimiento_historial",
    "novedad_mensual",
    "liquidacion",
    "liquidacion_detalle",
    "carpeta_mensual",
    "revision_profesional",
    "recibo",
)
