"""Contrato declarativo para incorporar convenios sin tocar el motor a mano."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


ESTADOS_FUENTE = {
    "VERIFICADA", "HOMOLOGADO_NO_PUBLICADO", "PUBLICADA_POR_PARTE_SIGNATARIA",
    "PENDIENTE_DOCUMENTACION",
}


@dataclass(frozen=True)
class DiagnosticoPaquete:
    errores: tuple[str, ...]
    advertencias: tuple[str, ...]
    resumen: dict[str, Any]

    @property
    def valido(self) -> bool:
        return not self.errores


def validar_paquete(datos: dict[str, Any]) -> DiagnosticoPaquete:
    """Valida integridad y trazabilidad; jamás completa datos faltantes."""
    errores: list[str] = []
    advertencias: list[str] = []
    identidad = datos.get("identidad") or {}
    estructura = datos.get("estructura") or {}
    periodos = datos.get("periodos") or []
    motor = datos.get("motor") or {}
    numero = str(identidad.get("numero", "")).strip()
    version = str(datos.get("version_paquete", "")).strip()
    if not numero:
        errores.append("Falta identidad.numero")
    if not version:
        errores.append("Falta version_paquete")

    categorias = estructura.get("categorias") or []
    reglas = estructura.get("reglas") or []
    _duplicados(categorias, "codigo", "categoría", errores)
    _duplicados(reglas, "codigo", "regla", errores)
    nombres = {str(c.get("nombre", "")).strip() for c in categorias}
    for tipo, filas in (("categoría", categorias), ("regla", reglas)):
        for fila in filas:
            _trazabilidad(fila, tipo, errores)

    total_escalas = total_parametros = 0
    for periodo in periodos:
        etiqueta = str(periodo.get("periodo", ""))
        try:
            anio, mes = map(int, etiqueta.split("-"))
            date(anio, mes, 1)
        except (ValueError, TypeError):
            errores.append(f"Período inválido: {etiqueta or '(vacío)'}")
        escalas = periodo.get("escalas") or []
        parametros = periodo.get("parametros") or []
        total_escalas += len(escalas)
        total_parametros += len(parametros)
        claves: set[tuple[str, str]] = set()
        for escala in escalas:
            clave = (str(escala.get("categoria", "")), str(escala.get("zona", "")))
            if clave in claves:
                errores.append(f"Escala duplicada en {etiqueta}: {clave[0]} / {clave[1]}")
            claves.add(clave)
            if clave[0] not in nombres:
                errores.append(f"Escala {etiqueta} usa categoría desconocida: {clave[0]}")
            _numero(escala.get("basico"), f"básico {etiqueta} {clave[0]}", errores)
            _trazabilidad(escala, f"escala {etiqueta} {clave[0]}", errores)
        for parametro in parametros:
            _numero(parametro.get("valor"), f"parámetro {parametro.get('codigo', '')}", errores)
            _trazabilidad(parametro, f"parámetro {parametro.get('codigo', '')}", errores)

        zonas = estructura.get("zonas") or [""]
        esperadas = len(categorias) * len(zonas)
        if periodo.get("matriz_completa") and len(escalas) != esperadas:
            errores.append(
                f"{etiqueta}: matriz declarada completa pero hay {len(escalas)}/{esperadas} escalas"
            )

    if motor.get("estado") == "PRODUCTIVO":
        if not periodos:
            errores.append("Motor productivo sin períodos")
        if not motor.get("pruebas_regresion"):
            errores.append("Motor productivo sin pruebas de regresión declaradas")
        if any(not p.get("matriz_completa") for p in periodos):
            errores.append("Motor productivo con una matriz salarial incompleta")
        items = [*categorias, *reglas]
        for periodo in periodos:
            items.extend(periodo.get("escalas") or [])
            items.extend(periodo.get("parametros") or [])
        if any(not item.get("verificado") or not str(item.get("fuente", "")).strip() for item in items):
            errores.append("Motor productivo contiene datos no verificados o sin fuente")
        if any(not escala.get("habilitada") for p in periodos for escala in (p.get("escalas") or [])):
            errores.append("Motor productivo contiene escalas no habilitadas para liquidación")
    elif motor.get("estado") not in {"BLOQUEADO", "VISTA_PREVIA", "PRODUCTIVO"}:
        errores.append("motor.estado debe ser BLOQUEADO, VISTA_PREVIA o PRODUCTIVO")

    if not periodos:
        advertencias.append("Paquete estructural sin valores por período")
    return DiagnosticoPaquete(
        tuple(errores), tuple(advertencias),
        {"cct": numero, "version": version, "categorias": len(categorias),
         "reglas": len(reglas), "periodos": len(periodos), "escalas": total_escalas,
         "parametros": total_parametros, "motor": motor.get("estado", "")},
    )


def _duplicados(filas: list[dict], campo: str, etiqueta: str, errores: list[str]) -> None:
    valores = [str(f.get(campo, "")).strip() for f in filas]
    for valor in sorted({v for v in valores if valores.count(v) > 1}):
        errores.append(f"Código de {etiqueta} duplicado: {valor}")
    if any(not v for v in valores):
        errores.append(f"Hay una {etiqueta} sin {campo}")


def _trazabilidad(fila: dict, etiqueta: str, errores: list[str]) -> None:
    estado = str(fila.get("estado_fuente", "PENDIENTE_DOCUMENTACION"))
    if estado not in ESTADOS_FUENTE:
        errores.append(f"Estado de fuente inválido en {etiqueta}: {estado}")
    if fila.get("verificado") and not str(fila.get("fuente", "")).strip():
        errores.append(f"{etiqueta} figura verificada pero no tiene fuente")


def _numero(valor: Any, etiqueta: str, errores: list[str]) -> None:
    try:
        if Decimal(str(valor)) < 0:
            raise InvalidOperation
    except (InvalidOperation, ValueError, TypeError):
        errores.append(f"Valor numérico inválido en {etiqueta}")
