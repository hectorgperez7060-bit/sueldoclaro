"""Value object CUIL con validación real por módulo 11.

Algoritmo AFIP/ARCA:
- 11 dígitos: PP-DDDDDDDD-V (prefijo, 8 dígitos, verificador).
- Prefijos válidos: 20, 23, 24, 27 (personas físicas) y 30, 33, 34 (personas
  jurídicas / casos especiales).
- Multiplicadores para los primeros 10 dígitos: [5,4,3,2,7,6,5,4,3,2].
- suma = Σ díg_i * mult_i ; resto = suma % 11 ; verificador = 11 - resto.
  Si verificador == 11 -> 0. Si verificador == 10 -> el número requiere cambio
  de prefijo y no es válido tal como está (se rechaza).
"""
from __future__ import annotations

from dataclasses import dataclass

MULTIPLICADORES = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
PREFIJOS_VALIDOS = {20, 23, 24, 27, 30, 33, 34}


def digito_verificador(diez_digitos: str) -> int:
    """Devuelve el DV esperado (0..9) o -1 si el número exige cambio de prefijo."""
    if len(diez_digitos) != 10 or not diez_digitos.isdigit():
        raise ValueError("Se esperan exactamente 10 dígitos numéricos")
    suma = sum(int(d) * m for d, m in zip(diez_digitos, MULTIPLICADORES))
    resto = suma % 11
    verificador = 11 - resto
    if verificador == 11:
        return 0
    if verificador == 10:
        return -1  # requiere prefijo alternativo; inválido tal cual
    return verificador


def es_cuil_valido(cuil: str) -> bool:
    limpio = cuil.replace("-", "").replace(" ", "")
    if len(limpio) != 11 or not limpio.isdigit():
        return False
    if int(limpio[:2]) not in PREFIJOS_VALIDOS:
        return False
    esperado = digito_verificador(limpio[:10])
    if esperado < 0:
        return False
    return esperado == int(limpio[10])


@dataclass(frozen=True)
class Cuil:
    """CUIL validado. Se normaliza a 11 dígitos sin guiones."""

    valor: str

    def __post_init__(self) -> None:
        limpio = self.valor.replace("-", "").replace(" ", "")
        if not es_cuil_valido(limpio):
            raise ValueError(f"CUIL inválido: {self.valor!r}")
        object.__setattr__(self, "valor", limpio)

    @property
    def prefijo(self) -> str:
        return self.valor[:2]

    def formateado(self) -> str:
        return f"{self.valor[:2]}-{self.valor[2:10]}-{self.valor[10]}"

    def __str__(self) -> str:
        return self.formateado()
