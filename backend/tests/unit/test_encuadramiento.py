import pytest

from domain.entities.encuadramiento import (
    resolver_encuadramiento,
    validar_filas_encuadramiento,
)


CATALOGO = {
    "130/75": {"Administrativo A", "Maestranza A"},
    "414/05": {"Empleado Especializado de Farmacia"},
    "40/89": set(),
}


def test_resuelve_categoria_sin_perder_nombre_oficial():
    assert resolver_encuadramiento(" 130/75 ", "administrativo a", CATALOGO) == (
        "130/75", "Administrativo A"
    )


def test_rechaza_convenio_inactivo_o_inexistente():
    with pytest.raises(ValueError, match="no está activo"):
        resolver_encuadramiento("999/99", "Categoría", CATALOGO)


def test_rechaza_categoria_de_otro_convenio():
    with pytest.raises(ValueError, match="no pertenece"):
        resolver_encuadramiento("130/75", "Empleado Especializado de Farmacia", CATALOGO)


def test_rechaza_convenio_sin_categorias_cargadas():
    with pytest.raises(ValueError, match="no tiene categorías"):
        resolver_encuadramiento("40/89", "Chofer", CATALOGO)


def test_excel_separa_fila_invalida_y_canoniza_la_valida():
    filas = [
        {"fila": 2, "nombre": "Ana", "apellido": "A", "cuil": "1",
         "cct_numero": "130/75", "categoria": "administrativo a"},
        {"fila": 3, "nombre": "Beto", "apellido": "B", "cuil": "2",
         "cct_numero": "130/75", "categoria": "Farmacia"},
    ]
    validas, errores = validar_filas_encuadramiento(filas, CATALOGO)
    assert validas[0]["categoria"] == "Administrativo A"
    assert errores == [{
        "fila": 3, "nombre": "B, Beto", "cuil": "2",
        "errores": ["La categoría Farmacia no pertenece al convenio 130/75"],
    }]
