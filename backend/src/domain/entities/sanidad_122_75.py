"""Reglas estructurales verificadas del CCT 122/75 (Clínicas y Sanatorios)."""
from __future__ import annotations


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
