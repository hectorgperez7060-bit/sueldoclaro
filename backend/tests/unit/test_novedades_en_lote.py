"""Carga de novedades para varios empleados a la vez.

Cargar diez legajos de a uno con el mismo mes es la parte que empuja a poner
cualquier cosa. Estas pruebas cubren las dos formas de evitarlo -aplicar la misma
novedad a todo el plantel y traer las del mes anterior- y, sobre todo, que
ninguna de las dos pise lo que ya estaba cargado.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from api.routes.novedades import _CAMPOS_COPIABLES, _copia_al_periodo
from application.dto.schemas import NovedadCopiaIn, NovedadLoteIn, ResultadoLoteNovedades
from domain.entities.novedad import DatosNovedadMensual
from main import create_app

EMP_A = "12345678-1234-5678-1234-567812345678"
EMP_B = "22345678-1234-5678-1234-567812345678"


def test_los_endpoints_de_lote_estan_publicados():
    rutas = create_app().openapi()["paths"]
    assert "/novedades/lote" in rutas
    assert "/novedades/copiar" in rutas
    assert "post" in rutas["/novedades/lote"]
    assert "post" in rutas["/novedades/copiar"]


# ------------------------------------------------ aplicar a todos


def test_el_lote_no_pide_empleado_y_vale_para_todo_el_plantel():
    dto = NovedadLoteIn(periodo="2026-08", dias_trabajados=20)
    assert dto.empleado_ids is None
    assert dto.datos_dominio().dias_trabajados == 20


def test_el_lote_puede_apuntar_a_algunos_empleados():
    dto = NovedadLoteIn(periodo="2026-08", empleado_ids=[EMP_A, EMP_B])
    assert dto.empleado_ids == [EMP_A, EMP_B]


def test_la_lista_de_empleados_no_se_cuela_en_los_datos_de_la_novedad():
    """empleado_ids es a quién aplicarla, no un dato de la novedad."""
    dto = NovedadLoteIn(periodo="2026-08", empleado_ids=[EMP_A])
    assert "empleado_ids" not in dto._datos()
    assert isinstance(dto.datos_dominio(), DatosNovedadMensual)


def test_el_lote_valida_igual_que_una_novedad_suelta():
    with pytest.raises(ValidationError, match="entre 0 y 28"):
        NovedadLoteIn(periodo="2026-02", dias_trabajados=29)


# ------------------------------------------------ copiar del mes anterior


def test_copiar_exige_dos_periodos_distintos():
    with pytest.raises(ValidationError, match="no pueden ser el mismo"):
        NovedadCopiaIn(periodo_origen="2026-08", periodo_destino="2026-08")


def test_copiar_valida_el_formato_de_los_dos_periodos():
    for origen, destino in [("2026-13", "2026-08"), ("2026-07", "agosto")]:
        with pytest.raises(ValidationError):
            NovedadCopiaIn(periodo_origen=origen, periodo_destino=destino)


class _NovedadFalsa:
    """Una novedad como la devuelve el ORM, para probar la copia sin base."""

    def __init__(self):
        self.periodo = "2026-07"
        self.dias_trabajados = 21
        self.horas_extra_50 = Decimal("6.5")
        self.faltas_injustificadas = 1
        self.observaciones = "mes con feriado trabajado"
        self.premios = Decimal("15000")
        self.tipo_premio = "remunerativo"
        self.adicionales_convencionales = ["ADIC_X"]
        self.cantidades_adicionales = {"ADIC_X": Decimal("2")}
        self.feriados_uocra_detalle = []
        self.horas_extra_uocra_detalle = []
        self.camioneros_detalle = {"rama": "general"}
        self.uom_detalle = {}


def test_la_copia_cambia_el_periodo_y_conserva_los_valores():
    copia = _copia_al_periodo(_NovedadFalsa(), "2026-08")
    assert copia.periodo == "2026-08"
    assert copia.dias_trabajados == 21
    assert copia.horas_extra_50 == Decimal("6.5")
    assert copia.faltas_injustificadas == 1
    assert copia.observaciones == "mes con feriado trabajado"
    assert copia.tipo_premio == "remunerativo"


def test_la_copia_no_recalcula_ni_prorratea_nada():
    origen = _NovedadFalsa()
    copia = _copia_al_periodo(origen, "2026-08")
    assert copia.premios == origen.premios
    assert copia.horas_extra_50 == origen.horas_extra_50


def test_la_copia_convierte_las_colecciones_al_tipo_del_dominio():
    copia = _copia_al_periodo(_NovedadFalsa(), "2026-08")
    assert copia.adicionales_convencionales == ("ADIC_X",)
    assert copia.cantidades_adicionales == (("ADIC_X", Decimal("2")),)
    assert copia.camioneros_detalle == {"rama": "general"}


def test_el_periodo_nunca_se_copia_del_origen():
    """Es justamente lo que tiene que cambiar."""
    assert "periodo" not in _CAMPOS_COPIABLES


def test_una_novedad_vacia_se_copia_sin_romper():
    class Vacia:
        periodo = "2026-07"

    copia = _copia_al_periodo(Vacia(), "2026-08")
    assert copia.periodo == "2026-08"
    assert copia.dias_trabajados == 0
    assert copia.adicionales_convencionales == ()


# ------------------------------------------------ resultado del lote


def test_el_resultado_informa_creadas_omitidas_y_el_motivo_de_cada_una():
    r = ResultadoLoteNovedades(
        creadas=8, omitidas=2,
        detalle=[{"empleado_id": EMP_A, "estado": "creada"},
                 {"empleado_id": EMP_B, "estado": "omitido",
                  "motivo": "Ya existen novedades para ese empleado y período"}],
    )
    assert r.creadas == 8 and r.omitidas == 2
    omitido = next(d for d in r.detalle if d["estado"] == "omitido")
    assert "Ya existen novedades" in omitido["motivo"]
