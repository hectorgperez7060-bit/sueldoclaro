"""Compila un manifiesto validado a SQL PostgreSQL idempotente."""
from __future__ import annotations

import hashlib
import json
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Any

from domain.entities.paquete_convenio import DiagnosticoPaquete, validar_paquete


def cargar_paquete(ruta: str | Path) -> dict[str, Any]:
    return json.loads(Path(ruta).read_text(encoding="utf-8"))


def compilar_paquete(datos: dict[str, Any]) -> tuple[str, DiagnosticoPaquete]:
    diagnostico = validar_paquete(datos)
    if not diagnostico.valido:
        raise ValueError("Paquete inválido:\n- " + "\n- ".join(diagnostico.errores))
    canonico = json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    huella = hashlib.sha256(canonico.encode()).hexdigest()
    identidad, estructura = datos["identidad"], datos.get("estructura", {})
    numero = identidad["numero"]
    sql = ["BEGIN;", _upsert_cct(identidad)]
    for categoria in estructura.get("categorias", []):
        sql.append(_upsert_categoria(numero, categoria))
    for regla in estructura.get("reglas", []):
        sql.append(_upsert_regla(numero, regla))
    for periodo in datos.get("periodos", []):
        inicio, fin = _limites(periodo["periodo"])
        for escala in periodo.get("escalas", []):
            sql.append(_upsert_escala(numero, escala, inicio, fin))
        for parametro in periodo.get("parametros", []):
            sql.append(_upsert_parametro(numero, parametro, inicio, fin))
    resumen = json.dumps(diagnostico.resumen, ensure_ascii=False, sort_keys=True)
    sql.append(
        "INSERT INTO public.cct_paquete_version "
        "(cct_numero, paquete_version, hash_sha256, estado, resumen, fuente_manifest) VALUES "
        f"({_q(numero)}, {_q(datos['version_paquete'])}, {_q(huella)}, 'INSTALADO', "
        f"{_json(resumen)}, {_q(datos.get('fuente_manifest', 'manifiesto local'))}) "
        "ON CONFLICT (cct_numero, paquete_version) DO UPDATE SET "
        "hash_sha256=EXCLUDED.hash_sha256, estado=EXCLUDED.estado, resumen=EXCLUDED.resumen, "
        "fuente_manifest=EXCLUDED.fuente_manifest, instalado_at=now();"
    )
    sql.extend(["COMMIT;", ""])
    return "\n\n".join(sql), diagnostico


def _upsert_cct(x: dict) -> str:
    return (
        "INSERT INTO public.cct (numero,nombre,sindicato,activo) VALUES "
        f"({_q(x['numero'])},{_q(x['nombre'])},{_q(x.get('sindicato',''))},true) "
        "ON CONFLICT (numero) DO UPDATE SET nombre=EXCLUDED.nombre, sindicato=EXCLUDED.sindicato, activo=true;"
    )


def _upsert_categoria(cct: str, x: dict) -> str:
    return (
        "INSERT INTO public.cct_categoria (cct_numero,codigo,nombre,orden,fuente,estado_fuente,is_verified,version,activa) VALUES "
        f"({_q(cct)},{_q(x['codigo'])},{_q(x['nombre'])},{int(x.get('orden',0))},{_q(x.get('fuente',''))},"
        f"{_q(x.get('estado_fuente','PENDIENTE_DOCUMENTACION'))},{_b(x.get('verificado',False))},{int(x.get('version',1))},true) "
        "ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET nombre=EXCLUDED.nombre,orden=EXCLUDED.orden,"
        "fuente=EXCLUDED.fuente,estado_fuente=EXCLUDED.estado_fuente,is_verified=EXCLUDED.is_verified,activa=true;"
    )


def _upsert_regla(cct: str, x: dict) -> str:
    config = json.dumps(x.get("configuracion", {}), ensure_ascii=False, sort_keys=True)
    return (
        "INSERT INTO public.cct_regla_estructural (cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,estado_fuente,is_verified,version,activa) VALUES "
        f"({_q(cct)},{_q(x['codigo'])},{_q(x['tipo'])},{_q(x['descripcion'])},{_q(x.get('articulo',''))},{_json(config)},"
        f"{_q(x.get('fuente',''))},{_q(x.get('estado_fuente','PENDIENTE_DOCUMENTACION'))},{_b(x.get('verificado',False))},{int(x.get('version',1))},true) "
        "ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET descripcion=EXCLUDED.descripcion,articulo=EXCLUDED.articulo,"
        "configuracion=EXCLUDED.configuracion,fuente=EXCLUDED.fuente,estado_fuente=EXCLUDED.estado_fuente,"
        "is_verified=EXCLUDED.is_verified,activa=true;"
    )


def _upsert_escala(cct: str, x: dict, inicio: date, fin: date) -> str:
    return (
        "DELETE FROM public.escala_salarial WHERE "
        f"cct_numero={_q(cct)} AND categoria={_q(x['categoria'])} AND valid_from={_q(inicio.isoformat())} "
        f"AND version={int(x.get('version',1))} AND zona={_q(x.get('zona',''))};\n"
        "INSERT INTO public.escala_salarial (id,cct_numero,categoria,basico,valid_from,valid_to,fuente,estado_fuente,is_verified,version,provisoria,zona,unidad_escala,habilitada_liquidacion) VALUES "
        f"(gen_random_uuid(),{_q(cct)},{_q(x['categoria'])},{x['basico']},{_q(inicio.isoformat())},{_q(fin.isoformat())},"
        f"{_q(x.get('fuente',''))},{_q(x.get('estado_fuente','PENDIENTE_DOCUMENTACION'))},{_b(x.get('verificado',False))},"
        f"{int(x.get('version',1))},{_b(x.get('provisoria',False))},{_q(x.get('zona',''))},{_q(x.get('unidad','MENSUAL'))},{_b(x.get('habilitada',False))}) "
        "ON CONFLICT DO NOTHING;"
    )


def _upsert_parametro(cct: str, x: dict, inicio: date, fin: date) -> str:
    incidencias = json.dumps(x.get("incidencias", {}), ensure_ascii=False, sort_keys=True)
    return (
        "DELETE FROM public.parametro_legal WHERE "
        f"codigo={_q(x['codigo'])} AND cct_numero={_q(cct)} AND valid_from={_q(inicio.isoformat())} "
        f"AND version={int(x.get('version',1))};\n"
        "INSERT INTO public.parametro_legal (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,is_verified,version,cct_numero,incidencias) VALUES "
        f"(gen_random_uuid(),{_q(x['codigo'])},{x['valor']},{_q(x['unidad'])},{_q(x['ambito'])},{_q(inicio.isoformat())},{_q(fin.isoformat())},"
        f"{_q(x.get('fuente',''))},{_q(x.get('estado_fuente','PENDIENTE_DOCUMENTACION'))},{_b(x.get('verificado',False))},{int(x.get('version',1))},{_q(cct)},{_json(incidencias)}) "
        "ON CONFLICT DO NOTHING;"
    )


def _limites(periodo: str) -> tuple[date, date]:
    anio, mes = map(int, periodo.split("-"))
    return date(anio, mes, 1), date(anio, mes, monthrange(anio, mes)[1])


def _q(valor: Any) -> str:
    return "'" + str(valor).replace("'", "''") + "'"


def _json(texto: str) -> str:
    return _q(texto) + "::jsonb"


def _b(valor: Any) -> str:
    return "true" if bool(valor) else "false"
