"""Compila el JSON UOM auditado en una migración SQL idempotente."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


SOURCE = "ADIMRA/UOMRA Anexo I 2026-2027 · RE-2026-79536710-APN-CGDTEYS#MCH"
AGREEMENT = "ADIMRA/UOMRA acta 14/08/2026 · RE-2026-79537879-APN-CGDTEYS#MCH"
INSURANCE = "ADIMRA/UOMRA seguros 14/08/2026 · RE-2026-79536812-APN-CGDTEYS#MCH"


def q(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def code(prefix: str, *parts: str) -> str:
    raw = "|".join(parts)
    slug = re.sub(r"[^A-Z0-9]+", "_", raw.upper()).strip("_")[:35]
    return f"{prefix}_{slug}_{hashlib.sha1(raw.encode()).hexdigest()[:8]}"[:60]


def compile_sql(data: dict) -> str:
    if data["cct"] != "260/75" or data["conteos"] != {"CATEGORIA": 247, "IMGR": 5, "ADICIONAL": 75}:
        raise ValueError("Paquete UOM inesperado")
    categories = [row for row in data["filas"] if row["tipo"] == "CATEGORIA"]
    imgr = [row for row in data["filas"] if row["tipo"] == "IMGR"]
    additions = [row for row in data["filas"] if row["tipo"] == "ADICIONAL"]
    occurrences = Counter((r["grupo_codigo"], r["pagina"], r["etiqueta"]) for r in categories)
    seen = Counter()
    normalized = []
    for order, row in enumerate(categories, 1):
        key = (row["grupo_codigo"], row["pagina"], row["etiqueta"])
        seen[key] += 1
        suffix = f" #{seen[key]}" if occurrences[key] > 1 else ""
        group_short = row["grupo_nombre"].replace("Ramas ", "R").replace("Rama ", "R")
        name = f"{row['etiqueta']} · {group_short} · pág. {row['pagina']}{suffix}"
        name = name[:120]
        normalized.append((code("UOM", row["grupo_codigo"], str(row["pagina"]), row["etiqueta"], str(seen[key])), name, order, row))

    lines = ["-- UOM CCT 260/75 · estructura completa y escalas agosto 2026.", "BEGIN;", "",
             "ALTER TABLE public.novedad_mensual ADD COLUMN IF NOT EXISTS uom_detalle jsonb NOT NULL DEFAULT '{}'::jsonb;",
             "ALTER TABLE public.novedad_mensual DROP CONSTRAINT IF EXISTS uom_detalle_objeto;",
             "ALTER TABLE public.novedad_mensual ADD CONSTRAINT uom_detalle_objeto CHECK (jsonb_typeof(uom_detalle)='object');", "",
             "INSERT INTO public.cct (id,numero,nombre,sindicato,cuota_sindical_pct,antiguedad_pct_por_anio,presentismo_divisor,divisor_horas,aplica_presentismo,aplica_cuota_sindical,activo)",
             "VALUES (gen_random_uuid(),'260/75','Metalúrgicos','UOMRA',0,0,12,200,false,false,true)",
             "ON CONFLICT (numero) DO UPDATE SET nombre=EXCLUDED.nombre,sindicato=EXCLUDED.sindicato,activo=true;", "",
             "UPDATE public.cct_categoria SET activa=false WHERE cct_numero='260/75';", "",
             "INSERT INTO public.cct_categoria (id,cct_numero,codigo,nombre,orden,activa,fuente,estado_fuente,is_verified,version) VALUES"]
    values = []
    for cat_code, name, order, row in normalized:
        metadata = f"{SOURCE}; grupo={row['grupo_codigo']}; pagina={row['pagina']}; modalidad={row['modalidad']}"
        values.append(f"(gen_random_uuid(),'260/75',{q(cat_code)},{q(name)},{order*10},true,{q(metadata)},'PUBLICADA_POR_PARTE_SIGNATARIA',true,1)")
    lines.append(",\n".join(values))
    lines.append("ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET nombre=EXCLUDED.nombre,orden=EXCLUDED.orden,activa=true,fuente=EXCLUDED.fuente,estado_fuente=EXCLUDED.estado_fuente,is_verified=true;")
    lines += ["", "-- Sustituye únicamente la carga incompleta del mismo período; no toca historia anterior.",
              "DELETE FROM public.escala_salarial WHERE cct_numero='260/75' AND valid_from=DATE '2026-08-01';", "",
              "INSERT INTO public.escala_salarial (id,cct_numero,categoria,basico,valid_from,valid_to,fuente,estado_fuente,is_verified,version,provisoria,zona,unidad_escala,habilitada_liquidacion) VALUES"]
    scale_values = []
    for _, name, _, row in normalized:
        amount = row["valores"]["2026-08-01"]
        source = f"{SOURCE}; grupo={row['grupo_codigo']}; pagina={row['pagina']}"
        # El acta dispone aplicación efectiva desde la homologación. Al
        # 25/08/2026 ADIMRA publica acta/planillas, no el acto homologatorio.
        scale_values.append(f"(gen_random_uuid(),'260/75',{q(name)},{amount},DATE '2026-08-01',DATE '2026-08-31',{q(source)},'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,false,'',{q(row['modalidad'])},false)")
    lines.append(",\n".join(scale_values) + ";")

    lines += ["", "DELETE FROM public.parametro_legal WHERE cct_numero='260/75' AND valid_from=DATE '2026-08-01';",
              "", "INSERT INTO public.parametro_legal (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,is_verified,version,cct_numero,incidencias) VALUES"]
    param_values = []
    for row in imgr:
        c = code("IMGR", row["grupo_codigo"])
        inc = json.dumps({"tipo": "garantia_ingreso", "grupo": row["grupo_codigo"], "excluye": ["horas_extra"]}, ensure_ascii=False, separators=(",", ":"))
        param_values.append(f"(gen_random_uuid(),{q(c)},{row['valores']['2026-08-01']},'ARS','variable',DATE '2026-08-01',DATE '2026-08-31',{q(SOURCE)},'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,'260/75',{q(inc)}::jsonb)")
    for row in additions:
        c = code("UOM_ADIC", row["grupo_codigo"], row["etiqueta"])
        inc = json.dumps({"tipo": "adicional_variable", "grupo": row["grupo_codigo"], "modalidad": row["modalidad"], "pagina": row["pagina"]}, ensure_ascii=False, separators=(",", ":"))
        param_values.append(f"(gen_random_uuid(),{q(c)},{row['valores']['2026-08-01']},'ARS','variable',DATE '2026-08-01',DATE '2026-08-31',{q(SOURCE)},'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,'260/75',{q(inc)}::jsonb)")
    fixed = [
        ("GRATIFICACION_NR_UOM_2026_08", "30000", "ARS", "no_remunerativo", AGREEMENT,
         {"tipo": "gratificacion_extraordinaria", "regla_jornada": "proporcional", "base_sac": True, "base_obra_social": True, "base_sindical": True}),
        ("COMPENSACION_ABR_JUL_UOM_CUOTA1", "70000", "ARS", "no_remunerativo", AGREEMENT,
         {"tipo": "compensacion_extraordinaria", "requiere_contrato_31_07": True, "dias_periodo": 122, "absorbe_pagos_cuenta": True, "base_obra_social": True, "base_sindical": True}),
        ("SEGURO_VIDA_SEPELIO_UOM_TRAB", "8045.65", "ARS", "ded_todos", INSURANCE,
         {"tipo": "seguro_vida_sepelio", "parte": "trabajador"}),
        ("SEGURO_VIDA_SEPELIO_UOM_EMP", "8045.65", "ARS", "contrib_emp", INSURANCE,
         {"tipo": "seguro_vida_sepelio", "parte": "empleador"}),
    ]
    for codigo, valor, unidad, ambito, fuente, incidencias in fixed:
        inc = json.dumps(incidencias, ensure_ascii=False, separators=(",", ":"))
        param_values.append(f"(gen_random_uuid(),{q(codigo)},{valor},{q(unidad)},{q(ambito)},DATE '2026-08-01',DATE '2026-08-31',{q(fuente)},'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,'260/75',{q(inc)}::jsonb)")
    lines.append(",\n".join(param_values) + ";")
    lines += ["", "INSERT INTO public.cct_regla_estructural (id,cct_numero,codigo,tipo,descripcion,articulo,configuracion,fuente,estado_fuente,is_verified,version,activa) VALUES"]
    groups = []
    for group_code, group_name in sorted({(r["grupo_codigo"], r["grupo_nombre"]) for r in data["filas"]}):
        config = json.dumps({"grupo": group_code, "requiere_seleccion_explicita": True, "categorias": sum(r["grupo_codigo"] == group_code and r["tipo"] == "CATEGORIA" for r in data["filas"])}, ensure_ascii=False, separators=(",", ":"))
        groups.append(f"(gen_random_uuid(),'260/75',{q('RAMA_'+group_code)},'rama',{q(group_name)},'Anexo I',{q(config)}::jsonb,{q(SOURCE)},'PUBLICADA_POR_PARTE_SIGNATARIA',true,1,true)")
    lines.append(",\n".join(groups))
    lines.append("ON CONFLICT (cct_numero,codigo,version) DO UPDATE SET descripcion=EXCLUDED.descripcion,configuracion=EXCLUDED.configuracion,fuente=EXCLUDED.fuente,estado_fuente=EXCLUDED.estado_fuente,is_verified=true,activa=true;")
    lines += ["", "COMMIT;", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: compilar_uom_sql.py ENTRADA.json SALIDA.sql")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    Path(sys.argv[2]).write_text(compile_sql(data), encoding="utf-8")
