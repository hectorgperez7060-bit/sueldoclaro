from decimal import Decimal

import pytest

from application.dto.schemas import NovedadMensualIn
from domain.entities.novedad import DatosNovedadMensual
from infrastructure.database.models import NovedadMensual


def test_novedad_persiste_adicionales_y_cantidades_json():
    datos = DatosNovedadMensual(
        periodo="2026-08",
        adicionales_convencionales=("TITULO_SECUNDARIO", "IDIOMA"),
        cantidades_adicionales=(("IDIOMA", Decimal("2")),),
    ).para_persistir()
    assert datos["adicionales_convencionales"] == ["TITULO_SECUNDARIO", "IDIOMA"]
    assert datos["cantidades_adicionales"] == {"IDIOMA": "2"}


def test_novedad_rechaza_cantidad_sin_adicional_seleccionado():
    with pytest.raises(ValueError, match="corresponder"):
        DatosNovedadMensual(
            periodo="2026-08",
            cantidades_adicionales=(("IDIOMA", Decimal("2")),),
        )


def test_dto_convierte_listas_y_diccionarios_al_dominio():
    dto = NovedadMensualIn(
        empleado_id="11111111-1111-4111-8111-111111111111",
        periodo="2026-08",
        adicionales_convencionales=["IDIOMA"],
        cantidades_adicionales={"IDIOMA": Decimal("2")},
    )
    assert dto.datos_dominio().cantidades_adicionales == (("IDIOMA", Decimal("2")),)


def test_modelo_declara_columnas_json_de_adicionales():
    assert "adicionales_convencionales" in NovedadMensual.__table__.columns
    assert "cantidades_adicionales" in NovedadMensual.__table__.columns


def test_migracion_es_idempotente_y_no_desactiva_rls():
    from pathlib import Path

    sql = (Path(__file__).parents[2] / "migrations" / "003_novedades_adicionales_convencionales.sql").read_text()
    assert "ADD COLUMN IF NOT EXISTS adicionales_convencionales" in sql
    assert "ADD COLUMN IF NOT EXISTS cantidades_adicionales" in sql
    assert "DISABLE ROW LEVEL SECURITY" not in sql
