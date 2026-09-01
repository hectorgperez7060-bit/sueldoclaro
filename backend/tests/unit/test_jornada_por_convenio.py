"""La jornada completa la define cada convenio, no un 48 fijo.

Un trabajador de jornada completa de un convenio de 44 horas cargado contra un
divisor de 48 quedaba con proporción 0,9167 y el motor le prorrateaba el básico:
cobraba menos de lo que le corresponde y, por el art. 92 ter de la LCT, además
se lo trataba como parcial para la base de obra social.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from domain.entities.jornada import (
    HORAS_TOPE_LEY_11544,
    horas_desde_reglas,
    horas_jornada_completa,
    proporcion_jornada,
)
from infrastructure.excel.importer import horas_jornada_de

# Las cuatro formas en que las migraciones ya cargadas nombran la misma magnitud.
CONFIGURACIONES = [
    ("749/18", {"horas_semanales_convencionales": 44, "tope_legal_semanal": 48}, 44),
    ("761/19", {"horas_semanales": 44, "pausa_diaria_minutos": 20}, 44),
    ("130/75", {"completa_horas_semanales": 48, "divisor_horas_mensual": 200}, 48),
    ("414/05", {"completa_horas": 45, "nocturna_horas": 42}, 45),
]


@pytest.mark.parametrize("cct,configuracion,esperadas", CONFIGURACIONES)
def test_lee_la_jornada_de_cada_convenio(cct, configuracion, esperadas):
    assert horas_jornada_completa(configuracion) == Decimal(esperadas)


def test_un_convenio_que_no_declara_jornada_no_inventa_un_numero():
    assert horas_jornada_completa({"descanso_compensatorio": "1:1"}) is None
    assert horas_jornada_completa(None) is None


def test_encuentra_la_regla_jornada_entre_las_demas():
    reglas = [
        {"codigo": "ANTIGUEDAD", "configuracion": {"porcentaje_por_anio": 0.01}},
        {"codigo": "JORNADA", "configuracion": {"horas_semanales": 44}},
    ]
    assert horas_desde_reglas(reglas) == Decimal("44")
    assert horas_desde_reglas([{"codigo": "ANTIGUEDAD", "configuracion": {}}]) is None


@pytest.mark.parametrize("cct,configuracion,completas", CONFIGURACIONES)
def test_la_jornada_completa_del_convenio_da_proporcion_uno(cct, configuracion, completas):
    """El corazón del arreglo: 44 horas en un convenio de 44 es jornada completa."""
    horas = horas_jornada_completa(configuracion)
    assert proporcion_jornada(completas, horas) == Decimal("1")


def test_media_jornada_da_un_medio_en_cualquier_convenio():
    assert proporcion_jornada(22, Decimal("44")) == Decimal("0.5")
    assert proporcion_jornada(24, Decimal("48")) == Decimal("0.5")
    assert proporcion_jornada(Decimal("22.5"), Decimal("45")) == Decimal("0.5")


def test_no_se_puede_declarar_mas_jornada_que_la_del_convenio():
    with pytest.raises(ValueError, match="horas extra"):
        proporcion_jornada(48, Decimal("44"))


def test_horas_cero_o_negativas_se_rechazan():
    for invalidas in (0, -1):
        with pytest.raises(ValueError):
            proporcion_jornada(invalidas, Decimal("44"))


def test_sin_dato_del_convenio_cae_al_tope_legal_y_no_a_un_supuesto():
    assert horas_jornada_de({}, "999/99") == HORAS_TOPE_LEY_11544
    assert horas_jornada_de(None, "749/18") == HORAS_TOPE_LEY_11544
    assert horas_jornada_de({"749/18": Decimal("44")}, "749/18") == Decimal("44")


def test_el_recorte_que_este_arreglo_evita():
    """Deja registrado, en plata, qué pasaba antes del arreglo.

    Categoría segunda del CCT 749/18, agosto 2026, jornada completa de 44 horas.
    """
    basico = Decimal("1280935.75")
    antes = (basico * proporcion_jornada(44, Decimal("48"))).quantize(Decimal("0.01"))
    ahora = (basico * proporcion_jornada(44, Decimal("44"))).quantize(Decimal("0.01"))
    assert ahora == basico
    assert basico - antes == Decimal("106744.65")
