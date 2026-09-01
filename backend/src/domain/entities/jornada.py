"""Jornada completa declarada por cada convenio (dominio puro).

El motor prorratea el básico por ``proporcion_jornada``. Esa proporción sale de
comparar las horas que trabaja la persona contra las horas de jornada completa
del convenio que la encuadra, y esas horas están declaradas en la regla
estructural ``JORNADA`` de cada CCT. No son 48 para todos: Comercio 130/75 tiene
48, Farmacia 414/05 tiene 45 y los dos convenios de SOECRA tienen 44.

Tomar 48 como divisor universal le prorratea el sueldo a un trabajador de
jornada completa de cualquier convenio que no sea Comercio. Este módulo existe
para que ese número salga siempre de la norma cargada y de un solo lugar.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Mapping, Optional

# Las migraciones históricas nombraron esta misma magnitud de cuatro maneras
# distintas. Se aceptan todos los alias en orden de preferencia en vez de
# reescribir migraciones ya aplicadas; las cargas nuevas deberían usar
# ``horas_semanales_convencionales``.
CLAVES_HORAS_SEMANALES = (
    "horas_semanales_convencionales",   # CCT 749/18
    "completa_horas_semanales",         # CCT 130/75
    "completa_horas",                   # CCT 414/05
    "horas_semanales",                  # CCT 761/19 y posteriores
)

# Sólo se usa cuando el convenio no declara su jornada. No es un supuesto sobre
# la norma: es el máximo legal de la Ley 11.544, y quien lo reciba tiene que
# saber que el dato faltaba.
HORAS_TOPE_LEY_11544 = Decimal("48")


def horas_jornada_completa(configuracion: Optional[Mapping]) -> Optional[Decimal]:
    """Horas semanales de jornada completa declaradas por la regla JORNADA."""
    for clave in CLAVES_HORAS_SEMANALES:
        valor = (configuracion or {}).get(clave)
        if valor is None:
            continue
        try:
            horas = Decimal(str(valor))
        except (ArithmeticError, TypeError, ValueError):
            continue
        if horas > 0:
            return horas
    return None


def horas_desde_reglas(reglas: Iterable) -> Optional[Decimal]:
    """Busca la regla ``JORNADA`` entre las reglas estructurales de un convenio."""
    for regla in reglas or ():
        codigo = getattr(regla, "codigo", None) or (
            regla.get("codigo") if isinstance(regla, Mapping) else None)
        if codigo != "JORNADA":
            continue
        configuracion = getattr(regla, "configuracion", None)
        if configuracion is None and isinstance(regla, Mapping):
            configuracion = regla.get("configuracion")
        horas = horas_jornada_completa(configuracion)
        if horas is not None:
            return horas
    return None


def proporcion_jornada(
    horas_trabajadas: Decimal | str | int | float,
    horas_convenio: Optional[Decimal],
) -> Decimal:
    """Proporción de jornada, siempre relativa a la jornada del convenio.

    Trabajar la jornada completa del convenio da 1 exacto, sea de 44, 45 o 48
    horas. Declarar más horas que la jornada completa no es jornada parcial: es
    un error de carga o son horas extra, y en cualquier caso se rechaza.
    """
    horas = Decimal(str(horas_trabajadas))
    completa = Decimal(str(horas_convenio)) if horas_convenio else HORAS_TOPE_LEY_11544
    if completa <= 0:
        raise ValueError("La jornada completa del convenio debe ser mayor que cero")
    if horas <= 0:
        raise ValueError("Las horas semanales deben ser mayores que cero")
    if horas > completa:
        raise ValueError(
            f"{horas} horas semanales superan la jornada completa del convenio "
            f"({completa}). Las horas por encima de la jornada son horas extra y "
            f"se cargan como novedad del mes, no como jornada."
        )
    return horas / completa
