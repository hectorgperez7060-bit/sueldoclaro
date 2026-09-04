"""El CUIT de la empresa vale tanto como el CUIL del trabajador.

Va impreso en el recibo que firma la persona y en el archivo que se le presenta
a ARCA. Antes solo se controlaba el largo, así que uno con un dígito mal pasaba
sin que nadie lo notara hasta que ARCA rechazaba la presentación.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from application.dto.schemas import EmpresaIn, RegistroEstudio, validar_cuit_empresa


CUIT_VALIDO = "30710000006"


def test_un_cuit_con_un_digito_mal_se_rechaza():
    # Este es el CUIT que salió impreso en un recibo real: no verifica.
    with pytest.raises(ValueError, match="dígito de control"):
        validar_cuit_empresa("23223337949")


def test_se_guarda_normalizado_sin_guiones():
    assert validar_cuit_empresa("30-71000000-6") == CUIT_VALIDO
    assert validar_cuit_empresa(" 30 71000000 6 ") == CUIT_VALIDO


def test_el_alta_de_empresa_lo_valida():
    with pytest.raises(ValidationError):
        EmpresaIn(razon_social="La Obra SA", cuit="23223337949")
    empresa = EmpresaIn(razon_social="La Obra SA", cuit="30-71000000-6")
    assert empresa.cuit == CUIT_VALIDO


def test_el_registro_de_la_cuenta_lo_valida():
    with pytest.raises(ValidationError):
        RegistroEstudio(
            razon_social="Estudio", cuit="23223337949",
            email="alguien@ejemplo.com", password="unaclavelarga",
        )
    cuenta = RegistroEstudio(
        razon_social="Estudio", cuit=CUIT_VALIDO,
        email="alguien@ejemplo.com", password="unaclavelarga",
    )
    assert cuenta.cuit == CUIT_VALIDO
