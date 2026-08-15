from decimal import Decimal
from types import SimpleNamespace
import uuid

from application.use_cases.liquidar_periodo import resolver_horas_extra


def _empleado(empleado_id=None):
    return SimpleNamespace(id=empleado_id or uuid.uuid4())


def _novedad(empleado_id, h50="0", h100="0", adicionales=None, cantidades=None):
    return SimpleNamespace(
        id=uuid.uuid4(), empleado_id=empleado_id,
        horas_extra_50=Decimal(h50), horas_extra_100=Decimal(h100),
        premios=Decimal("0"), tipo_premio="pendiente",
        descuentos_adicionales=Decimal("0"), observaciones="",
        adicionales_convencionales=adicionales or [],
        cantidades_adicionales=cantidades or {},
    )


def test_sin_novedades_conserva_resultado_vacio():
    emp = _empleado()
    assert resolver_horas_extra([emp], [], {}) == {}


def test_usa_horas_guardadas_del_periodo():
    emp = _empleado()
    nov = _novedad(emp.id, "3.5", "2")
    res = resolver_horas_extra([emp], [nov], {})[str(emp.id)]
    assert res["horas_extra_50"] == Decimal("3.5")
    assert res["horas_extra_100"] == Decimal("2")
    assert res["origen"] == "novedad_mensual"
    assert res["novedad_id"] == str(nov.id)


def test_novedad_guardada_prevalece_sobre_body_anterior():
    emp = _empleado()
    nov = _novedad(emp.id, "4", "1")
    legacy = {str(emp.id): {"horas_extra_50": "99", "horas_extra_100": "99"}}
    res = resolver_horas_extra([emp], [nov], legacy)[str(emp.id)]
    assert res["horas_extra_50"] == Decimal("4")
    assert res["horas_extra_100"] == Decimal("1")
    assert res["origen"] == "novedad_mensual"


def test_body_anterior_sigue_funcionando_si_no_hay_guardada():
    emp = _empleado()
    legacy = {str(emp.id): {"horas_extra_50": "2.5", "horas_extra_100": "1"}}
    res = resolver_horas_extra([emp], [], legacy)[str(emp.id)]
    assert res["horas_extra_50"] == Decimal("2.5")
    assert res["horas_extra_100"] == Decimal("1")
    assert res["origen"] == "body_legacy"


def test_descarta_body_de_empleado_ajeno_a_la_nomina():
    emp = _empleado()
    ajeno = str(uuid.uuid4())
    assert resolver_horas_extra(
        [emp], [], {ajeno: {"horas_extra_50": "50"}}
    ) == {}


def test_lleva_adicionales_guardados_al_motor():
    emp = _empleado()
    nov = _novedad(
        emp.id,
        adicionales=["TITULO_SECUNDARIO", "IDIOMA"],
        cantidades={"IDIOMA": "2"},
    )
    res = resolver_horas_extra([emp], [nov], {})[str(emp.id)]
    assert res["adicionales_convencionales"] == ("TITULO_SECUNDARIO", "IDIOMA")
    assert res["cantidades_adicionales"] == (("IDIOMA", Decimal("2")),)
