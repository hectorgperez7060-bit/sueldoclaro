from decimal import Decimal

import pytest
from pydantic import ValidationError

from application.dto.schemas import NovedadMensualIn, NovedadMensualUpdate
from main import create_app


EMPLEADO_ID = "12345678-1234-5678-1234-567812345678"


def test_dto_novedad_valido():
    dto = NovedadMensualIn(
        empleado_id=EMPLEADO_ID,
        periodo="2026-08",
        dias_trabajados=20,
        horas_extra_50=Decimal("2.5"),
    )
    assert dto.datos_dominio().periodo == "2026-08"


def test_dto_rechaza_empleado_invalido():
    with pytest.raises(ValidationError, match="empleado inválido"):
        NovedadMensualIn(empleado_id="cualquier-cosa", periodo="2026-08")


def test_dto_update_reutiliza_validacion_de_dominio():
    with pytest.raises(ValidationError, match="entre 0 y 28"):
        NovedadMensualUpdate(periodo="2026-02", dias_trabajados=29)


def test_router_novedades_esta_registrado_con_crud_completo():
    rutas = create_app().openapi()["paths"]
    assert {"get", "post"} <= set(rutas["/novedades"])
    assert {"get", "put", "delete"} <= set(rutas["/novedades/{novedad_id}"])
