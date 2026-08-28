from datetime import date
from decimal import Decimal

from domain.entities.parametros import ParametroLegal, ParametroSet


def _p(codigo: str, cct: str | None) -> ParametroLegal:
    return ParametroLegal(
        codigo, Decimal("1"), "%", "ded_todos", date(2026, 8, 1),
        None, False, "", cct,
    )


def test_pendientes_no_mezclan_convenios_ajenos():
    parametros = ParametroSet([
        _p("GENERAL", None),
        _p("COMERCIO", "130/75"),
        _p("UOM", "260/75"),
    ])

    codigos = {
        p.codigo for p in parametros.pendientes_normativos({"130/75"})
    }

    assert codigos == {"GENERAL", "COMERCIO"}
