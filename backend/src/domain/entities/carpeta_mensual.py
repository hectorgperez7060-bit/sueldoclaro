"""Estados y huella inmutable de la carpeta mensual de liquidación."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal


ESTADOS_CARPETA = (
    "borrador", "calculada", "revisada", "presentada", "aceptada", "pagada",
)
TRANSICIONES = {
    "borrador": {"calculada"},
    "calculada": {"revisada", "borrador"},
    "revisada": {"presentada", "borrador"},
    "presentada": {"aceptada", "revisada"},
    "aceptada": {"pagada"},
    "pagada": set(),
}


def huella_carpeta(contenido: dict) -> str:
    canonico = json.dumps(
        contenido, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(canonico).hexdigest()


def construir_contenido_carpeta(
    *, periodo: str, tipo: str, liquidacion_id: str,
    detalles: list[dict], snapshot: dict, reglas_pendientes: list[dict],
) -> dict:
    """Construye una fotografía canónica usando el resultado ya liquidado."""
    bruto = sum((Decimal(str(d["bruto"])) for d in detalles), Decimal("0"))
    deducciones = sum(
        (Decimal(str(d["total_deducciones"])) for d in detalles), Decimal("0")
    )
    neto = sum((Decimal(str(d["neto"])) for d in detalles), Decimal("0"))
    conceptos = sum((len(d.get("conceptos", [])) for d in detalles), 0)
    return {
        "periodo": periodo,
        "tipo": tipo,
        "liquidacion_id": liquidacion_id,
        "cantidad_empleados": len(detalles),
        "cantidad_conceptos": conceptos,
        "totales": {
            "bruto": str(bruto.quantize(Decimal("0.01"))),
            "deducciones": str(deducciones.quantize(Decimal("0.01"))),
            "neto": str(neto.quantize(Decimal("0.01"))),
        },
        "detalles": detalles,
        "snapshot_parametros": snapshot,
        "control_normativo": {
            "apto_produccion": not reglas_pendientes,
            "pendientes": reglas_pendientes,
        },
    }


def validar_transicion(actual: str, nuevo: str, comprobante_externo: str = "") -> None:
    if actual not in ESTADOS_CARPETA or nuevo not in ESTADOS_CARPETA:
        raise ValueError("Estado de carpeta mensual inválido")
    if nuevo not in TRANSICIONES[actual]:
        raise ValueError(f"No se puede pasar de {actual} a {nuevo}")
    if nuevo in {"presentada", "aceptada", "pagada"} and not comprobante_externo.strip():
        raise ValueError(f"El estado {nuevo} requiere comprobante externo")


@dataclass(frozen=True)
class PerfilContador:
    nombre_apellido: str
    cuit: str
    matricula: str
    jurisdiccion: str
    consejo_profesional: str
    matricula_vigente: bool
    constancia_url: str

    def puede_revisar(self) -> bool:
        return all((
            self.nombre_apellido.strip(), self.cuit.strip(), self.matricula.strip(),
            self.jurisdiccion.strip(), self.consejo_profesional.strip(),
            self.constancia_url.strip(), self.matricula_vigente,
        ))
