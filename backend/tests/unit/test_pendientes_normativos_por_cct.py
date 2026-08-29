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


def test_pendientes_usados_ignora_catalogo_no_consultado():
    parametros = ParametroSet([
        _p("APORTE_USADO", None),
        _p("CONTRIB_NO_USADA", None),
    ])

    parametros.fraccion("APORTE_USADO")

    assert [p.codigo for p in parametros.pendientes_usados()] == ["APORTE_USADO"]


def test_con_extra_comparte_el_registro_de_uso():
    parametros = ParametroSet([_p("GENERAL", None)])
    parametro_extra = _p("CUOTA_RESUELTA", "130/75")
    por_empleado = parametros.con_extra(parametro_extra)

    por_empleado.fraccion("CUOTA_RESUELTA")

    assert [p.codigo for p in parametros.pendientes_usados()] == ["CUOTA_RESUELTA"]


def test_consultar_porcentaje_guarda_el_objeto_y_no_solo_el_codigo():
    parametro = _p("APORTE_ADEF_REM_414/05", "414/05")
    parametros = ParametroSet([parametro])

    assert parametros.fraccion("APORTE_ADEF_REM_414/05") == Decimal("1")
    assert parametros._parametros_usados == {
        "APORTE_ADEF_REM_414/05": parametro
    }
