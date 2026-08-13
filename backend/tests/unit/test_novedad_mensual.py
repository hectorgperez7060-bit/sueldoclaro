from decimal import Decimal

import pytest

from domain.entities.novedad import DatosNovedadMensual


def test_novedad_valida_y_normaliza_importes_y_observacion():
    datos = DatosNovedadMensual(
        periodo="2026-08",
        dias_trabajados=20,
        faltas_justificadas=1,
        horas_extra_50=Decimal("2.5"),
        premios=Decimal("10000"),
        observaciones="  Presentó certificado  ",
    )
    persistido = datos.para_persistir()
    assert persistido["horas_extra_50"] == Decimal("2.5")
    assert persistido["observaciones"] == "Presentó certificado"


@pytest.mark.parametrize("periodo", ["2026-8", "2026-13", "26-08", "texto", ""])
def test_periodo_debe_ser_aaaa_mm(periodo):
    with pytest.raises(ValueError, match="período"):
        DatosNovedadMensual(periodo=periodo)


def test_febrero_respeta_dias_del_anio():
    DatosNovedadMensual(periodo="2028-02", dias_trabajados=29)
    with pytest.raises(ValueError, match="entre 0 y 28"):
        DatosNovedadMensual(periodo="2026-02", dias_trabajados=29)


def test_dias_incompatibles_no_superan_el_mes():
    with pytest.raises(ValueError, match="suma de días"):
        DatosNovedadMensual(
            periodo="2026-04",
            dias_trabajados=25,
            vacaciones=6,
        )


@pytest.mark.parametrize(
    "campo",
    ["horas_extra_50", "horas_extra_100", "premios", "descuentos_adicionales"],
)
def test_horas_e_importes_no_admiten_negativos(campo):
    with pytest.raises(ValueError, match="negativo"):
        DatosNovedadMensual(periodo="2026-08", **{campo: Decimal("-1")})


def test_premio_exige_clasificacion_valida():
    with pytest.raises(ValueError, match="Tipo de premio"):
        DatosNovedadMensual(periodo="2026-08", premios=Decimal("1000"), tipo_premio="quizas")


def test_descuento_exige_observacion():
    with pytest.raises(ValueError, match="requieren una observación"):
        DatosNovedadMensual(periodo="2026-08", descuentos_adicionales=Decimal("1000"))
    DatosNovedadMensual(
        periodo="2026-08", descuentos_adicionales=Decimal("1000"),
        observaciones="Adelanto de sueldo autorizado",
    )
