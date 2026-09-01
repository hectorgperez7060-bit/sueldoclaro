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
NOTA_PROVISORIA = "Escala publicada y documentada, pendiente de validación final"
MENSAJE_MOTOR_NO_HABILITADO = (
    "La escala está documentada, pero el motor todavía no está habilitado "
    "para su unidad y modalidad de liquidación"
)


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
    *,
    confirmado: bool = False,
) -> EvaluacionEscala:
    """Decide qué hacer con la escala vigente de un empleado en un período.

    Toda la vigencia (incluida la reutilización provisoria acotada) vive en los
    DATOS: ``vigente`` es la escala cuya vigencia cubre el período pedido.

    - sin escala vigente: BLOQUEADA con el mensaje normativo. Nunca se reutiliza
      una escala anterior por fuera de su vigencia declarada.
    - escala vigente marcada ``provisoria``: se ofrece PROVISORIA y exige
      confirmación expresa antes de liquidar.
    - escala vigente normal: se liquida con ella (comportamiento intacto para
      cualquier convenio con su escala del período cargada).
    """
    if vigente is None:
        return EvaluacionEscala("bloqueada", None, False, False, MENSAJE_SIN_ESCALA, "")
    # Política general: una escala provisoria con fuente y vigencia explícitas
    # puede usarse con confirmación, aunque no esté habilitada como definitiva.
    # El indicador habilitada_liquidacion reserva la publicación final; no debe
    # impedir el trabajo mensual mientras la homologación administrativa demora.
    if getattr(vigente, "provisoria", False) and (vigente.fuente or "").strip():
        return EvaluacionEscala(
            "provisoria", vigente, True, not confirmado, "", NOTA_PROVISORIA
        )
    if not getattr(vigente, "habilitada_liquidacion", True):
        return EvaluacionEscala(
            "bloqueada", None, False, False, MENSAJE_MOTOR_NO_HABILITADO, ""
        )
    if not vigente.is_verified:
        return EvaluacionEscala(
            "bloqueada", None, False, False, MENSAJE_SIN_ESCALA, ""
        )
    return EvaluacionEscala("vigente", vigente, False, False, "", "")
