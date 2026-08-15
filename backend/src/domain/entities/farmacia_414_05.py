"""Reglas estructurales del CCT 414/05 (ADEF), independientes de importes.

Fuentes: CCT 414/05 homologado por Resolución S.T. 269/2005 y modificaciones
identificadas en cada regla. Este módulo no contiene escalas monetarias.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from domain.payroll_engine.config import ReglaAdicionalConfig


CCT_FARMACIA = "414/05"

CATEGORIAS_FARMACIA = (
    "Categoría Inicial A",
    "Categoría Inicial B",
    "Cajero, Perfumería y Administrativo",
    "Empleado de Farmacia",
    "Empleado Especializado de Farmacia",
    "Farmacéutico",
)

_ALIAS_CATEGORIAS = {
    "inicial a": "Categoría Inicial A",
    "categoria inicial a": "Categoría Inicial A",
    "categoría inicial a": "Categoría Inicial A",
    "inicial b": "Categoría Inicial B",
    "categoria inicial b": "Categoría Inicial B",
    "categoría inicial b": "Categoría Inicial B",
    "cajero": "Cajero, Perfumería y Administrativo",
    "perfumeria": "Cajero, Perfumería y Administrativo",
    "perfumería": "Cajero, Perfumería y Administrativo",
    "administrativo": "Cajero, Perfumería y Administrativo",
    "empleado de farmacia": "Empleado de Farmacia",
    "empleado especializado de farmacia": "Empleado Especializado de Farmacia",
    "farmaceutico": "Farmacéutico",
    "farmacéutico": "Farmacéutico",
}

# Art. 3, texto modificado por Acuerdo 1209/2010, Res. S.T. 1165/2010.
AMBITO_TERRITORIAL_414_05 = frozenset({
    "CABA", "SAN MARTIN", "TRES DE FEBRERO", "MORON", "ITUZAINGO",
    "HURLINGHAM", "MERLO", "SAN JUSTO", "LA MATANZA", "LANUS",
    "AVELLANEDA", "SAN ISIDRO", "SAN FERNANDO", "VICENTE LOPEZ",
    "LOMAS DE ZAMORA", "ESCOBAR", "PILAR", "TIGRE", "SAN MIGUEL",
    "MALVINAS ARGENTINAS", "JOSE C PAZ", "MORENO",
})


def _normalizar(texto: str) -> str:
    tabla = str.maketrans("ÁÉÍÓÚÜÑ", "AEIOUUN")
    return " ".join(str(texto or "").upper().translate(tabla).replace(".", "").split())


def categoria_farmacia_canonica(categoria: str) -> str:
    ingresada = " ".join(str(categoria or "").strip().split())
    for canonica in CATEGORIAS_FARMACIA:
        if _normalizar(canonica) == _normalizar(ingresada):
            return canonica
    alias = _ALIAS_CATEGORIAS.get(ingresada.casefold())
    if alias:
        return alias
    raise ValueError(f"Categoría no contemplada por el CCT 414/05: {ingresada or '(vacía)'}")


def aplica_ambito_farmacia(localidad: str) -> bool:
    """No presume encuadre fuera del ámbito territorial expreso del art. 3."""
    return _normalizar(localidad) in AMBITO_TERRITORIAL_414_05


def dias_vacaciones_farmacia(anios_antiguedad: int) -> int:
    """Licencia anual del art. 24: 17, 26, 35 o 44 días corridos."""
    if anios_antiguedad < 0:
        raise ValueError("La antigüedad no puede ser negativa")
    if anios_antiguedad <= 5:
        return 17
    if anios_antiguedad <= 10:
        return 26
    if anios_antiguedad <= 20:
        return 35
    return 44


@dataclass(frozen=True)
class JornadaFarmacia:
    tipo: str
    horas_semanales: Decimal
    proporcion_salarial: Decimal
    admite_horas_extra: bool
    base_obra_social_jornada_completa: bool


def resolver_jornada_farmacia(
    horas_semanales: Decimal,
    *,
    nocturna: bool = False,
    insalubre: bool = False,
) -> JornadaFarmacia:
    """Resuelve jornadas expresamente reguladas por los arts. 14 a 16.

    Las jornadas reducidas que no encajan inequívocamente se rechazan para que
    una persona indique su régimen en vez de aplicar un prorrateo supuesto.
    """
    horas = Decimal(horas_semanales)
    if horas <= 0:
        raise ValueError("Las horas semanales deben ser positivas")
    if nocturna and insalubre:
        raise ValueError("La combinación nocturna e insalubre requiere revisión específica")
    if insalubre:
        if horas != Decimal("33"):
            raise ValueError("La jornada insalubre convencional es de 33 horas semanales")
        return JornadaFarmacia("insalubre", horas, Decimal("1"), False, True)
    if nocturna:
        if horas != Decimal("42"):
            raise ValueError("La jornada nocturna convencional es de 42 horas semanales")
        return JornadaFarmacia("nocturna", horas, Decimal("1"), False, True)
    if horas == Decimal("45"):
        return JornadaFarmacia("completa", horas, Decimal("1"), True, True)
    if horas < Decimal("30"):
        return JornadaFarmacia(
            "tiempo_parcial", horas, horas / Decimal("45"), False, True
        )
    raise ValueError(
        "La jornada reducida entre 30 y 44 horas necesita encuadre documentado"
    )


@dataclass(frozen=True)
class ReglaAdicionalFarmacia:
    codigo: str
    descripcion: str
    porcentaje: Decimal
    base: str
    articulo: str
    condicion: str


# Arts. 17 a 19. Las bases se expresan, no se calculan aquí con una fórmula
# genérica, porque cada adicional tiene una base convencional distinta.
REGLAS_ADICIONALES_FARMACIA = (
    ReglaAdicionalFarmacia("NOCTURNO_VOLUNTARIO", "Servicio nocturno voluntario", Decimal("1"), "basico_categoria", "17", "horas entre 21 y 6 en servicio voluntario o extendido; excluye serenos y vigilancia"),
    ReglaAdicionalFarmacia("TITULO_FARMACEUTICO", "Título farmacéutico", Decimal("0.58"), "basico_inicial_a_mas_antiguedad", "18.a", "farmaceutico con titulo"),
    ReglaAdicionalFarmacia("DIRECCION_TECNICA", "Dirección técnica con bloqueo", Decimal("0.88"), "basico_inicial_a", "18.b", "director tecnico con bloqueo"),
    ReglaAdicionalFarmacia("COMPLEMENTO_DIRECCION", "Complemento dirección técnica", Decimal("0.10"), "basico_farmaceutico_mas_antiguedad", "18.b", "director tecnico con bloqueo"),
    ReglaAdicionalFarmacia("AUXILIAR_CON_BLOQUEO", "Farmacéutico auxiliar con bloqueo", Decimal("0.20"), "basico_inicial_a", "18.c", "farmaceutico auxiliar con bloqueo"),
    ReglaAdicionalFarmacia("AUXILIAR_SIN_BLOQUEO", "Farmacéutico auxiliar sin bloqueo", Decimal("0.17"), "basico_inicial_a", "18.d", "farmaceutico auxiliar sin bloqueo"),
    ReglaAdicionalFarmacia("TITULO_AUXILIAR", "Título auxiliar de farmacia", Decimal("0.20"), "basico_categoria_mas_antiguedad", "18.e", "titulo y requisitos convencionales"),
    ReglaAdicionalFarmacia("TITULO_SECUNDARIO", "Título secundario", Decimal("0.05"), "basico_categoria_mas_antiguedad", "18.f", "titulo admitido"),
    ReglaAdicionalFarmacia("ADICIONAL_CAJERO", "Adicional de cajero", Decimal("0.10"), "basico_categoria_mas_antiguedad", "18.g", "tarea de cajero"),
    ReglaAdicionalFarmacia("ADMIN_PERFUMERIA", "Tareas administrativas o perfumería", Decimal("0.10"), "basico_categoria_mas_antiguedad", "18.h", "mas de 5 años en la tarea"),
    ReglaAdicionalFarmacia("IDIOMA", "Uso de idioma extranjero", Decimal("0.10"), "basico_categoria_mas_antiguedad", "18.i", "por cada idioma requerido"),
    ReglaAdicionalFarmacia("BICICLETA_CICLOMOTOR", "Uso de bicicleta o ciclomotor propio", Decimal("0.15"), "basico_inicial_b_mas_antiguedad", "18.j", "vehiculo propio requerido"),
    ReglaAdicionalFarmacia("FALLA_CAJA", "Fondo compensador por falla de caja", Decimal("0.10"), "basico_categoria", "19", "tarea de cajero; saldo no compensado remunerativo"),
)


def configurar_adicionales_farmacia(
    basico_inicial_a: Decimal,
    basico_inicial_b: Decimal,
    basico_farmaceutico: Decimal,
) -> tuple[tuple[ReglaAdicionalConfig, ...], tuple[tuple[str, Decimal], ...]]:
    """Traduce los arts. 17–19 al formato genérico consumido por el motor."""
    bases_motor = {
        "basico_categoria": "basico_categoria",
        "basico_categoria_mas_antiguedad": "basico_categoria_mas_antiguedad",
        "basico_inicial_a": "referencia:INICIAL_A",
        "basico_inicial_a_mas_antiguedad": "referencia_mas_antiguedad:INICIAL_A",
        "basico_inicial_b_mas_antiguedad": "referencia_mas_antiguedad:INICIAL_B",
        "basico_farmaceutico_mas_antiguedad": "referencia_mas_antiguedad:FARMACEUTICO",
    }
    requieren_cantidad = {"NOCTURNO_VOLUNTARIO", "IDIOMA"}
    reglas = tuple(
        ReglaAdicionalConfig(
            codigo=r.codigo,
            descripcion=r.descripcion,
            porcentaje=r.porcentaje,
            base=bases_motor[r.base],
            articulo=r.articulo,
            requiere_cantidad=r.codigo in requieren_cantidad,
            modo_calculo=(
                "proporcion_periodo" if r.codigo == "NOCTURNO_VOLUNTARIO"
                else "remanente_fondo" if r.codigo == "FALLA_CAJA"
                else "multiplicador"
            ),
            clave_cantidad_base=(
                "HORAS_TOTALES_PERIODO" if r.codigo == "NOCTURNO_VOLUNTARIO"
                else None
            ),
        )
        for r in REGLAS_ADICIONALES_FARMACIA
    )
    referencias = (
        ("INICIAL_A", Decimal(basico_inicial_a)),
        ("INICIAL_B", Decimal(basico_inicial_b)),
        ("FARMACEUTICO", Decimal(basico_farmaceutico)),
    )
    return reglas, referencias
