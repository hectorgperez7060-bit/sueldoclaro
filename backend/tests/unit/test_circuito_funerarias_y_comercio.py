"""Circuito completo de prueba para Comercio 130/75 y SOECRA 749/18 y 761/19.

Estas pruebas no leen texto de migraciones: ejecutan el motor. Cubren el camino
que un usuario recorre de verdad —liquidar, mirar el recibo, agrupar la boleta
sindical y calcular las bases del F.931— para los convenios habilitados en la
prueba piloto.

Existen porque el resto de la cobertura de funerarias es documental: verifica
que la migración diga lo que tiene que decir, pero nunca liquidó un recibo. Esa
distancia dejó pasar que ``base_deduccion`` viajaba con una descripción en prosa
donde el motor espera un selector, y el CCT 761/19 se caía al liquidar.
"""
from __future__ import annotations

import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.boleta_sindical import agrupar_obligaciones_sindicales
from domain.entities.concepto import TipoConcepto
from domain.entities.empleado import Empleado
from domain.entities.parametros import EscalaSalarial, ParametroLegal
from domain.payroll_engine.config import CctConfig
from domain.payroll_engine.engine import (
    BASES_DEDUCCION_VALIDAS,
    MotorLiquidacion,
    Novedades,
)
from domain.value_objects.cuil import Cuil
from domain.value_objects.dinero import Dinero
from domain.value_objects.periodo import Periodo
from infrastructure.lsd.calculator import ParametrosPeriodoLSD, calcular_bases_lsd
from parametros_seed import parametros_ejemplo, sin_amparos

BACKEND = Path(__file__).resolve().parents[2]
VIGENCIA = date(2026, 8, 1)
PERIODO = Periodo.desde_texto("2026-08")


def _cct(numero: str, *, presentismo: bool) -> CctConfig:
    return CctConfig(
        cct_numero=numero,
        antiguedad_pct_por_anio=Decimal("0.01"),
        presentismo_divisor=Decimal("12"),
        divisor_horas=Decimal("200"),
        aplica_presentismo=presentismo,
        aplica_cuota_sindical=False,
    )


def _empleado(numero: str, categoria: str, *, afiliado: bool) -> Empleado:
    return Empleado(
        nombre="Prueba", apellido="Piloto", cuil=Cuil("20123456786"),
        fecha_ingreso=date(2018, 3, 1), cct_numero=numero,
        categoria=categoria, legajo="1", afiliado_sindicato=afiliado,
    )


def _escala(numero: str, categoria: str, basico: str, zona: str = "") -> EscalaSalarial:
    return EscalaSalarial(
        numero, categoria, Dinero(Decimal(basico)), VIGENCIA,
        is_verified=False, provisoria=True, zona=zona,
        habilitada_liquidacion=False, estado_fuente="PROVISORIA",
    )


def _deduccion(codigo: str, valor: str, ambito: str, cct: str,
               incidencias: dict) -> ParametroLegal:
    return ParametroLegal(
        codigo, Decimal(valor), "%", ambito, VIGENCIA,
        valid_to=date(2026, 8, 31), is_verified=False,
        fuente="Paquete provisorio de la prueba piloto",
        cct_numero=cct, incidencias=incidencias,
    )


def _aporte_solidario_soecra() -> ParametroLegal:
    """Réplica del parámetro que instala la migración 054 para el CCT 761/19."""
    return _deduccion(
        "APORTE_SOLIDARIO_SOECRA_761/19", "0.01", "ded_noafil", "761/19",
        {"base_deduccion": "remunerativa",
         "base_deduccion_texto_convencional": "total de remuneraciones (CCT 761/19 arts. 75 y 76)",
         "sumas_no_remunerativas_incluidas": False,
         "condicion": "solo_no_afiliados",
         "destino_pago": "SOECRA", "codigo_boleta": "SOECRA_APORTE_SOLIDARIO",
         "canal_pago": "CuotaQ", "url_pago": "https://www.cuotaq.com/soecra"},
    )


def _liquidar(numero, categoria, basico, *, afiliado, extras=(), presentismo=False):
    params = parametros_ejemplo()
    for extra in extras:
        params = params.con_extra(extra)
    motor = MotorLiquidacion(params, sin_amparos())
    empleado = _empleado(numero, categoria, afiliado=afiliado)
    resultado = motor.liquidar_mensual(
        empleado, PERIODO, _escala(numero, categoria, basico),
        _cct(numero, presentismo=presentismo), Novedades(),
    )
    return empleado, resultado


def _concepto(resultado, codigo):
    return next((c for c in resultado.conceptos if c.codigo == codigo), None)


# --------------------------------------------------------------- recibo


def test_cementerios_liquida_el_recibo_y_no_se_cae_por_la_base_del_aporte():
    """Regresión del fallo real: el motor abortaba antes de emitir el recibo."""
    _, res = _liquidar(
        "761/19", "Con fines de lucro - Parque y crematorio - Categoría 4ª - Trabajador calificado",
        "1188504.22", afiliado=False, extras=[_aporte_solidario_soecra()],
    )
    aporte = _concepto(res, "APORTE_SOLIDARIO_SOECRA_761/19")
    assert aporte is not None, "el aporte solidario no llegó al recibo"
    assert aporte.tipo == TipoConcepto.DEDUCCION

    base_remunerativa = res.total_remunerativo
    assert aporte.base_calculo.redondear() == base_remunerativa
    assert aporte.importe == base_remunerativa.porcentaje(Decimal("0.01")).redondear()


def test_el_aporte_solidario_no_alcanza_al_afiliado():
    _, res = _liquidar(
        "761/19", "Con fines de lucro - Parque y crematorio - Categoría 4ª - Trabajador calificado",
        "1188504.22", afiliado=True, extras=[_aporte_solidario_soecra()],
    )
    assert _concepto(res, "APORTE_SOLIDARIO_SOECRA_761/19") is None


def test_cocherias_no_retiene_nada_sindical_porque_sus_aportes_estan_bloqueados():
    """El CCT 749/18 tiene los arts. 55, 56 y 61 en disputa documental.

    Mientras no se resuelva, ninguna liquidación puede retenerle nada al
    trabajador por ese concepto: la ausencia es el comportamiento correcto.
    """
    _, res = _liquidar(
        "749/18", "Agrupamiento A - Categoría Segunda - Administrativo Polivalente A",
        "1280935.75", afiliado=True,
    )
    sindicales = [c for c in res.conceptos
                  if "SOECRA" in c.codigo or c.codigo == "CUOTA_SINDICAL"]
    assert sindicales == []


def test_comercio_liquida_el_recibo_en_el_mismo_circuito():
    _, res = _liquidar("130/75", "Administrativo A", "1200000.00",
                       afiliado=True, presentismo=True)
    assert _concepto(res, "BASICO") is not None
    assert _concepto(res, "ANTIGUEDAD") is not None
    assert _concepto(res, "PRESENTISMO") is not None
    assert res.total_remunerativo.monto > 0


# --------------------------------------------------- boleta sindical


def test_la_boleta_sindical_de_soecra_sale_del_recibo_sin_recalcular():
    empleado, res = _liquidar(
        "761/19", "Con fines de lucro - Parque y crematorio - Categoría 4ª - Trabajador calificado",
        "1188504.22", afiliado=False, extras=[_aporte_solidario_soecra()],
    )
    aporte = _concepto(res, "APORTE_SOLIDARIO_SOECRA_761/19")
    grupos = agrupar_obligaciones_sindicales([{
        "empleado_id": empleado.legajo, "cct_numero": "761/19",
        "localidad": "Pilar",
        "conceptos": [{"codigo": aporte.codigo, "importe": str(aporte.importe.monto),
                       "destino_pago": aporte.destino_pago,
                       "codigo_boleta": aporte.codigo_boleta,
                       "canal_pago": aporte.canal_pago,
                       "url_pago": aporte.url_pago}],
    }])
    assert len(grupos) == 1
    boleta = grupos[0]
    assert boleta["destino_pago"] == "SOECRA"
    assert boleta["codigo_boleta"] == "SOECRA_APORTE_SOLIDARIO"
    assert boleta["url_pago"] == "https://www.cuotaq.com/soecra"
    assert Decimal(boleta["importe"]) == aporte.importe.monto


def test_una_empresa_mixta_no_mezcla_las_boletas_de_comercio_y_soecra():
    grupos = agrupar_obligaciones_sindicales([
        {"empleado_id": "e1", "cct_numero": "130/75", "localidad": "CABA",
         "conceptos": [{"codigo": "APORTE_ART100", "importe": "1000.00",
                        "destino_pago": "FAECYS", "codigo_boleta": "FAECYS_ART100"}]},
        {"empleado_id": "e2", "cct_numero": "761/19", "localidad": "Pilar",
         "conceptos": [{"codigo": "APORTE_SOLIDARIO_SOECRA_761/19", "importe": "13905.50",
                        "destino_pago": "SOECRA", "codigo_boleta": "SOECRA_APORTE_SOLIDARIO"}]},
    ])
    assert len(grupos) == 2
    assert {g["cct_numero"] for g in grupos} == {"130/75", "761/19"}
    assert {g["destino_pago"] for g in grupos} == {"FAECYS", "SOECRA"}


# ------------------------------------------------------ F.931 / LSD


def _params_lsd() -> ParametrosPeriodoLSD:
    return ParametrosPeriodoLSD(
        periodo=PERIODO,
        tope_min_sipa=Dinero("135837.40"),
        tope_max_sipa_mensual=Dinero("4414652.38"),
        tope_max_sipa_sac=Dinero("2207326.19"),
        piso_obra_social=Dinero("135837.40"),
        detraccion_ley27541_mensual=Dinero("0.00"),
        detraccion_ley27541_sac=Dinero("0.00"),
    )


@pytest.mark.parametrize("numero,categoria,basico,extras", [
    ("761/19", "Con fines de lucro - Parque y crematorio - Categoría 4ª - Trabajador calificado",
     "1188504.22", True),
    ("130/75", "Administrativo A", "1200000.00", False),
])
def test_las_diez_bases_del_f931_salen_de_la_liquidacion(numero, categoria, basico, extras):
    empleado, res = _liquidar(
        numero, categoria, basico, afiliado=False,
        extras=[_aporte_solidario_soecra()] if extras else (),
    )
    bases = calcular_bases_lsd(res, empleado, _cct(numero, presentismo=False),
                               _params_lsd(), PERIODO)
    assert len(bases) == 10
    assert all(isinstance(b, Decimal) and b >= 0 for b in bases)
    assert bases[0] > 0, "la base imponible 1 no puede quedar en cero"


def test_el_aporte_sindical_no_infla_las_bases_imponibles_del_f931():
    """Una deducción sindical no es remuneración: no puede mover el F.931."""
    empleado, con_aporte = _liquidar(
        "761/19", "Con fines de lucro - Parque y crematorio - Categoría 4ª - Trabajador calificado",
        "1188504.22", afiliado=False, extras=[_aporte_solidario_soecra()],
    )
    _, sin_aporte = _liquidar(
        "761/19", "Con fines de lucro - Parque y crematorio - Categoría 4ª - Trabajador calificado",
        "1188504.22", afiliado=True, extras=[_aporte_solidario_soecra()],
    )
    cct = _cct("761/19", presentismo=False)
    assert (calcular_bases_lsd(con_aporte, empleado, cct, _params_lsd(), PERIODO)
            == calcular_bases_lsd(sin_aporte, empleado, cct, _params_lsd(), PERIODO))


# ------------------------------------------- guarda de carga normativa


def _bases_declaradas():
    """Todo ``base_deduccion`` declarado en la normativa cargada del repositorio."""
    encontrados = []
    for ruta in sorted((BACKEND / "normativa").glob("*.json")):
        paquete = json.loads(ruta.read_text(encoding="utf-8"))
        for periodo in paquete.get("periodos", []):
            for parametro in periodo.get("parametros", []):
                valor = (parametro.get("incidencias") or {}).get("base_deduccion")
                if valor is not None:
                    encontrados.append((ruta.name, parametro.get("codigo"), valor))
    for ruta in sorted((BACKEND / "migrations").glob("*.sql")):
        for valor in re.findall(r'"base_deduccion":\s*"([^"]+)"',
                                ruta.read_text(encoding="utf-8")):
            encontrados.append((ruta.name, "-", valor))
    return encontrados


def test_ninguna_carga_normativa_declara_una_base_de_deduccion_inexistente():
    """La prosa descriptiva no puede ocupar el lugar de un selector del motor."""
    declarados = _bases_declaradas()
    assert declarados, "la guarda quedó sin nada que verificar"
    invalidos = [d for d in declarados if d[2] not in BASES_DEDUCCION_VALIDAS]
    assert invalidos == [], (
        "hay cargas normativas con una base de deducción que el motor no conoce: "
        f"{invalidos}. Valores admitidos: {BASES_DEDUCCION_VALIDAS}"
    )


def test_la_migracion_056_corrige_la_base_en_una_base_ya_instalada():
    """054 ya corrió en producción: el arreglo necesita su propia migración."""
    sql = (BACKEND / "migrations" / "056_corregir_base_deduccion_soecra_761_19.sql").read_text(
        encoding="utf-8")

    # Toca los dos parámetros de SOECRA y ninguno más.
    assert sql.count("UPDATE public.parametro_legal") == 2
    for codigo in ("APORTE_SOLIDARIO_SOECRA_761/19", "CUOTA_SINDICAL_SOECRA_761/19"):
        assert codigo in sql
    assert "'remunerativa'" in sql
    assert "base_deduccion_texto_convencional" in sql

    # Idempotente: si ya está corregido, el UPDATE no alcanza ninguna fila.
    assert "IS DISTINCT FROM 'remunerativa'" in sql

    # Transaccional y con control final que falla antes de dejar basura.
    assert sql.count("BEGIN;") == 1 and sql.count("COMMIT;") == 1
    assert "RAISE EXCEPTION" in sql

    # No toca importes ni estados documentales.
    for prohibido in ("UPDATE public.escala_salarial", "habilitada_liquidacion",
                      "is_verified = true", "VERIFICADA_OFICIAL"):
        assert prohibido not in sql


def test_no_hay_dos_migraciones_con_el_numero_056():
    numeros = [p.name[:3] for p in (BACKEND / "migrations").glob("056_*.sql")]
    assert len(numeros) == 1, "el número 056 ya está usado por otra migración"
