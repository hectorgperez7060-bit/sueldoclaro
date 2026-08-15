"""Validación pura del encuadramiento convencional de un empleado."""
from __future__ import annotations


def resolver_encuadramiento(
    cct_numero: str,
    categoria: str,
    catalogo: dict[str, set[str]],
) -> tuple[str, str]:
    """Devuelve CCT/categoría canónicos o rechaza una combinación inexistente."""
    cct = str(cct_numero or "").strip()
    categoria_ingresada = str(categoria or "").strip()

    if cct not in catalogo:
        raise ValueError(f"El convenio {cct or '(vacío)'} no está activo en el sistema")

    categorias = catalogo[cct]
    if not categorias:
        raise ValueError(f"El convenio {cct} todavía no tiene categorías salariales cargadas")

    buscada = categoria_ingresada.casefold()
    for canonica in sorted(categorias):
        if canonica.strip().casefold() == buscada:
            return cct, canonica

    raise ValueError(
        f"La categoría {categoria_ingresada or '(vacía)'} no pertenece al convenio {cct}"
    )


def validar_filas_encuadramiento(
    filas: list[dict],
    catalogo: dict[str, set[str]],
) -> tuple[list[dict], list[dict]]:
    """Separa filas válidas y errores conservando el número de fila del Excel."""
    validas: list[dict] = []
    errores: list[dict] = []
    for fila in filas:
        try:
            cct, categoria = resolver_encuadramiento(
                fila.get("cct_numero", ""), fila.get("categoria", ""), catalogo
            )
        except ValueError as exc:
            errores.append({
                "fila": fila.get("fila"),
                "nombre": f"{fila.get('apellido', '')}, {fila.get('nombre', '')}".strip(", "),
                "cuil": fila.get("cuil", ""),
                "errores": [str(exc)],
            })
            continue
        item = dict(fila)
        item["cct_numero"] = cct
        item["categoria"] = categoria
        validas.append(item)
    return validas, errores
