"""Interpretación tolerante de los encabezados de un Excel de empleados.

El importador original exigía que la primera fila dijera exactamente
``nombre, apellido, cuil, fecha_ingreso, cct_numero, categoria``. Cualquier
planilla real del estudio contable fallaba entera: ``Categoría`` con tilde,
``CUIL/CUIT``, ``Fecha de ingreso``, ``Apellido y Nombre`` en una sola celda.

Este módulo traduce el encabezado que trae el archivo a las columnas canónicas
del sistema y explica cómo interpretó cada una, para que la app pueda mostrarle
al usuario qué entendió antes de importar nada.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from typing import Dict, List, Tuple

# Columnas canónicas que entiende el importador.
CANONICAS = (
    "nombre", "apellido", "cuil", "fecha_ingreso", "cct_numero",
    "categoria", "legajo", "horas_semanales", "remuneracion_pactada",
    "afiliado_sindicato", "email",
)

# Columna virtual: una sola celda que trae apellido y nombre juntos.
NOMBRE_COMPLETO = "nombre_completo"

OBLIGATORIAS = ("nombre", "apellido", "cuil", "fecha_ingreso", "cct_numero", "categoria")

# Sinónimos aceptados por columna, ya normalizados (sin tildes, en minúscula,
# separadores unificados como espacio simple).
SINONIMOS: Dict[str, Tuple[str, ...]] = {
    "nombre": (
        "nombre", "nombres", "nombre de pila", "primer nombre",
        "nombre del empleado", "nombre empleado", "nombre trabajador",
    ),
    "apellido": (
        "apellido", "apellidos", "apellido paterno", "apellido del empleado",
        "apellido empleado", "apellido trabajador",
    ),
    NOMBRE_COMPLETO: (
        "apellido y nombre", "apellido y nombres", "apellido nombre",
        "apellido, nombre", "nombre y apellido", "nombre y apellidos",
        "nombre completo", "apellido y nombre del empleado", "empleado",
        "trabajador", "agente", "datos del empleado",
    ),
    "cuil": (
        "cuil", "cuit", "cuil cuit", "cuil/cuit", "nro cuil", "numero de cuil",
        "n cuil", "cuil nro", "cuil del empleado", "clave unica",
        "clave unica de identificacion laboral",
    ),
    "fecha_ingreso": (
        "fecha ingreso", "fecha de ingreso", "ingreso", "alta",
        "fecha de alta", "fecha alta", "f ingreso", "fec ingreso",
        "fecha de ingreso al empleo", "antiguedad desde", "desde",
    ),
    # El primer puñado de cada lista es lo que se le sugiere al usuario cuando
    # falta la columna, así que van adelante los títulos más habituales.
    "cct_numero": (
        "convenio", "cct", "gremio", "numero de convenio",
        "cct numero", "n convenio", "nro convenio", "convenio colectivo",
        "cct nro", "sindicato", "encuadre", "encuadramiento",
    ),
    "categoria": (
        "categoria", "puesto", "cargo", "categoria del convenio",
        "categoria laboral", "cat", "categoria cct", "funcion",
        "categoria convenio",
    ),
    "legajo": (
        "legajo", "nro legajo", "numero de legajo", "n legajo", "leg",
        "codigo empleado", "id empleado", "interno",
    ),
    "horas_semanales": (
        "horas semanales", "horas", "hs semanales", "hs", "jornada",
        "horas por semana", "carga horaria", "hs sem", "jornada semanal",
        "horas semana",
    ),
    "remuneracion_pactada": (
        "remuneracion pactada", "remuneracion", "sueldo", "sueldo pactado",
        "sueldo basico", "basico", "sueldo bruto", "haber", "haberes",
        "importe", "sueldo acordado", "remuneracion acordada",
        "sueldo de bolsillo", "salario",
    ),
    "afiliado_sindicato": (
        "afiliado sindicato", "afiliado", "afiliado al sindicato",
        "afiliacion", "afiliado gremio", "cuota sindical",
        "aporte sindical", "sindicalizado", "afiliado si no",
    ),
    "email": (
        "email", "e mail", "correo", "correo electronico", "mail",
        "direccion de correo", "correo del empleado",
    ),
}

# Umbral del cotejo aproximado. Alto a propósito: preferimos avisar que no
# reconocimos una columna antes que adivinar mal y liquidar con datos de otra.
UMBRAL_APROXIMADO = 0.86


def normalizar(texto) -> str:
    """Deja el encabezado comparable: sin tildes, sin puntuación, en minúscula."""
    if texto is None:
        return ""
    s = str(texto).strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("ñ", "n")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# Índice inverso normalizado: sinónimo -> columna canónica.
_INDICE: Dict[str, str] = {}
for _canonica, _variantes in SINONIMOS.items():
    _INDICE[normalizar(_canonica)] = _canonica
    for _v in _variantes:
        _INDICE.setdefault(normalizar(_v), _canonica)


def _match_aproximado(clave: str) -> str | None:
    if len(clave) < 3:
        return None
    cercanos = difflib.get_close_matches(clave, _INDICE.keys(), n=1, cutoff=UMBRAL_APROXIMADO)
    return _INDICE[cercanos[0]] if cercanos else None


def detectar_mapeo(encabezado: List) -> Tuple[Dict[str, int], List[dict], List[str]]:
    """Traduce el encabezado del archivo a columnas canónicas.

    Devuelve ``(indices, interpretacion, sin_reconocer)`` donde:

    - ``indices`` mapea columna canónica -> posición en la fila.
    - ``interpretacion`` describe, columna por columna, qué se entendió y cómo
      (``exacto``, ``sinonimo`` o ``aproximado``), para mostrárselo al usuario.
    - ``sin_reconocer`` lista los encabezados que se ignoraron.
    """
    indices: Dict[str, int] = {}
    interpretacion: List[dict] = []
    sin_reconocer: List[str] = []

    for posicion, bruto in enumerate(encabezado):
        clave = normalizar(bruto)
        if not clave:
            continue

        canonica = _INDICE.get(clave)
        modo = "exacto" if canonica and clave == normalizar(canonica) else "sinonimo"
        if canonica is None:
            canonica = _match_aproximado(clave)
            modo = "aproximado"

        if canonica is None:
            sin_reconocer.append(str(bruto).strip())
            continue

        if canonica in indices:
            # Dos columnas apuntan a lo mismo: nos quedamos con la primera y
            # avisamos, en lugar de pisar en silencio.
            sin_reconocer.append(str(bruto).strip())
            continue

        indices[canonica] = posicion
        interpretacion.append({
            "columna_archivo": str(bruto).strip(),
            "interpretada_como": canonica,
            "modo": modo,
        })

    return indices, interpretacion, sin_reconocer


def partir_nombre_completo(valor, encabezado_original: str = "") -> Tuple[str, str]:
    """Separa una celda tipo "Pérez, Juan" o "Pérez Juan" en (apellido, nombre).

    Con coma, lo de antes de la coma es el apellido: es la forma en que las
    planillas de sueldos escriben la nómina. Sin coma, decide según lo que diga
    el encabezado; ante la duda usa el orden "apellido primero", que es el más
    frecuente en liquidación.
    """
    texto = re.sub(r"\s+", " ", str(valor or "").strip())
    if not texto:
        return "", ""

    if "," in texto:
        izquierda, _, derecha = texto.partition(",")
        return izquierda.strip(), derecha.strip()

    partes = texto.split(" ")
    if len(partes) == 1:
        return partes[0], ""

    cabecera = normalizar(encabezado_original)
    nombre_primero = cabecera.startswith("nombre") and "apellido" in cabecera
    if nombre_primero or cabecera.startswith("nombre completo"):
        # "Juan Pérez" -> apellido es lo último.
        return partes[-1], " ".join(partes[:-1])
    # "Pérez Juan" -> apellido es lo primero.
    return partes[0], " ".join(partes[1:])
