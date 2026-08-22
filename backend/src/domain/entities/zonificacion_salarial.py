"""Resolución general de zona salarial a partir de datos normativos."""
from __future__ import annotations

import unicodedata


def _normalizar(valor: str) -> str:
    texto = unicodedata.normalize("NFD", str(valor or ""))
    return " ".join(
        "".join(c for c in texto if unicodedata.category(c) != "Mn")
        .upper().replace(".", "").replace(",", "").split()
    )


def normalizar_provincia(valor: str) -> str:
    """Normaliza provincias y alias sin decidir una zona ni una vigencia."""
    buscada = _normalizar(valor)
    alias = {
        "CIUDAD AUTONOMA DE BUENOS AIRES": "CABA",
        "CAPITAL FEDERAL": "CABA",
        "TIERRA DEL FUEGO ANTARTIDA E ISLAS DEL ATLANTICO SUR": "TIERRA DEL FUEGO",
    }
    return alias.get(buscada, buscada)


def resolver_zona(configuracion: dict, provincia: str) -> str | None:
    """Devuelve el código de zona cuyo listado contiene la jurisdicción."""
    buscada = normalizar_provincia(provincia)
    if not buscada:
        return None
    for zona, jurisdicciones in (configuracion.get("zonas") or {}).items():
        normalizadas = {_normalizar(item) for item in jurisdicciones}
        if buscada in normalizadas:
            return str(zona)
    return None
