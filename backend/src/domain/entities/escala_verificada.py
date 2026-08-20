"""Regla GENERAL de disponibilidad de escala salarial verificada.

No depende de ningún convenio ni contiene importes: recibe las escalas ya
resueltas (desde la base) y decide si una liquidación puede hacerse, si debe
reutilizar provisoriamente la última escala verificada (con confirmación) o si
debe bloquearse por falta de escala para el período. Nunca estima ni pone cero.

Aplica a cualquier CCT/categoría/período: la lógica de bloqueo no está escrita
para un convenio en particular.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from domain.entities.parametros import EscalaSalarial


MENSAJE_SIN_ESCALA = "Sin escala salarial verificada para el período"
NOTA_PROVISORIA = "Valor provisorio: última escala verificada disponible"


@dataclass(frozen=True)
class EvaluacionEscala:
    estado: str                       # "vigente" | "provisoria" | "bloqueada"
    escala: Optional[EscalaSalarial]  # escala a usar para liquidar (o None)
    provisorio: bool
    requiere_confirmacion: bool
    motivo: str                       # mensaje de bloqueo (si aplica)
    nota: str                         # nota de provisorio (si aplica)

    @property
    def puede_liquidar(self) -> bool:
        if self.estado == "vigente":
            return True
        if self.estado == "provisoria":
            return not self.requiere_confirmacion
        return False


def evaluar_escala(
    vigente: Optional[EscalaSalarial],
    previa_verificada: Optional[EscalaSalarial],
    *,
    confirmado: bool = False,
) -> EvaluacionEscala:
    """Decide qué hacer con la escala de un empleado en un período.

    - vigente presente: se liquida con ella (comportamiento actual intacto para
      cualquier convenio que tenga su escala del período cargada).
    - sin vigente pero con una escala verificada anterior: se ofrece PROVISORIA,
      reutilizando la última verificada, y exige confirmación expresa.
    - sin vigente ni anterior verificada: BLOQUEADA, con el mensaje normativo.
    """
    if vigente is not None:
        return EvaluacionEscala("vigente", vigente, False, False, "", "")
    if previa_verificada is not None:
        return EvaluacionEscala(
            "provisoria", previa_verificada, True, not confirmado, "", NOTA_PROVISORIA
        )
    return EvaluacionEscala("bloqueada", None, False, False, MENSAJE_SIN_ESCALA, "")
