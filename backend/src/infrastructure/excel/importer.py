"""Importación masiva de empleados desde .xlsx (openpyxl).

Valida fila por fila y reporta errores por fila sin abortar todo el archivo por
una fila mala (sección 5.2 del prompt).
"""
from __future__ import annotations

import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Tuple

from openpyxl import Workbook, load_workbook

from domain.value_objects.cuil import digito_verificador, es_cuil_valido

from domain.entities.jornada import HORAS_TOPE_LEY_11544, proporcion_jornada


def horas_jornada_de(horas_por_cct, cct_numero: str) -> Decimal:
    """Jornada completa del convenio de la fila; tope legal si no la declara."""
    valor = (horas_por_cct or {}).get(cct_numero)
    try:
        horas = Decimal(str(valor))
    except (ArithmeticError, TypeError, ValueError):
        return HORAS_TOPE_LEY_11544
    return horas if horas > 0 else HORAS_TOPE_LEY_11544


COLUMNAS = [
    "nombre", "apellido", "cuil", "fecha_ingreso", "cct_numero",
    "categoria", "legajo", "horas_semanales", "remuneracion_pactada",
    "afiliado_sindicato", "email",
]



def generar_cuil_valido_unico(dni_int: int, cuils_existentes: set[str], prefijo: str = "20") -> str:

    while True:
        diez_dig = f"{prefijo}{dni_int:08d}"
        dv = digito_verificador(diez_dig)
        if dv >= 0:
            c = f"{diez_dig}{dv}"
            if c not in cuils_existentes:
                return c
        dni_int += 1


def generar_plantilla(cuils_existentes: set[str] = None) -> bytes:
    cuils_existentes = cuils_existentes or set()
    cuil_sample = generar_cuil_valido_unico(12345678, cuils_existentes, "20")
    wb = Workbook()
    ws = wb.active
    ws.title = "empleados"
    ws.append(COLUMNAS)
    ws.append([
        "Juan", "Pérez", cuil_sample, "2021-07-01", "130/75",
        "Administrativo A", "0001", 48, "", "SI", "juan@ejemplo.com",
    ])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def generar_demo_excel(cuils_existentes: set[str] = None) -> bytes:
    cuils_existentes = cuils_existentes or set()
    c1 = generar_cuil_valido_unico(12345678, cuils_existentes, "20")
    c2 = generar_cuil_valido_unico(23456789, cuils_existentes, "27")

    wb = Workbook()
    ws = wb.active
    ws.title = "empleados"
    ws.append(COLUMNAS)
    # Fila 2: Válida 1 (CUIL no existe en nómina activa)
    ws.append(["Carlos", "Gómez", c1, "2021-07-01", "130/75", "Administrativo A", "0001", 48, "", "SI", "carlos@ejemplo.com"])
    # Fila 3: Válida 2 (CUIL no existe en nómina activa)
    ws.append(["María", "López", c2, "2022-03-15", "130/75", "Vendedor B", "0002", 30, "", "NO", "maria@ejemplo.com"])
    # Fila 4: Error - CUIL repetido dentro del mismo Excel
    ws.append(["Carlos", "Gómez Duplicado", c1, "2021-07-01", "130/75", "Administrativo A", "0003", 48, "", "SI", ""])
    # Fila 5: Error - CUIL inválido
    ws.append(["Pedro", "Mendoza", "20999999999", "2023-01-10", "130/75", "Maestranza A", "0004", 48, "", "SI", ""])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()






def _a_fecha(valor) -> date:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), "%Y-%m-%d").date()


def parsear(contenido: bytes, cuils_existentes: set[str] = None,
            horas_por_cct: dict = None) -> Tuple[List[dict], List[dict]]:
    """Devuelve (empleados_validos, errores_por_fila).

    ``horas_por_cct`` trae las horas de jornada completa declaradas por cada
    convenio. La proporción de jornada se calcula contra la jornada del convenio
    de esa fila, no contra 48 fijas: en un convenio de 44 horas, 44 horas son
    jornada completa y prorratear contra 48 le recortaría el sueldo.
    """
    wb = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    ws = wb.active
    filas = list(ws.iter_rows(values_only=True))
    validos: List[dict] = []
    errores: List[dict] = []
    if not filas:
        return validos, errores

    encabezado = [str(c).strip().lower() if c is not None else "" for c in filas[0]]
    idx = {col: encabezado.index(col) for col in COLUMNAS if col in encabezado}

    faltantes = [c for c in ("nombre", "apellido", "cuil", "fecha_ingreso", "cct_numero", "categoria") if c not in idx]
    if faltantes:
        return validos, [{"fila": 1, "errores": [f"Faltan columnas obligatorias: {', '.join(faltantes)}"]}]

    cuils_vistos_excel: set[str] = set()
    cuils_existentes = cuils_existentes or set()

    for n, fila in enumerate(filas[1:], start=2):
        def val(col):
            i = idx.get(col)
            return fila[i] if (i is not None and i < len(fila)) else None

        errs: List[str] = []
        cuil = str(val("cuil") or "").replace("-", "").strip()
        if not es_cuil_valido(cuil):
            errs.append(f"CUIL inválido: {val('cuil')!r}")
        else:
            if cuil in cuils_vistos_excel:
                errs.append(f"CUIL {cuil} repetido dentro del mismo archivo Excel")
            else:
                cuils_vistos_excel.add(cuil)

            if cuil in cuils_existentes:
                errs.append(f"CUIL {cuil} ya existe registrado en la nómina activa")

        try:
            fecha_ing = _a_fecha(val("fecha_ingreso"))
        except (ValueError, TypeError):
            fecha_ing = None
            errs.append(f"fecha_ingreso inválida: {val('fecha_ingreso')!r} (usar YYYY-MM-DD)")

        for req in ("nombre", "apellido", "cct_numero", "categoria"):
            if not str(val(req) or "").strip():
                errs.append(f"Campo obligatorio vacío: {req}")

        rem = val("remuneracion_pactada")
        rem_dec = None
        if rem not in (None, ""):
            try:
                rem_dec = Decimal(str(rem))
            except (InvalidOperation, ValueError):
                errs.append(f"remuneracion_pactada inválida: {rem!r}")

        cct_fila = str(val("cct_numero") or "").strip()
        horas_completas = horas_jornada_de(horas_por_cct, cct_fila)
        try:
            horas_semanales = Decimal(str(val("horas_semanales") or horas_completas))
            proporcion = proporcion_jornada(horas_semanales, horas_completas)
        except (InvalidOperation, ValueError) as exc:
            horas_semanales = horas_completas
            proporcion = Decimal("1")
            errs.append(str(exc) if isinstance(exc, ValueError) and str(exc)
                        else f"horas_semanales inválidas para el convenio {cct_fila}")

        nom = str(val("nombre") or "").strip()
        ape = str(val("apellido") or "").strip()

        if errs:
            errores.append({"fila": n, "nombre": f"{ape}, {nom}".strip(", "), "cuil": cuil, "errores": errs})
            continue

        afil = str(val("afiliado_sindicato") or "SI").strip().upper()
        validos.append({
            "fila": n,
            "nombre": nom,
            "apellido": ape,
            "cuil": cuil,
            "fecha_ingreso": fecha_ing,
            "cct_numero": str(val("cct_numero")).strip(),
            "categoria": str(val("categoria")).strip(),
            "legajo": str(val("legajo") or "").strip(),
            "remuneracion_pactada": rem_dec,
            "proporcion_jornada": proporcion,
            "afiliado_sindicato": afil in ("SI", "S", "TRUE", "1", "X"),
            "email": (str(val("email")).strip() or None) if val("email") else None,
        })

    return validos, errores
