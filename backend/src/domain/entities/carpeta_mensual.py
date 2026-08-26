"""Estados y huella inmutable de la carpeta mensual de liquidación."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal

from .boleta_sindical import agrupar_obligaciones_sindicales


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
TRANSICIONES_OBLIGACION = {
    "pendiente": {"generada"},
    "generada": {"pagada"},
    "pagada": {"verificada"},
    "verificada": set(),
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
        "obligaciones_sindicales": agrupar_obligaciones_sindicales(detalles),
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


def validar_transicion_obligacion(actual: str, nuevo: str, comprobante: str = "") -> None:
    if actual not in TRANSICIONES_OBLIGACION or nuevo not in TRANSICIONES_OBLIGACION:
        raise ValueError("Estado de obligación mensual inválido")
    if nuevo not in TRANSICIONES_OBLIGACION[actual]:
        raise ValueError(f"No se puede pasar la obligación de {actual} a {nuevo}")
    if nuevo in {"pagada", "verificada"} and not comprobante.strip():
        raise ValueError(f"El estado {nuevo} requiere comprobante")


def obligaciones_desde_contenido(contenido: dict) -> list[dict]:
    """Convierte las salidas calculadas en tareas pagables, sin recalcular importes."""
    salida = [{
        "tipo": "ARCA_F931", "cct_numero": None, "destino_pago": "ARCA",
        "codigo_boleta": "F931", "importe": None,
        "canal_pago": "Libro de Sueldos Digital / Declaración en Línea",
        "url_pago": "https://www.arca.gob.ar/",
        "fuente_pago": "RG 3781 y normativa SUSS vigente",
    }]
    for boleta in contenido.get("obligaciones_sindicales", []):
        salida.append({
            "tipo": "SINDICAL", "cct_numero": boleta.get("cct_numero") or None,
            "destino_pago": boleta["destino_pago"],
            "codigo_boleta": boleta["codigo_boleta"],
            "importe": Decimal(str(boleta["importe"])),
            "canal_pago": boleta.get("canal_pago") or "",
            "url_pago": boleta.get("url_pago") or "",
            "fuente_pago": boleta.get("fuente_pago") or "",
        })
    return salida


def faltantes_para_revision(contenido: dict, obligaciones: list[dict]) -> list[str]:
    """Lista breve y determinística de controles que impiden firmar la carpeta."""
    faltantes = []
    control = contenido.get("control_normativo", {})
    pendientes_reales = [
        p for p in control.get("pendientes", [])
        if p.get("codigo") != "APROBACION_CONTADOR_UOM"
    ]
    if pendientes_reales:
        faltantes.append("Existen reglas normativas o aprobaciones pendientes")
    if not obligaciones:
        faltantes.append("No se generaron obligaciones del período")
    if any(o.get("estado") != "verificada" for o in obligaciones):
        faltantes.append("Hay F.931, boletas o pagos sin verificar")
    return faltantes


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
