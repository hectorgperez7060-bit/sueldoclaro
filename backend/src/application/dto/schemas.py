"""DTOs de la API (Pydantic v2)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# --- Auth ---
MODOS_CUENTA = ("ESTUDIO", "EMPRESA")


class RegistroEstudio(BaseModel):
    razon_social: str
    cuit: str = Field(min_length=11, max_length=13)
    email: EmailStr
    password: str = Field(min_length=8)
    # ESTUDIO lleva empresas clientes; EMPRESA es una sola, con menos datos.
    modo_cuenta: str = "ESTUDIO"

    @field_validator("modo_cuenta")
    @classmethod
    def _modo_valido(cls, valor: str) -> str:
        valor = (valor or "ESTUDIO").upper()
        if valor not in MODOS_CUENTA:
            raise ValueError("Elegí si la cuenta es de un estudio contable o de una empresa")
        return valor


class ModoCuenta(BaseModel):
    modo_cuenta: str

    @field_validator("modo_cuenta")
    @classmethod
    def _modo_valido(cls, valor: str) -> str:
        valor = (valor or "").upper()
        if valor not in MODOS_CUENTA:
            raise ValueError("Elegí si la cuenta es de un estudio contable o de una empresa")
        return valor


class PerfilCuenta(BaseModel):
    email: str
    modo_cuenta: str
    empresas: int = 0


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


class EmpresaIn(BaseModel):
    razon_social: str = Field(min_length=2, max_length=200)
    cuit: str = Field(min_length=11, max_length=13)
    grupo_cliente: str = Field(default="", max_length=200)


class EmpresaOut(BaseModel):
    id: str
    razon_social: str
    cuit: str
    grupo_cliente: str = ""
    modo_liquidacion: str = "PRUEBA"
    actividad_sector: str = "PENDIENTE"
    condicion_mipyme: str = "PENDIENTE"
    certificado_mipyme_vigente_hasta: Optional[date] = None
    respaldo_regimen_patronal: str = ""
    regimen_contribucion_patronal: str = "PENDIENTE"
    fundamento_regimen_patronal: str = ""
    rol: str
    activa: bool = False


class PerfilLaboralEmpresa(BaseModel):
    modo_liquidacion: str
    actividad_sector: str
    condicion_mipyme: str
    certificado_mipyme_vigente_hasta: Optional[date] = None
    respaldo_regimen_patronal: str = Field(default="", max_length=1000)


class SeleccionarEmpresa(BaseModel):
    tenant_id: str


class EstablecimientoIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    domicilio: str = Field(min_length=3, max_length=200)
    localidad: str = Field(default="", max_length=120)
    provincia: str = Field(default="", max_length=120)
    actividad: str = Field(default="", max_length=120)
    art_nombre: str = Field(default="", max_length=160)
    art_alicuota_pct: Optional[Decimal] = Field(default=None, ge=0, le=100)
    art_suma_fija: Optional[Decimal] = Field(default=None, ge=0)
    art_vigencia_desde: Optional[date] = None
    art_vigencia_hasta: Optional[date] = None
    art_comprobante_ref: str = Field(default="", max_length=500)
    activo: bool = True


class EstablecimientoOut(EstablecimientoIn):
    id: str


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
    proporcion_jornada: Decimal = Field(default=Decimal("1"), gt=0, le=1)
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
    establecimiento_id: Optional[str] = None
    lugar_trabajo_desde: Optional[date] = None
    # Datos estructurados para resolver la cuota sindical de afiliado (Art. 101).
    localidad: Optional[str] = None
    filial_sindical: Optional[str] = None
    # Perfil registral ARCA. Puede quedar incompleto al crear la ficha; la
    # exportación LSD informa cada faltante y no genera un TXT engañoso.
    perfil_arca: dict = Field(default_factory=dict)

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
    proporcion_jornada: Decimal = Decimal("1")
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
    establecimiento_id: Optional[str] = None
    localidad: Optional[str] = None
    filial_sindical: Optional[str] = None
    perfil_arca: dict = Field(default_factory=dict)


# --- Novedades mensuales ---
class NovedadMensualIn(BaseModel):
    empleado_id: str
    periodo: str
    dias_trabajados: int = 0
    faltas_justificadas: int = 0
    faltas_injustificadas: int = 0
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    feriados_trabajados: int = 0
    feriados_no_trabajados: int = 0
    licencias: int = 0
    vacaciones: int = 0
    premios: Decimal = Decimal("0")
    tipo_premio: str = "pendiente"
    descuentos_adicionales: Decimal = Decimal("0")
    observaciones: str = ""
    adicionales_convencionales: List[str] = Field(default_factory=list)
    cantidades_adicionales: dict[str, Decimal] = Field(default_factory=dict)
    horas_normales_q1: Optional[Decimal] = None
    horas_normales_q2: Optional[Decimal] = None
    asistencia_perfecta_q1: Optional[bool] = None
    asistencia_perfecta_q2: Optional[bool] = None
    feriados_habilitados_q1: int = 0
    feriados_habilitados_q2: int = 0
    feriados_uocra_detalle: List[dict] = Field(default_factory=list)
    fcl_criterio_aniversario: Optional[str] = None
    fcl_aprobado_por: Optional[str] = None
    fcl_fundamento: Optional[str] = None
    base_contribucion_uocra_mes_anterior: Optional[Decimal] = Field(default=None, ge=0)
    horas_extra_uocra_detalle: List[dict] = Field(default_factory=list)
    horas_extra_uocra_acumuladas_anio: Decimal = Field(default=Decimal("0"), ge=0, le=200)
    horas_hormigon_manual_uocra: Decimal = Field(default=Decimal("0"), ge=0)
    horas_altura_uocra: Decimal = Field(default=Decimal("0"), ge=0)
    altura_metros_uocra: Optional[Decimal] = Field(default=None, ge=0)
    camioneros_detalle: dict = Field(default_factory=dict)
    uom_detalle: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validar_novedad(self):
        import uuid

        from domain.entities.novedad import DatosNovedadMensual

        try:
            uuid.UUID(self.empleado_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("Identificador de empleado inválido") from exc
        DatosNovedadMensual(**self._datos())
        return self

    def _datos(self):
        datos = self.model_dump(exclude={"empleado_id"})
        datos["adicionales_convencionales"] = tuple(datos["adicionales_convencionales"])
        datos["cantidades_adicionales"] = tuple(datos["cantidades_adicionales"].items())
        datos["feriados_uocra_detalle"] = tuple(datos["feriados_uocra_detalle"])
        datos["horas_extra_uocra_detalle"] = tuple(datos["horas_extra_uocra_detalle"])
        return datos

    def datos_dominio(self):
        from domain.entities.novedad import DatosNovedadMensual

        return DatosNovedadMensual(**self._datos())


class NovedadMensualUpdate(BaseModel):
    periodo: str
    dias_trabajados: int = 0
    faltas_justificadas: int = 0
    faltas_injustificadas: int = 0
    horas_extra_50: Decimal = Decimal("0")
    horas_extra_100: Decimal = Decimal("0")
    feriados_trabajados: int = 0
    feriados_no_trabajados: int = 0
    licencias: int = 0
    vacaciones: int = 0
    premios: Decimal = Decimal("0")
    tipo_premio: str = "pendiente"
    descuentos_adicionales: Decimal = Decimal("0")
    observaciones: str = ""
    adicionales_convencionales: List[str] = Field(default_factory=list)
    cantidades_adicionales: dict[str, Decimal] = Field(default_factory=dict)
    horas_normales_q1: Optional[Decimal] = None
    horas_normales_q2: Optional[Decimal] = None
    asistencia_perfecta_q1: Optional[bool] = None
    asistencia_perfecta_q2: Optional[bool] = None
    feriados_habilitados_q1: int = 0
    feriados_habilitados_q2: int = 0
    feriados_uocra_detalle: List[dict] = Field(default_factory=list)
    fcl_criterio_aniversario: Optional[str] = None
    fcl_aprobado_por: Optional[str] = None
    fcl_fundamento: Optional[str] = None
    base_contribucion_uocra_mes_anterior: Optional[Decimal] = Field(default=None, ge=0)
    horas_extra_uocra_detalle: List[dict] = Field(default_factory=list)
    horas_extra_uocra_acumuladas_anio: Decimal = Field(default=Decimal("0"), ge=0, le=200)
    horas_hormigon_manual_uocra: Decimal = Field(default=Decimal("0"), ge=0)
    horas_altura_uocra: Decimal = Field(default=Decimal("0"), ge=0)
    altura_metros_uocra: Optional[Decimal] = Field(default=None, ge=0)
    camioneros_detalle: dict = Field(default_factory=dict)
    uom_detalle: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validar_novedad(self):
        from domain.entities.novedad import DatosNovedadMensual

        DatosNovedadMensual(**self._datos())
        return self

    def _datos(self):
        datos = self.model_dump()
        datos["adicionales_convencionales"] = tuple(datos["adicionales_convencionales"])
        datos["cantidades_adicionales"] = tuple(datos["cantidades_adicionales"].items())
        datos["feriados_uocra_detalle"] = tuple(datos["feriados_uocra_detalle"])
        datos["horas_extra_uocra_detalle"] = tuple(datos["horas_extra_uocra_detalle"])
        return datos

    def datos_dominio(self):
        from domain.entities.novedad import DatosNovedadMensual

        return DatosNovedadMensual(**self._datos())


class NovedadLoteIn(NovedadMensualUpdate):
    """La misma novedad para varios empleados a la vez.

    ``empleado_ids`` vacío significa todo el plantel activo del período. Existe
    porque cargar de a uno diez legajos con el mismo mes es la parte que hace que
    la gente termine poniendo cualquier cosa.
    """

    empleado_ids: Optional[List[str]] = None

    def _datos(self):
        datos = self.model_dump(exclude={"empleado_ids"})
        datos["adicionales_convencionales"] = tuple(datos["adicionales_convencionales"])
        datos["cantidades_adicionales"] = tuple(datos["cantidades_adicionales"].items())
        datos["feriados_uocra_detalle"] = tuple(datos["feriados_uocra_detalle"])
        datos["horas_extra_uocra_detalle"] = tuple(datos["horas_extra_uocra_detalle"])
        return datos


class NovedadCopiaIn(BaseModel):
    """Traer al período nuevo las novedades que ya se cargaron en otro."""

    periodo_origen: str
    periodo_destino: str
    empleado_ids: Optional[List[str]] = None

    @model_validator(mode="after")
    def _validar(self):
        from domain.entities.novedad import DatosNovedadMensual

        DatosNovedadMensual(periodo=self.periodo_origen)
        DatosNovedadMensual(periodo=self.periodo_destino)
        if self.periodo_origen == self.periodo_destino:
            raise ValueError("El período de origen y el de destino no pueden ser el mismo")
        return self


class ResultadoLoteNovedades(BaseModel):
    """Qué pasó con cada empleado. Nunca se cae todo por uno que falla."""

    creadas: int
    omitidas: int
    detalle: List[dict] = Field(default_factory=list)


class NovedadMensualOut(BaseModel):
    id: str
    empleado_id: str
    periodo: str
    dias_trabajados: int
    faltas_justificadas: int
    faltas_injustificadas: int
    horas_extra_50: Decimal
    horas_extra_100: Decimal
    feriados_trabajados: int
    feriados_no_trabajados: int
    licencias: int
    vacaciones: int
    premios: Decimal
    tipo_premio: str
    descuentos_adicionales: Decimal
    observaciones: str
    adicionales_convencionales: List[str] = Field(default_factory=list)
    cantidades_adicionales: dict[str, Decimal] = Field(default_factory=dict)
    horas_normales_q1: Optional[Decimal] = None
    horas_normales_q2: Optional[Decimal] = None
    asistencia_perfecta_q1: Optional[bool] = None
    asistencia_perfecta_q2: Optional[bool] = None
    feriados_habilitados_q1: int = 0
    feriados_habilitados_q2: int = 0
    feriados_uocra_detalle: List[dict] = Field(default_factory=list)
    fcl_criterio_aniversario: Optional[str] = None
    fcl_aprobado_por: Optional[str] = None
    fcl_fundamento: Optional[str] = None
    base_contribucion_uocra_mes_anterior: Optional[Decimal] = None
    horas_extra_uocra_detalle: List[dict] = Field(default_factory=list)
    horas_extra_uocra_acumuladas_anio: Decimal = Decimal("0")
    horas_hormigon_manual_uocra: Decimal = Decimal("0")
    horas_altura_uocra: Decimal = Decimal("0")
    altura_metros_uocra: Optional[Decimal] = None
    camioneros_detalle: dict = Field(default_factory=dict)
    uom_detalle: dict = Field(default_factory=dict)
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
    # Confirmación expresa para liquidar reutilizando la última escala verificada
    # como provisoria (p.ej. agosto reutilizando julio).
    confirmar_provisorios: bool = False


class ConceptoOut(BaseModel):
    codigo: str
    descripcion: str
    tipo: str
    importe: Decimal
    cantidad: Decimal = Decimal("1")
    base_calculo: Optional[Decimal] = None
    unidad: str = "suma fija"
    regimen: str
    articulo_amparo: Optional[str] = None
    destino_pago: Optional[str] = None
    codigo_boleta: Optional[str] = None
    canal_pago: Optional[str] = None
    url_pago: Optional[str] = None
    regla_vencimiento: Optional[str] = None
    fuente_pago: Optional[str] = None


class DetalleOut(BaseModel):
    empleado_id: str
    cct_numero: Optional[str] = None
    localidad: Optional[str] = None
    filial_sindical: Optional[str] = None
    bruto: Decimal
    total_deducciones: Decimal
    neto: Decimal
    conceptos: List[ConceptoOut]
    escala_provisoria: Optional[dict] = None
    vista_previa: bool = False


class LiquidacionOut(BaseModel):
    id: str
    periodo: str
    tipo: str
    estado: str
    detalles: List[DetalleOut]
    bloqueos: List[dict] = []
    carpeta_mensual: Optional[dict] = None


class ConceptoAjusteManualIn(BaseModel):
    codigo: str = Field(min_length=1, max_length=120)
    descripcion: str = Field(min_length=1, max_length=240)
    tipo: Literal["remunerativo", "no_remunerativo", "deduccion", "contribucion"]
    importe: Decimal = Field(ge=0)
    cantidad: Decimal = Field(default=Decimal("1"), ge=0)
    base_calculo: Optional[Decimal] = Field(default=None, ge=0)
    unidad: str = Field(default="suma fija", max_length=80)
    regimen: str = "no_aplica"
    articulo_amparo: Optional[str] = None
    destino_pago: Optional[str] = None
    codigo_boleta: Optional[str] = None
    canal_pago: Optional[str] = None
    url_pago: Optional[str] = None
    regla_vencimiento: Optional[str] = None
    fuente_pago: Optional[str] = None


class AjusteManualLiquidacionIn(BaseModel):
    motivo: str = Field(min_length=5, max_length=500)
    conceptos: List[ConceptoAjusteManualIn] = Field(min_length=1)


# --- Import xlsx ---
class ErrorFila(BaseModel):
    fila: int
    errores: List[str]


class ImportResultado(BaseModel):
    importados: int
    total_filas: int
    errores: List[ErrorFila]
