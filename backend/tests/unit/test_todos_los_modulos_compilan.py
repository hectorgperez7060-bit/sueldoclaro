"""Ningún archivo del backend puede llegar a producción sin compilar.

Existe por una caída real. El PR 62 escribió en main.py la línea

    return HTMLResponse(\\n            UI_HTML,\\n ... )

con barra-n literales en vez de saltos de línea, producto de una edición
automática mal hecha. Python no pudo importar el módulo, la función serverless
no arrancó y toda la aplicación devolvió 500 FUNCTION_INVOCATION_FAILED en cada
pantalla. Hubo que revertir el PR entero, y en el camino se perdió también la
mejora del menú que viajaba en el mismo lote.

Un error de sintaxis no se nota en una prueba de negocio: revienta al importar.
Por eso esta prueba no mira lógica, solo que todo el código compile.
"""
from __future__ import annotations

from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
MODULOS = sorted(SRC.rglob("*.py"))


def test_hay_modulos_para_revisar():
    assert len(MODULOS) > 20, "la búsqueda de módulos no encontró el código"


@pytest.mark.parametrize("ruta", MODULOS, ids=[str(m.relative_to(SRC)) for m in MODULOS])
def test_el_modulo_compila(ruta: Path):
    try:
        compile(ruta.read_text(encoding="utf-8"), str(ruta), "exec")
    except SyntaxError as exc:
        pytest.fail(f"{ruta.relative_to(SRC)} no compila: {exc}")


@pytest.mark.parametrize("ruta", MODULOS, ids=[str(m.relative_to(SRC)) for m in MODULOS])
def test_ninguna_linea_de_codigo_trae_barra_ene_literal(ruta: Path):
    """La firma exacta del incidente: '\\n' pegado fuera de una cadena.

    Una barra invertida seguida de 'n' en código Python es una continuación de
    línea inválida. Dentro de una cadena es legítima, así que sólo se miran las
    líneas que terminan el patrón con paréntesis o coma, que es como quedó la
    edición rota y como no aparece nunca en texto normal.
    """
    sospechosas = [
        (n, linea.strip())
        for n, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1)
        if "\\n " in linea and linea.rstrip().endswith((")", ",")) and '"""' not in linea
        and not linea.lstrip().startswith(("#", "'", '"'))
    ]
    assert not sospechosas, (
        f"{ruta.relative_to(SRC)} tiene barra-n literal en código: {sospechosas}"
    )
