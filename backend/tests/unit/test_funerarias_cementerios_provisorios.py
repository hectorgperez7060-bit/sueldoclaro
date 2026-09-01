"""Pruebas de seguridad para CCT 749/18 y 761/19 provisorios."""
from __future__ import annotations

import json
from pathlib import Path

from domain.entities.encuadramiento_asistido import sugerir_encuadramiento


BACKEND = Path(__file__).resolve().parents[2]
NORMATIVA = BACKEND / "normativa"


def _paquete(nombre: str) -> dict:
    return json.loads((NORMATIVA / nombre).read_text(encoding="utf-8"))


def _periodo(paquete: dict) -> dict:
    return next(p for p in paquete["periodos"] if p["periodo"] == "2026-08")


def test_cocherias_queda_provisoria_y_bloqueada():
    paquete = _paquete("soecra_749_18_2026_08_provisorio.json")
    periodo = _periodo(paquete)

    assert paquete["cct"] == "749/18"
    assert len(paquete["estructura"]["categorias"]) == 11
    assert len(paquete["estructura"]["reglas"]) == 12
    assert len(periodo["escalas"]) == 11
    assert len(periodo["parametros"]) == 11
    assert all(e["estado_fuente"] == "PROVISORIA" for e in periodo["escalas"])
    assert all(e["provisoria"] and not e["verificado"] and not e["habilitada"] for e in periodo["escalas"])


def test_cementerios_queda_provisorio_con_zonas_sin_asignar():
    paquete = _paquete("soecra_761_19_2026_08_provisorio.json")
    periodo = _periodo(paquete)

    assert paquete["cct"] == "761/19"
    assert len(paquete["estructura"]["categorias"]) == 16
    assert len(paquete["estructura"]["reglas"]) == 18
    assert len(periodo["escalas"]) == 30
    assert len(periodo["parametros"]) == 32
    assert {e["zona"] for e in periodo["escalas"]} == {"ZONA 1", "ZONA 2", "ZONA INHOSPITA"}
    assert all(e["provisoria"] and not e["verificado"] and not e["habilitada"] for e in periodo["escalas"])


def test_migracion_no_disfraza_datos_como_homologados():
    sql = (BACKEND / "migrations" / "054_funerarias_cementerios_agosto_2026.sql").read_text(encoding="utf-8")

    assert "'PROVISORIA'" in sql
    assert "PUBLICADA_POR_PARTE_SIGNATARIA" not in sql
    assert "NORMA_HOMOLOGADA" not in sql
    assert "PENDIENTE_HOMOLOGACION" not in sql
    assert "habilitada_liquidacion" in sql
    # La migración es el reflejo de los dos paquetes: se cuenta contra ellos y no
    # contra un número fijo, para que cargar más escalas no rompa la prueba ni la
    # vuelva decorativa.
    paquetes = [_paquete("soecra_749_18_2026_08_provisorio.json"),
                _paquete("soecra_761_19_2026_08_provisorio.json")]
    escalas = sum(len(_periodo(p)["escalas"]) for p in paquetes)
    parametros = sum(len(_periodo(p)["parametros"]) for p in paquetes)
    assert sql.count("INSERT INTO public.escala_salarial ") == escalas
    assert sql.count("INSERT INTO public.parametro_legal ") == parametros
    assert sql.count("INSERT INTO public.cct_paquete_version ") == len(paquetes)
    assert sql.count("VALUES (gen_random_uuid(),") == escalas + parametros + len(paquetes)
    # Ninguna escala puede quedar habilitada para liquidar.
    assert sql.count("'MENSUAL',false)") == escalas
    assert "'MENSUAL',true)" not in sql
    columnas_cct = (
        "id,numero,nombre,sindicato,cuota_sindical_pct,"
        "antiguedad_pct_por_anio,presentismo_divisor,divisor_horas,"
        "aplica_presentismo,aplica_cuota_sindical,activo"
    )
    assert sql.count(columnas_cct) == 2
    assert sql.count(",0,0.01,10,200,false,false,true)") == 2


def test_encuadra_funebre_y_cementerio_privado_sin_aplicacion_automatica():
    funeraria = sugerir_encuadramiento(
        "Servicios funerarios y casa velatoria", "Ituzaingó", "Administrativa polivalente"
    )
    cementerio = sugerir_encuadramiento(
        "Cementerio privado y crematorio", "Merlo", "Operario de parque"
    )

    assert funeraria["candidatos"][0]["cct_numero"] == "749/18"
    assert cementerio["candidatos"][0]["cct_numero"] == "761/19"
    assert not funeraria["puede_aplicar_automaticamente"]
    assert not cementerio["puede_aplicar_automaticamente"]


def test_cementerio_municipal_no_se_encuadra_automaticamente():
    resultado = sugerir_encuadramiento(
        "Cementerio municipal", "Merlo", "Operario"
    )

    assert resultado["candidatos"] == []
    assert any("municipal" in texto.lower() for texto in resultado["faltantes"])


def test_politica_operativa_configura_reglas_sin_inventar_cuota():
    sql = (
        BACKEND / "migrations" / "055_politica_provisoria_general_y_soecra.sql"
    ).read_text(encoding="utf-8")

    assert "presentismo_divisor = 10" in sql
    assert "aplica_presentismo = true" in sql
    assert "antiguedad_pct_por_anio = 0.01" in sql
    assert "aplica_cuota_sindical = false" in sql
    assert "cuota_sindical_pct = 0" in sql


def test_dashboard_no_tiene_lista_blanca_de_convenios_provisorios():
    fuente = (BACKEND / "src" / "api" / "routes" / "convenios.py").read_text(
        encoding="utf-8"
    )

    assert 'cct.numero in {"389/04", "659/13"}' not in fuente
    assert "escalas_provisorias_publicadas" in fuente
