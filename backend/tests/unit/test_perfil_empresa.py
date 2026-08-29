import pytest

from domain.entities.perfil_empresa import resolver_regimen_contribucion


@pytest.mark.parametrize("sector", ["COMERCIO", "SERVICIOS", "INDUSTRIA", "CONSTRUCCION"])
def test_certificado_mipyme_vigente_resuelve_18(sector):
    regimen, fundamento = resolver_regimen_contribucion(
        sector, "CERTIFICADO_VIGENTE"
    )
    assert regimen == "PRIVADO_18"
    assert fundamento


@pytest.mark.parametrize("sector", ["COMERCIO", "SERVICIOS"])
def test_gran_comercio_o_servicios_resuelve_204(sector):
    regimen, fundamento = resolver_regimen_contribucion(
        sector, "SUPERA_LIMITES"
    )
    assert regimen == "SERVICIOS_COMERCIO_204"
    assert fundamento


def test_situacion_no_comprobada_no_inventa_porcentaje():
    assert resolver_regimen_contribucion(
        "COMERCIO", "PENDIENTE"
    ) == ("PENDIENTE", "")
