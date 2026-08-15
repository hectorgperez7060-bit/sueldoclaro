from decimal import Decimal

import pytest

from domain.entities.farmacia_414_05 import (
    CATEGORIAS_FARMACIA,
    REGLAS_ADICIONALES_FARMACIA,
    aplica_ambito_farmacia,
    categoria_farmacia_canonica,
    dias_vacaciones_farmacia,
    resolver_jornada_farmacia,
)


def test_cct_tiene_las_seis_categorias_oficiales():
    assert len(CATEGORIAS_FARMACIA) == 6
    assert categoria_farmacia_canonica("empleado especializado de farmacia") == (
        "Empleado Especializado de Farmacia"
    )
    assert categoria_farmacia_canonica("administrativo") == (
        "Cajero, Perfumería y Administrativo"
    )
    with pytest.raises(ValueError, match="no contemplada"):
        categoria_farmacia_canonica("Vendedor inventado")


def test_ambito_no_se_extiende_por_suposicion():
    assert aplica_ambito_farmacia("Merlo")
    assert aplica_ambito_farmacia("José C. Paz")
    assert not aplica_ambito_farmacia("Córdoba")


@pytest.mark.parametrize("anios,dias", [(0, 17), (5, 17), (6, 26), (10, 26), (11, 35), (20, 35), (21, 44)])
def test_vacaciones_convencionales(anios, dias):
    assert dias_vacaciones_farmacia(anios) == dias


def test_jornadas_especiales_no_se_prorratean_como_parciales():
    assert resolver_jornada_farmacia(Decimal("45")).proporcion_salarial == Decimal("1")
    assert resolver_jornada_farmacia(Decimal("42"), nocturna=True).proporcion_salarial == Decimal("1")
    assert resolver_jornada_farmacia(Decimal("33"), insalubre=True).proporcion_salarial == Decimal("1")
    parcial = resolver_jornada_farmacia(Decimal("22.5"))
    assert parcial.proporcion_salarial == Decimal("0.5")
    assert not parcial.admite_horas_extra
    assert parcial.base_obra_social_jornada_completa


def test_jornada_ambigua_exige_revision_en_lugar_de_inventar():
    with pytest.raises(ValueError, match="encuadre documentado"):
        resolver_jornada_farmacia(Decimal("36"))


def test_adicionales_del_cct_quedan_en_reglas_separadas_y_auditables():
    codigos = {r.codigo for r in REGLAS_ADICIONALES_FARMACIA}
    assert {"DIRECCION_TECNICA", "ADICIONAL_CAJERO", "IDIOMA", "FALLA_CAJA"} <= codigos
    assert len(codigos) == len(REGLAS_ADICIONALES_FARMACIA)
    assert all(r.articulo and r.base and r.condicion for r in REGLAS_ADICIONALES_FARMACIA)
