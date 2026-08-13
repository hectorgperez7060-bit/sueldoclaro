"""DTOs de la API (Pydantic v2)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


# --- Auth ---
class RegistroEstudio(BaseModel):
    razon_social: str
    cuit: str = Field(min_length=11, max_length=13)
    email: EmailStr
    password: str = Field(min_length=8)


class Login(BaseModel):
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None  # opcional: elegir empresa activa


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    tenant_id: Optional[str] = None
    rol: Optional[str] = None


# --- Empleados ---
class EmpleadoIn(BaseModel):
    nombre: str
    apellido: str
    cuil: str
    fecha_ingreso: date
    cct_numero: str
    categoria: str
    legajo: str = ""
    remuneracion_pactada: Optional[Decimal] = None
    proporcion_jornada: Decimal = Decimal("1")  # 1 = completa, 0.5 = media jornada
    afiliado_sindicato: bool = True
    email: Optional[EmailStr] = None
    # datos adicionales para el recibo
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    estado_civil: Optional[str] = None
    domicilio: Optional[str] = None
    cantidad_hijos: int = 0
    conyuge_a_cargo: bool = False
    obra_social: Optional[str] = None
    modalidad_contrato: str = "Tiempo indeterminado"
    cbu: Optional[str] = None
    # Forma de pago OBLIGATORIA (ARCA la exige para el LSD/F.931).
    # 1 efectivo, 2 cheque, 3 acreditación en cuenta (exige CBU), 4 otra.
    forma_pago: str
    lugar_trabajo: Optional[str] = None
    # Datos estructurados para resolver la cuota sindical de afiliado (Art. 101).
    localidad: Optional[str] = None
    filial_sindical: Optional[str] = None

    @model_validator(mode="after")
    def _validar_forma_pago(self):
        if self.forma_pago not in ("1", "2", "3", "4"):
            raise ValueError(
                "Forma de pago obligatoria: 1 efectivo, 2 cheque, "
                "3 acreditación en cuenta, 4 otra"
            )
        if self.forma_pago == "3":
            cbu = "".join(ch for ch in (self.cbu or "") if ch.isdigit())
            if len(cbu) != 22:
                raise ValueError(
                    "La acreditación en cuenta (forma de pago 3) exige CBU de 22 dígitos"
                )
        return self


class EmpleadoOut(BaseModel):
    id: str
    nombre: str
    apellido: str
    cuil: str
    fecha_ingreso: date
    cct_numero: str
    categoria: str
    legajo: str
    afiliado_sindicato: bool
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    estado_civil: Optional[str] = None
    domicilio: Optional[str] = None
    cantidad_hijos: int = 0
    conyuge_a_cargo: bool = False
    obra_social: Optional[str] = None
    modalidad_contrato: Optional[str] = None
    cbu: Optional[str] = None
    forma_pago: Optional[str] = None
    lugar_trabajo: Optional[str] = None
    localidad: Optional[str] = None
    filial_sindical: Optional[str] = None


# --- Novedades mensuales ---
class NovedadMensualIn(BaseModel):
    empleado_id: str
    periodo: str
    dias_trabajados: int = 0
    faltas_justificadas: int = 0
    faltas_injustificadas: int = 0
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    licencias: int = 0
    vacaciones: int = 0
    premios: Decimal = Decimal("0")
    tipo_premio: str = "pendiente"
    descuentos_adicionales: Decimal = Decimal("0")
    observaciones: str = ""

    @model_validator(mode="after")
    def _validar_novedad(self):
        import uuid

        from domain.entities.novedad import DatosNovedadMensual

        try:
            uuid.UUID(self.empleado_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("Identificador de empleado inválido") from exc
        DatosNovedadMensual(**self.model_dump(exclude={"empleado_id"}))
        return self

    def datos_dominio(self):
        from domain.entities.novedad import DatosNovedadMensual

        return DatosNovedadMensual(**self.model_dump(exclude={"empleado_id"}))


class NovedadMensualUpdate(BaseModel):
    periodo: str
    dias_trabajados: int = 0
    faltas_justificadas: int = 0
    faltas_injustificadas: int = 0
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    licencias: int = 0
    vacaciones: int = 0
    premios: Decimal = Decimal("0")
    tipo_premio: str = "pendiente"
    descuentos_adicionales: Decimal = Decimal("0")
    observaciones: str = ""

    @model_validator(mode="after")
    def _validar_novedad(self):
        from domain.entities.novedad import DatosNovedadMensual

        DatosNovedadMensual(**self.model_dump())
        return self

    def datos_dominio(self):
        from domain.entities.novedad import DatosNovedadMensual

        return DatosNovedadMensual(**self.model_dump())


class NovedadMensualOut(BaseModel):
    id: str
    empleado_id: str
    periodo: str
    dias_trabajados: int
    faltas_justificadas: int
    faltas_injustificadas: int
    horas_extra_50: Decimal
    horas_extra_100: Decimal
    licencias: int
    vacaciones: int
    premios: Decimal
    tipo_premio: str
    descuentos_adicionales: Decimal
    observaciones: str
    bloqueada: bool = False


# --- Liquidación ---
class NovedadEmpleado(BaseModel):
    empleado_id: str
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")


class LiquidarIn(BaseModel):
    periodo: str = Field(pattern=r"^\d{4}-\d{2}$")
    tipo: str = "mensual"
    novedades: List[NovedadEmpleado] = []


class ConceptoOut(BaseModel):
    codigo: str
    descripcion: str
    tipo: str
    importe: Decimal
    regimen: str
    articulo_amparo: Optional[str] = None


class DetalleOut(BaseModel):
    empleado_id: str
    bruto: Decimal
    total_deducciones: Decimal
    neto: Decimal
    conceptos: List[ConceptoOut]


class LiquidacionOut(BaseModel):
    id: str
    periodo: str
    tipo: str
    estado: str
    detalles: List[DetalleOut]
    carpeta_mensual: Optional[dict] = None


# --- Import xlsx ---
class ErrorFila(BaseModel):
    fila: int
    errores: List[str]


class ImportResultado(BaseModel):
    importados: int
    total_filas: int
    errores: List[ErrorFila]
