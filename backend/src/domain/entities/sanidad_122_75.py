"""Reglas estructurales verificadas del CCT 122/75 (Clínicas y Sanatorios)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from domain.payroll_engine.config import ReglaAdicionalConfig


CCT_SANIDAD = "122/75"

CATEGORIAS_SANIDAD = (
    "Profesionales Bioquímicos, Nutricionistas, Farmacéuticos y Kinesiólogos",
    "Obstétricas e instrumentadoras", "Cabos/as de cirugía",
    "Cabos/as de Piso o Pabellón",
    "Enfermeros/as de Cirugía y personal de esterilización",
    "Auxiliar Técnico de Rayos X", "Pedicuros y Masajistas",
    "Enfermero/a de Piso o Consultorios Externos",
    "Personal Especializado en Terapia Intensiva, Clímax, Unidad Coronaria, Nursery, Foniatría y Riñón artificial",
    "Personal destinado a la atención de enfermos mentales y nerviosos",
    "Personal Técnico de Hemoterapia, Fisioterapia, Anatomía Patológica y Laboratorio",
    "Ayudante de radiología, Fisioterapia, Hemoterapia, Anatomía Patológica y Laboratorio",
    "Mucamas de Cirugía o sin atingencia con la atención de enfermos",
    "Asistente Geriátrica", "Asistente de Comedores con atención al público",
    "Camilleros y fotógrafos", "Personal de Lavadero y ropería",
    "Mucamas de Piso, Consultorios Externos y Geriátricos",
    "Mantenimiento - Oficiales", "Mantenimiento - Medio oficiales",
    "Mantenimiento - Ascensoristas, Porteros y Serenos",
    "Mantenimiento - Jardineros", "Mantenimiento - Peones en general",
    "Cocina - Primer cocinero, repostero o fiambrero",
    "Cocina - Segundo cocinero, repostero o fiambrero",
    "Cocina - Cocinero/a de Establecimientos Geriátricos",
    "Cocina - Encargado/a de Office, cafetero o Jefe de despacho",
    "Cocina - Ayudante de cocina y cacerolero",
    "Cocina - Peones de cocina en general", "Administrativo de Primera",
    "Administrativo de Segunda", "Administrativo de Tercera", "Cadete",
    "Geriátricos - Auxiliar de Enfermería",
)


def _normalizar(texto: str) -> str:
    tabla = str.maketrans("ÁÉÍÓÚÜÑ", "AEIOUUN")
    return " ".join(str(texto or "").upper().translate(tabla).replace(".", "").split())


def categoria_sanidad_canonica(categoria: str) -> str:
    ingresada = _normalizar(categoria)
    for canonica in CATEGORIAS_SANIDAD:
        if _normalizar(canonica) == ingresada:
            return canonica
    raise ValueError(f"Categoría no contemplada por el CCT 122/75: {categoria or '(vacía)'}")


def antiguedad_sanidad(anios: int) -> int:
    """Art. 10: dos puntos porcentuales por cada año desde el primero."""
    if anios < 0:
        raise ValueError("La antigüedad no puede ser negativa")
    return anios * 2


@dataclass(frozen=True)
class ReglaEstructuralSanidad:
    codigo: str
    descripcion: str
    articulo: str
    automatizable: bool
    dato_requerido: str


# Catálogo estructural del CCT. Las reglas no automatizables no se pierden:
# quedan expresamente identificadas para la siguiente capa, sin convertir una
# condición organizativa en una fórmula supuesta.
REGLAS_ESTRUCTURALES_SANIDAD = (
    ReglaEstructuralSanidad("FONDO_CIRUGIA_PARTO", "Distribución por cirugía mayor o parto", "9", False, "cantidad de actos y personal participante"),
    ReglaEstructuralSanidad("TERAPIA_8H", "Enfermería en terapia, clímax, coronaria, nursery o riñón artificial (8 h)", "9", True, "asignación efectiva al sector"),
    ReglaEstructuralSanidad("MUCAMA_SECTOR_ESPECIAL", "Mucama en sector especial", "9", True, "asignación efectiva al sector"),
    ReglaEstructuralSanidad("MENTAL_ENFERMERIA", "Atención de enfermos mentales y nerviosos con tareas de enfermería", "9", True, "tarea realizada"),
    ReglaEstructuralSanidad("MENTAL_TERAPIA", "Terapia, vigilancia, aislamiento o sector intensivo de salud mental", "9", True, "tarea realizada"),
    ReglaEstructuralSanidad("MENTAL_OTRAS_TAREAS", "Otras tareas en área de salud mental", "9", True, "tarea realizada"),
    ReglaEstructuralSanidad("ELECTRICISTA_TITULO", "Electricista con título habilitante", "9", True, "título y tarea"),
    ReglaEstructuralSanidad("NOCTURNIDAD", "Trabajo entre las 22:00 y las 06:00", "9", True, "horas nocturnas y horas totales del período"),
    ReglaEstructuralSanidad("OPERADOR_MAQUINAS_CONTABLES", "Operador de máquinas contables", "9", True, "tarea realizada"),
    ReglaEstructuralSanidad("LAB_AREA_CERRADA", "Laboratorio en área cerrada", "9", True, "área y tarea realizadas"),
    ReglaEstructuralSanidad("RAYOS_LAB_48H", "Opción de jornada de 48 horas en rayos o laboratorio", "14", True, "régimen de jornada documentado"),
    ReglaEstructuralSanidad("TAREA_SUPERIOR", "Tarea de categoría superior", "9", False, "categoría, horas y mínimo convencional"),
    ReglaEstructuralSanidad("TAREA_NO_HABITUAL", "Tarea no habitual", "9", False, "horas y mínimo convencional"),
    ReglaEstructuralSanidad("TAREA_ADICIONAL", "Tarea adicional de otro puesto", "9", False, "horas, puesto y exclusiones"),
    ReglaEstructuralSanidad("CAMAS_PACIENTES_EXCEDENTES", "Recargo por camas, pacientes o gerontes excedentes", "7", False, "dotación, turno, sector y excedente"),
    ReglaEstructuralSanidad("ZONA_DESFAVORABLE", "Zona desfavorable", "13", False, "domicilio laboral y base convencional completa"),
    ReglaEstructuralSanidad("LICENCIA_ESPECIAL", "Licencia adicional por exposición o sector", "22", False, "sector y tiempo anual de exposición"),
    ReglaEstructuralSanidad("SALA_MATERNAL", "Reintegro por sala maternal", "26", False, "obligación legal, disponibilidad e hijos"),
    ReglaEstructuralSanidad("LAVADO_ROPA", "Reintegro por lavado y planchado de ropa", "30", False, "acuerdo local y prestación sustituida"),
)


def configurar_adicionales_sanidad() -> tuple[ReglaAdicionalConfig, ...]:
    """Reglas mensuales que pueden liquidarse sin inferir datos faltantes."""
    sector = "SECTOR_ESPECIAL_SANIDAD"
    return (
        ReglaAdicionalConfig("TERAPIA_8H", "Adicional sector especial (8 h)", Decimal("0.20"), "basico_categoria", "9", grupo_exclusion=sector),
        ReglaAdicionalConfig("MUCAMA_SECTOR_ESPECIAL", "Mucama en sector especial", Decimal("0.10"), "basico_categoria", "9", grupo_exclusion=sector),
        ReglaAdicionalConfig("MENTAL_ENFERMERIA", "Salud mental con tareas de enfermería", Decimal("0.10"), "basico_categoria", "9", grupo_exclusion=sector),
        ReglaAdicionalConfig("MENTAL_TERAPIA", "Salud mental: terapia, vigilancia o aislamiento", Decimal("0.20"), "basico_categoria", "9", grupo_exclusion=sector),
        ReglaAdicionalConfig("MENTAL_OTRAS_TAREAS", "Otras tareas en área de salud mental", Decimal("0.10"), "basico_categoria", "9", grupo_exclusion=sector),
        ReglaAdicionalConfig("ELECTRICISTA_TITULO", "Electricista con título habilitante", Decimal("0.20"), "basico_categoria", "9"),
        ReglaAdicionalConfig("NOCTURNIDAD", "Horas trabajadas de 22:00 a 06:00", Decimal("0.10"), "basico_categoria", "9", True, "proporcion_periodo", "HORAS_TOTALES_PERIODO"),
        ReglaAdicionalConfig("OPERADOR_MAQUINAS_CONTABLES", "Operador de máquinas contables", Decimal("0.20"), "basico_categoria", "9"),
        ReglaAdicionalConfig("LAB_AREA_CERRADA", "Laboratorio en área cerrada", Decimal("0.30"), "basico_categoria", "9"),
        ReglaAdicionalConfig("RAYOS_LAB_48H", "Jornada de 48 h en rayos o laboratorio", Decimal("0.33"), "basico_categoria", "14"),
    )


def reglas_pendientes_revision_sanidad() -> tuple[ReglaEstructuralSanidad, ...]:
    return tuple(regla for regla in REGLAS_ESTRUCTURALES_SANIDAD if not regla.automatizable)
