"""Batería de CUILes válidos e inválidos (módulo 11)."""
import pytest

from domain.value_objects.cuil import Cuil, digito_verificador, es_cuil_valido

CUILES_VALIDOS = [
    "20123456786",
    "27123456780",
    "30123456781",
    "20-12345678-6",  # con guiones
]

CUILES_INVALIDOS = [
    "20123456785",   # dígito verificador incorrecto
    "10123456789",   # prefijo inexistente (10)
    "2012345678",    # 10 dígitos (corto)
    "201234567861",  # 12 dígitos (largo)
    "2012345678X",   # carácter no numérico
    "",              # vacío
]


@pytest.mark.parametrize("cuil", CUILES_VALIDOS)
def test_cuiles_validos(cuil):
    assert es_cuil_valido(cuil)
    Cuil(cuil)  # no debe lanzar


@pytest.mark.parametrize("cuil", CUILES_INVALIDOS)
def test_cuiles_invalidos(cuil):
    assert not es_cuil_valido(cuil)
    with pytest.raises(ValueError):
        Cuil(cuil)


def test_digito_verificador_conocido():
    # 20-12345678 -> DV 6
    assert digito_verificador("2012345678") == 6


def test_normalizacion_y_formato():
    c = Cuil("20-12345678-6")
    assert c.valor == "20123456786"
    assert c.formateado() == "20-12345678-6"
    assert c.prefijo == "20"
