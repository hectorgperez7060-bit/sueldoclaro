"""Recibo de haberes A4.

Requisitos legales que el documento debe satisfacer:

- LCT arts. 139 y 140 (texto vigente según Ley 27.802): doble ejemplar, constancia
  de recepción de la copia y contenido mínimo del recibo — datos del empleador y
  del trabajador, período, remuneración, deducciones, fecha y lugar de pago.
- Ley 17.250 art. 12: el recibo debe informar el **último depósito** de aportes y
  contribuciones, indicando **fecha, período y banco o entidad**. Tres datos, no uno.

Reglas de construcción:

- Nada se trunca. Si un texto no entra, se achica hasta un piso legible y, si aún
  no entra, se parte en dos renglones. Un domicilio cortado con "..." no cumple.
- Nada se inventa. Un dato ausente se muestra como "No informado" y los datos del
  último depósito, si faltan, se declaran pendientes.
- El PDF descargado queda listo para firma y entrega. Mientras no exista firma
  o aceptación acreditada, lo informa sin convertir al contador en requisito.
- Un importe pendiente nunca se muestra como $ 0,00: se muestra como pendiente.
- Los porcentajes del gráfico se derivan de los mismos importes mostrados y su
  redondeo visible suma exactamente 100,0 %.
"""
from __future__ import annotations

import math
import re
from decimal import Decimal, ROUND_FLOOR
from io import BytesIO
from typing import Any, Iterable

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

GREEN, PALE = HexColor("#087F73"), HexColor("#E7F5F2")
DARK, GRAY, LINE = HexColor("#111827"), HexColor("#4B5563"), HexColor("#6B7280")
AMBER_BG, AMBER_LINE, AMBER_INK = Color(1, .96, .80), Color(.85, .55, 0), Color(.50, .28, 0)

NO_INFORMADO = "No informado"
DEPOSITO_PENDIENTE = "Datos del último depósito pendientes de completar"
PARA_FIRMA = "EMITIDO POR EL EMPLEADOR — PENDIENTE DE FIRMA Y CONSTANCIA DE ENTREGA"
REVISION_OPCIONAL = "REVISIÓN PROFESIONAL OPCIONAL"
GRUPO_ART = "ART"
ART_PENDIENTE = "ART pendiente de contrato/cálculo"
SUBTOTAL_SIN_ART = "Subtotal conocido del costo laboral — ART pendiente"
COSTO_CON_ART = "Costo laboral con ART incluida"
GRUPO_SINDICAL = "Sindical"
GRUPO_SINDICAL_RUBRO = "Sindical"


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _money(value: Any) -> str:
    raw = f"{_decimal(value):,.2f}"
    return "$ " + raw.replace(",", "X").replace(".", ",").replace("X", ".")


def _date_display(value: Any) -> str:
    text = str(value or "")
    match = re.fullmatch(r"(\d{4})[-/](\d{2})[-/](\d{2})", text)
    return f"{match[3]}/{match[2]}/{match[1]}" if match else text


_UNITS = ("", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve")
_SPECIAL = {10: "diez", 11: "once", 12: "doce", 13: "trece", 14: "catorce", 15: "quince",
            16: "dieciseis", 17: "diecisiete", 18: "dieciocho", 19: "diecinueve",
            20: "veinte", 21: "veintiuno", 22: "veintidos", 23: "veintitres",
            24: "veinticuatro", 25: "veinticinco", 26: "veintiseis", 27: "veintisiete",
            28: "veintiocho", 29: "veintinueve"}
_TENS = ("", "", "", "treinta", "cuarenta", "cincuenta", "sesenta", "setenta", "ochenta", "noventa")
_HUNDREDS = ("", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos",
             "seiscientos", "setecientos", "ochocientos", "novecientos")


def _under_thousand(n: int) -> str:
    if not n:
        return ""
    if n == 100:
        return "cien"
    parts: list[str] = []
    if n >= 100:
        parts.append(_HUNDREDS[n // 100]); n %= 100
    if n in _SPECIAL:
        parts.append(_SPECIAL[n])
    elif n >= 30:
        parts.append(_TENS[n // 10] + ((" y " + _UNITS[n % 10]) if n % 10 else ""))
    elif n:
        parts.append(_UNITS[n])
    return " ".join(parts)


def _integer_words(n: int) -> str:
    if n == 0:
        return "cero"
    if n >= 1_000_000_000:
        q, r = divmod(n, 1_000_000_000)
        return (("mil millones" if q == 1 else _integer_words(q) + " mil millones") + " " + _integer_words(r)).strip()
    if n >= 1_000_000:
        q, r = divmod(n, 1_000_000)
        return (("un millon" if q == 1 else _integer_words(q) + " millones") + " " + _integer_words(r)).strip()
    if n >= 1000:
        q, r = divmod(n, 1000)
        return (("mil" if q == 1 else _under_thousand(q) + " mil") + " " + _under_thousand(r)).strip()
    return _under_thousand(n)


def _money_words(value: Any) -> str:
    amount = _decimal(value); pesos = int(amount); cents = int((amount - pesos) * 100)
    return f"Pesos {_integer_words(pesos)} con {cents:02d}/100"


def _require(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for key in path.split("."):
        current = current.get(key) if isinstance(current, dict) else None
    if current is None or str(current).strip() == "":
        raise ValueError(f"Falta el dato obligatorio del recibo: {path}")
    return current


def _dato(data: dict[str, Any], path: str, defecto: str = NO_INFORMADO) -> str:
    """Valor declarado o "No informado". Nunca completa por su cuenta."""
    current: Any = data
    for key in path.split("."):
        current = current.get(key) if isinstance(current, dict) else None
    text = str(current or "").strip()
    return text or defecto


def validar_datos_legales(data: dict[str, Any]) -> None:
    """Datos sin los cuales el recibo no puede emitirse (LCT arts. 139 y 140).

    Los datos del último depósito (Ley 17.250 art. 12) no bloquean la emisión:
    se declaran pendientes en el cuerpo del recibo para que quede a la vista.
    """
    for path in ("periodo", "empresa.razon_social", "empresa.cuit", "empresa.domicilio",
                 "empleado.apellido", "empleado.nombre", "empleado.cuil", "empleado.fecha_ingreso",
                 "empleado.categoria", "pago.fecha", "pago.lugar", "pago.forma"):
        _require(data, path)
    if not data.get("conceptos"):
        raise ValueError("El recibo no contiene conceptos liquidados")
    for index, concept in enumerate(data["conceptos"], 1):
        for field in ("descripcion", "tipo", "importe", "base_calculo", "unidad", "cantidad"):
            if concept.get(field) is None or str(concept.get(field)).strip() == "":
                raise ValueError(f"Concepto {index}: falta {field}")


# --------------------------------------------------------------------------- #
# Texto que siempre entra: primero achica, después parte en dos renglones.
# --------------------------------------------------------------------------- #
def _fit(value: Any, width: float, size: float, bold: bool = False) -> str:
    """Compatibilidad histórica: devuelve el texto sin recortar.

    El ajuste real lo hace ``_draw_fit``; esta función ya no trunca con "...".
    """
    return str(value or "-")


def _wrap(text: str, width: float, font: str, size: float, max_lines: int) -> list[str]:
    palabras, lineas, actual = text.split(), [], ""
    for palabra in palabras:
        tentativa = f"{actual} {palabra}".strip()
        if stringWidth(tentativa, font, size) <= width or not actual:
            actual = tentativa
        else:
            lineas.append(actual)
            actual = palabra
            if len(lineas) == max_lines:
                break
    if actual and len(lineas) < max_lines:
        lineas.append(actual)
    return lineas or [text]


def _draw_fit(c: Canvas, x: float, y: float, value: Any, width: float, size: float,
              bold: bool = False, color: Color = DARK, min_size: float = 4.6,
              max_lines: int = 2, leading: float | None = None) -> float:
    """Dibuja ``value`` sin truncar. Devuelve el alto ocupado."""
    text = str(value if value not in (None, "") else "-")
    font = "Helvetica-Bold" if bold else "Helvetica"
    actual = size
    while stringWidth(text, font, actual) > width and actual > min_size:
        actual -= .15
    c.setFillColor(color)
    if stringWidth(text, font, actual) <= width:
        c.setFont(font, actual); c.drawString(x, y, text)
        return actual
    lineas = _wrap(text, width, font, actual, max_lines)
    salto = leading or actual + .6
    for indice, linea in enumerate(lineas):
        c.setFont(font, actual)
        c.drawString(x, y - indice * salto, linea)
    return salto * len(lineas)


def _text(c: Canvas, x: float, y: float, value: Any, size: float = 7, bold: bool = False,
          color: Color = DARK, right: bool = False) -> None:
    c.setFillColor(color); c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    (c.drawRightString if right else c.drawString)(x, y, str(value))


def _section(c: Canvas, y: float, title: str) -> float:
    c.setFillColor(GREEN); c.setStrokeColor(GREEN); c.rect(24, y - 14, 547, 17, fill=1, stroke=1)
    _text(c, 30, y - 9, title, 8, True, white)
    return y - 20


def _unit(value: Any) -> str:
    text = str(value or "")
    divisor = re.fullmatch(r"1/(\d+(?:\.\d+)?)", text.strip())
    if divisor and Decimal(divisor.group(1)) != 0:
        porcentaje = Decimal("100") / Decimal(divisor.group(1))
        visible = format(porcentaje.quantize(Decimal("0.01")), "f").rstrip("0").rstrip(".")
        return visible.replace(".", ",") + "%"
    if "%" in text:
        try:
            raw_number, suffix = text.split("%", 1)
            number = format(Decimal(raw_number), "f")
            if "." in number:
                number = number.rstrip("0").rstrip(".")
            number = number.replace(".", ",")
            return f"{number or '0'}%{suffix}"
        except Exception:
            return text
    return text


def _row(c: Canvas, y: float, row: dict[str, Any], size: float, height: float, shaded: bool = False) -> float:
    bottom = y - height / 2
    if shaded:
        c.setFillColor(HexColor("#F3F4F6")); c.rect(28, bottom, 540, height, fill=1, stroke=0)
    _draw_fit(c, 32, y, row["descripcion"], 256, size, max_lines=1, min_size=4.2)
    _text(c, 370, y, _money(row["base_calculo"]), size, right=True)
    _draw_fit(c, 380, y, _unit(row["unidad"]), 84, size, max_lines=1, min_size=4.2)
    _text(c, 508, y, row["cantidad"], size, right=True)
    _text(c, 562, y, _money(row["importe"]), size, True, right=True)
    c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.line(28, bottom, 568, bottom)
    for x in (28, 292, 374, 466, 516, 568): c.line(x, bottom, x, bottom + height)
    return y - height


def _concept_band(c: Canvas, y: float, title: str) -> float:
    c.setFillColor(HexColor("#CDEBE5")); c.setStrokeColor(GREEN)
    c.rect(28, y - 5, 540, 13, fill=1, stroke=1)
    _text(c, 32, y - 1, title, 6.5, True, DARK)
    return y - 13


def _table_header(c: Canvas, y: float) -> float:
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(28, y - 5, 540, 15, fill=1, stroke=1)
    for x in (292, 374, 466, 516): c.line(x, y - 5, x, y + 10)
    for x, label in zip((32, 300, 380, 476, 522), ("Concepto", "Base", "Unidad", "Cant.", "Monto")):
        _text(c, x, y, label, 6.5, True, DARK)
    return y - 15


# --------------------------------------------------------------------------- #
# Clasificación del costo laboral. Se resuelve por metadatos del concepto,
# nunca por el nombre de un gremio en particular.
# --------------------------------------------------------------------------- #
def _cost_group(row: dict[str, Any]) -> str:
    code = str(row.get("codigo", "")).lower()
    desc = str(row.get("descripcion", "")).lower()
    destino = str(row.get("destino_pago") or "").strip()
    boleta = str(row.get("codigo_boleta") or "").strip()

    if code.startswith(("cuota_art", "art_")) or "riesgos del trabajo" in desc or "a.r.t" in desc:
        return GRUPO_ART
    if "obra_social" in code or "obra social" in desc:
        return "Obra social"
    if "inssjp" in code or "inssjp" in desc:
        return "INSSJP"
    if any(word in desc for word in (
        "jubil", "asignaciones", "fondo de empleo", "seguridad social",
        "contribuciones patronales", "contribución patronal",
    )) or code.startswith(("contrib_jubilacion", "contrib_seg_social", "aporte_jubilacion")):
        return "Seguridad social"
    if "camara" in code or "cámara" in desc:
        return "Cámaras / entidades"
    # Metadatos de boleta: el concepto declara a quién y con qué boleta se paga.
    # Sirve para cualquier gremio (ADEF, FATSA, UOCRA…) sin nombrarlo en el código.
    if destino and boleta:
        return GRUPO_SINDICAL
    if any(word in code for word in ("sindical", "solidario", "faecys", "fatsa", "adef")):
        return GRUPO_SINDICAL
    return "Otros rubros"


def _destinos_sindicales(filas: Iterable[dict[str, Any]]) -> list[str]:
    """Entidades que cobran los aportes sindicales, tomadas de los metadatos."""
    destinos: list[str] = []
    for fila in filas:
        if _cost_group(fila) != GRUPO_SINDICAL:
            continue
        destino = str(fila.get("destino_pago") or "").strip()
        if destino and destino not in destinos:
            destinos.append(destino)
    return destinos


def _etiqueta_sindical(destinos: list[str]) -> str:
    """Rótulo del rubro sindical: el rubro del decreto más el destino real."""
    if not destinos:
        return "Aportes sindicales"
    return "Aportes sindicales / " + ", ".join(destinos)


# Rubros mínimos exigidos por el Anexo I, art. 5 del Decreto 407/2026. Se
# muestran siempre, aunque el importe sea cero: la norma pide la discriminación,
# no sólo los rubros con movimiento.
RUBROS_MINIMOS = (
    GRUPO_SINDICAL_RUBRO, "Seguridad social", "Obra social", "INSSJP",
    GRUPO_ART, "Cámaras / entidades", "Otros rubros",
)

_COLORES_COMPOSICION = (
    HexColor("#087F73"), HexColor("#2563EB"), HexColor("#F59E0B"),
    HexColor("#7C3AED"), HexColor("#DC2626"), HexColor("#0891B2"),
    HexColor("#65A30D"), HexColor("#6B7280"),
)


def _pie_chart(c: Canvas, cx: float, cy: float, radius: float,
               items: list[tuple[str, Decimal]]) -> None:
    """Torta de porciones. Sólo entran importes conocidos y ciertos.

    Un rubro pendiente no se dibuja como porción cero: quedaría representado
    como si no costara nada. Se informa aparte, debajo de la referencia.

    El porcentaje de cada porción se escribe una sola vez, en la referencia:
    repetirlo dentro de la porción duplica el dato y lo vuelve ilegible.
    """
    total = sum((amount for _, amount in items), Decimal("0")) or Decimal("1")
    angle = 90.0
    for index, (_, amount) in enumerate(items):
        fraction = float(amount / total)
        extent = fraction * 360
        if extent <= 0:
            continue
        c.setFillColor(_COLORES_COMPOSICION[index % len(_COLORES_COMPOSICION)])
        c.setStrokeColor(white); c.setLineWidth(.5)
        c.wedge(cx - radius, cy - radius, cx + radius, cy + radius, angle, extent,
                fill=1, stroke=1)
        angle += extent


def _porcentajes_visibles(items: list[tuple[str, Decimal]]) -> list[Decimal]:
    """Redondea a un decimal conservando una suma visible de 100,0 %."""
    total = sum((importe for _, importe in items), Decimal("0"))
    if total <= 0:
        return [Decimal("0.0") for _ in items]
    exactos = [importe * Decimal("1000") / total for _, importe in items]
    decimas = [valor.to_integral_value(rounding=ROUND_FLOOR) for valor in exactos]
    faltantes = int(Decimal("1000") - sum(decimas))
    orden = sorted(range(len(items)), key=lambda i: exactos[i] - decimas[i], reverse=True)
    for indice in orden[:faltantes]:
        decimas[indice] += 1
    return [valor / Decimal("10") for valor in decimas]


def _composition_block(
    c: Canvas, top: float, neto: Decimal,
    worker: list[dict[str, Any]], contributions: list[dict[str, Any]],
) -> float:
    """Resumen de la composición del costo laboral (Decreto 407/2026, Anexo I art. 5).

    Tabla con los siete rubros mínimos y gráfico de porciones al costado. Los
    porcentajes salen de los mismos importes de la tabla: no se calculan aparte.
    """
    empleado = {rubro: Decimal("0") for rubro in RUBROS_MINIMOS}
    empleador = dict(empleado)
    deducciones = [r for r in worker if r["tipo"] == "deduccion"]
    for row in deducciones:
        empleado[_cost_group(row)] += _decimal(row["importe"])
    for row in contributions:
        empleador[_cost_group(row)] += _decimal(row["importe"])

    destinos = _destinos_sindicales(deducciones + contributions)
    art_calculada = (empleado[GRUPO_ART] + empleador[GRUPO_ART]) > 0

    x, ancho_tabla, row_h = 28, 330, 10.4
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.rect(x, top - 12, ancho_tabla, 14, fill=1, stroke=1)
    _text(c, x + 5, top - 8, "COMPOSICIÓN DEL COSTO LABORAL", 6.3, True)
    _text(c, x + 214, top - 8, "TRABAJADOR", 5.6, True, GRAY, True)
    _text(c, x + 270, top - 8, "EMPLEADOR", 5.6, True, GRAY, True)
    _text(c, x + 325, top - 8, "TOTAL", 5.6, True, GRAY, True)

    yy = top - 22
    subtotal = _decimal(neto)
    porciones: list[tuple[str, Decimal]] = [("Sueldo neto", _decimal(neto))]

    def fila(nombre: str, sombreada: bool, importe_emp: Decimal | None = None,
             importe_pat: Decimal | None = None, nota: str = "") -> None:
        nonlocal yy
        if sombreada:
            c.setFillColor(HexColor("#F3F4F6")); c.rect(x, yy - 3, ancho_tabla, row_h, fill=1, stroke=0)
        _draw_fit(c, x + 5, yy, nombre, 150, 5.8, max_lines=1, min_size=4.4)
        if nota:
            _draw_fit(c, x + 158, yy, nota, 168, 5.8, bold=True, color=AMBER_INK,
                      max_lines=1, min_size=4.6)
        else:
            _text(c, x + 214, yy, _money(importe_emp or 0), 5.8, right=True)
            _text(c, x + 270, yy, _money(importe_pat or 0), 5.8, right=True)
            _text(c, x + 325, yy, _money((importe_emp or 0) + (importe_pat or 0)), 5.8, True, right=True)
        c.setStrokeColor(LINE); c.line(x, yy - 3, x + ancho_tabla, yy - 3)
        yy -= row_h

    fila("Sueldo neto de bolsillo", False, _decimal(neto), Decimal("0"))
    for indice, rubro in enumerate(RUBROS_MINIMOS):
        sombreada = indice % 2 == 0
        if rubro == GRUPO_ART and not art_calculada:
            fila("A.R.T.", sombreada, nota=ART_PENDIENTE)
            continue
        nombre = rubro
        if rubro == GRUPO_SINDICAL_RUBRO:
            nombre = _etiqueta_sindical(destinos)
        elif rubro == GRUPO_ART:
            nombre = "A.R.T."
        importe_emp, importe_pat = empleado[rubro], empleador[rubro]
        total = importe_emp + importe_pat
        subtotal += total
        if total > 0:
            porciones.append((nombre, total))
        fila(nombre, sombreada, importe_emp, importe_pat)

    etiqueta = COSTO_CON_ART if art_calculada else SUBTOTAL_SIN_ART
    yy -= 3
    c.setFillColor(PALE); c.setStrokeColor(LINE)
    c.rect(x, yy - 16, ancho_tabla, 16, fill=1, stroke=1)
    _draw_fit(c, x + 5, yy - 11, etiqueta, 232, 6, bold=True, max_lines=1, min_size=4.8)
    _text(c, x + 325, yy - 11, _money(subtotal), 7, True, GREEN, True)
    c.setStrokeColor(LINE)
    c.rect(x, yy - 16, ancho_tabla, (top + 2) - (yy - 16), fill=0, stroke=1)

    # ----- Gráfico de porciones, a la derecha de la tabla -----
    alto_bloque = (top + 2) - (yy - 16)
    cx, cy = 410, top - alto_bloque / 2 + 4
    radio = min(38.0, max(24.0, alto_bloque / 2 - 12))
    _pie_chart(c, cx, cy, radio, porciones)
    ly = top - 10
    porcentajes = _porcentajes_visibles(porciones)
    for indice, (nombre, importe) in enumerate(porciones):
        c.setFillColor(_COLORES_COMPOSICION[indice % len(_COLORES_COMPOSICION)])
        c.rect(456, ly - 4, 5.5, 5.5, fill=1, stroke=0)
        _draw_fit(c, 465, ly - 3, nombre, 76, 5.2, max_lines=1, min_size=4.2)
        porcentaje = porcentajes[indice]
        _text(c, 566, ly - 3, f"{porcentaje:.1f}%".replace(".", ","), 5.2, True, right=True)
        ly -= 8.4
    if not art_calculada:
        _draw_fit(c, 456, ly - 3, "A.R.T.: pendiente, no incluida en las porciones",
                  110, 5, bold=True, color=AMBER_INK, max_lines=2, min_size=4.4)
    c.setStrokeColor(LINE)
    c.rect(x + ancho_tabla + 6, yy - 16, 540 - ancho_tabla - 6, alto_bloque, fill=0, stroke=1)
    return yy - 22


def _bloque_pago(c: Canvas, y: float, data: dict[str, Any]) -> float:
    """Datos del pago, cada uno en su campo (LCT art. 140)."""
    campos = (
        ("Período liquidado", str(data["periodo"])),
        ("Fecha efectiva de pago", _date_display(_dato(data, "pago.fecha"))),
        ("Forma de pago", _dato(data, "pago.forma")),
        ("Lugar o establecimiento de pago", _dato(data, "pago.lugar")),
        ("Domicilio del lugar de trabajo", _dato(data, "pago.domicilio_trabajo")),
        ("Establecimiento asignado", _dato(data, "pago.establecimiento")),
    )
    alto = 48
    c.setFillColor(white); c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.rect(28, y + 6 - alto, 540, alto, fill=1, stroke=1)
    _text(c, 34, y - 2, "PAGO DE ESTA REMUNERACIÓN", 6.2, True, GRAY)
    ancho_col, x0 = 180, 34
    for indice, (etiqueta, valor) in enumerate(campos):
        columna, renglon = indice % 3, indice // 3
        x = x0 + columna * ancho_col
        yy = y - 12 - renglon * 17
        _text(c, x, yy, etiqueta, 5.4, True, GRAY)
        _draw_fit(c, x, yy - 7.4, valor, ancho_col - 8, 6.6, max_lines=1, min_size=4.6)
    return y - alto - 4


def _bloque_deposito(c: Canvas, y: float, data: dict[str, Any]) -> float:
    """Último depósito de aportes y contribuciones (Ley 17.250 art. 12)."""
    cargas = data.get("cargas_sociales") or {}
    fecha = str(cargas.get("fecha") or "").strip()
    periodo = str(cargas.get("periodo") or "").strip()
    entidad = str(cargas.get("banco") or cargas.get("entidad") or cargas.get("lugar") or "").strip()
    completo = bool(fecha and periodo and entidad)

    alto = 32
    c.setFillColor(white if completo else AMBER_BG)
    c.setStrokeColor(LINE if completo else AMBER_LINE); c.setLineWidth(.35)
    c.rect(28, y + 6 - alto, 540, alto, fill=1, stroke=1)
    _text(c, 34, y - 2, "ÚLTIMO DEPÓSITO DE APORTES Y CONTRIBUCIONES · Ley 17.250 art. 12",
          6.2, True, GRAY if completo else AMBER_INK)
    if not completo:
        _draw_fit(c, 34, y - 14, DEPOSITO_PENDIENTE, 520, 7, bold=True,
                  color=AMBER_INK, max_lines=1, min_size=6)
        return y - alto - 4
    campos = (
        ("Fecha del último depósito", _date_display(fecha)),
        ("Período al que corresponde", periodo),
        ("Banco o entidad donde se depositó", entidad),
    )
    for indice, (etiqueta, valor) in enumerate(campos):
        x = 34 + indice * 180
        _text(c, x, y - 13, etiqueta, 5.4, True, GRAY)
        _draw_fit(c, x, y - 20.4, valor, 172, 6.6, max_lines=1, min_size=4.6)
    return y - alto - 4


def _bloque_firmas(c: Canvas, data: dict[str, Any], firma: dict[str, Any] | None,
                   tope: float) -> None:
    """Espacios de firma, fecha de recepción y constancia de copia fiel.

    ``tope`` es el borde inferior del último bloque: las observaciones se estiran
    hasta ahí para que la hoja no quede con un hueco en blanco.
    """
    alto = max(22.0, min(180.0, tope - 84))
    c.setFillColor(white); c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.rect(28, 84, 540, alto, fill=1, stroke=1)
    _text(c, 34, 84 + alto - 8, "OBSERVACIONES", 5.8, True, GRAY)

    c.setStrokeColor(GRAY)
    c.line(40, 62, 200, 62)
    _text(c, 40, 54, "Firma del empleador", 6.4, color=GRAY)
    c.line(215, 62, 375, 62)
    _text(c, 215, 54, "Firma o aceptación del trabajador", 6.4, color=GRAY)
    c.line(390, 62, 480, 62)
    _text(c, 390, 54, "Fecha de recepción", 6.4, color=GRAY)
    c.line(492, 62, 568, 62)
    _text(c, 492, 54, "Aclaración / DNI", 6.4, color=GRAY)

    _text(c, 40, 42,
          "Constancia de entrega: recibí copia fiel de este recibo (LCT arts. 139 y 140).",
          6.2, True, DARK)
    if firma:
        _draw_fit(c, 40, 33,
                  f"Firma registrada: {firma['tipo']} · {firma['verificacion']} · "
                  f"recepción {_date_display(firma['fecha_recepcion'])}",
                  520, 6, color=GRAY, max_lines=1, min_size=5)
    else:
        _draw_fit(c, 40, 33,
                  "Sin firma ni constancia de entrega registradas: este documento no "
                  "acredita la recepción del pago.", 520, 6, color=AMBER_INK,
                  max_lines=1, min_size=5)

    c.setFillColor(PALE); c.rect(20, 12, 555, 16, fill=1, stroke=0)
    _text(c, 297, 18,
          "Recibo confeccionado conforme a los artículos 139 y 140 de la LCT y al "
          "artículo 12 de la Ley 17.250", 6, color=GRAY, right=True)


def generar_recibo_pdf(data: dict[str, Any]) -> bytes:
    validar_datos_legales(data)
    output = BytesIO(); c = Canvas(output, pagesize=A4, pageCompression=1)
    c.setTitle(f"Recibo de haberes {data['periodo']}"); c.setAuthor(str(data["empresa"]["razon_social"]))
    concepts = list(data["conceptos"])
    contributions = [r for r in concepts if r["tipo"] == "contribucion"]
    worker = [r for r in concepts if r["tipo"] != "contribucion"]
    # La ruta pública genera el ejemplar para firma y entrega. Una firma válida deberá venir
    # de un registro persistido y verificado por el servidor, nunca del cuerpo
    # enviado por el navegador.
    firma = None

    # Encabezado documental compacto.
    c.setFillColor(GREEN); c.setStrokeColor(GREEN); c.rect(20, 808, 555, 25, fill=1, stroke=0)
    titulo = "RECIBO DE HABERES" if firma else "RECIBO DE HABERES · PARA FIRMA Y ENTREGA"
    _text(c, 28, 817, titulo, 9.2, True, white)
    _text(c, 567, 817, f"PERÍODO {data['periodo']}", 8, True, white, right=True)

    y = 800
    if not firma:
        c.setFillColor(AMBER_BG); c.setStrokeColor(AMBER_LINE)
        c.rect(24, y - 11, 547, 15, fill=1, stroke=1)
        _text(c, 297, y - 6, PARA_FIRMA, 6.8, True, AMBER_INK, right=True)
        y -= 17
    if not firma:
        c.setFillColor(PALE); c.setStrokeColor(GREEN)
        c.rect(24, y - 11, 547, 15, fill=1, stroke=1)
        _text(c, 297, y - 6, REVISION_OPCIONAL, 6.8, True, GREEN, right=True)
        y -= 17

    y = _section(c, y, "1. DATOS DEL EMPLEADOR, TRABAJADOR Y PAGO")
    e, w = data["empresa"], data["empleado"]
    left = (("Empleador", e["razon_social"]), ("CUIT", e["cuit"]),
            ("Domicilio legal", e["domicilio"]))
    worker_name = f"{w['nombre']} {w['apellido']}".strip().title()
    right = (("Trabajador", worker_name), ("CUIL / Legajo", f"{w['cuil']} / {w.get('legajo') or '-'}"),
             ("Ingreso / Antig.", f"{_date_display(w['fecha_ingreso'])} / {w.get('antiguedad') or '-'}"))
    # La jornada va escrita en el recibo: es el dato que explica por qué un básico
    # aparece prorrateado, y sin él el trabajador no puede controlar su propio sueldo.
    modalidad = w.get("modalidad_contrato") or NO_INFORMADO
    jornada = w.get("jornada") or ""
    extra = (("Categoría", w["categoria"]), ("CCT", w.get("cct_numero") or NO_INFORMADO),
             ("Modalidad / Jornada",
              f"{modalidad} / {jornada}" if jornada else modalidad))
    c.setFillColor(white); c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.rect(28, y - 46, 540, 52, fill=1, stroke=1)
    c.line(208, y - 46, 208, y + 6); c.line(388, y - 46, 388, y + 6)
    for columna, filas in enumerate((left, right, extra)):
        x = 34 + columna * 180
        for indice, (etiqueta, valor) in enumerate(filas):
            yy = y - 8 - indice * 14
            _text(c, x, yy, etiqueta, 5.4, True, GRAY)
            _draw_fit(c, x, yy - 7.4, valor, 168, 6.6, max_lines=1, min_size=4.4)
    y -= 56

    y = _bloque_pago(c, y, data)
    y = _bloque_deposito(c, y, data)

    # Alto de fila calculado con el espacio realmente disponible: se descuenta
    # todo lo que ocupa un alto fijo y el resto se reparte entre las líneas.
    bandas = sum(
        1 for _, tipo in (("", "remunerativo"), ("", "no_remunerativo"), ("", "deduccion"))
        if any(r["tipo"] == tipo for r in worker)
    )
    alto_composicion = 64 + (len(RUBROS_MINIMOS) + 1) * 10.4
    alto_fijo = (
        20 + 15 + 20        # sección 2: título, encabezado de tabla y total
        + 20 + 15 + 22      # sección 3: título, encabezado y caja bruto/descuentos
        + bandas * 13       # bandas de agrupación de conceptos
        + 20 + 40           # sección 4 (neto)
        + 20 + alto_composicion
    )
    # Los dos totales dejan media fila de aire cada uno: entran en la ecuación.
    disponible = y - 112 - alto_fijo - 6
    total_filas = len(contributions) + len(worker) + 1
    row_h = min(12.0, max(5.2, disponible / max(total_filas, 1)))
    font = min(7.0, max(4.2, row_h * .62))

    y = _section(c, y, "2. CONTRIBUCIONES Y CONCEPTOS A CARGO DEL EMPLEADOR")
    y = _table_header(c, y)
    for index, row in enumerate(contributions):
        y = _row(c, y, row, font, row_h, index % 2 == 1)
    total = sum((_decimal(r["importe"]) for r in contributions), Decimal("0"))
    y -= row_h / 2 + 3
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(365, y - 5, 203, 15, fill=1, stroke=1)
    _text(c, 375, y, "TOTAL EMPLEADOR", 6.7, True); _text(c, 558, y, _money(total), 7, True, DARK, True)
    y -= 20

    y = _section(c, y, "3. REMUNERACIÓN BRUTA, HABERES Y DEDUCCIONES")
    y = _table_header(c, y)
    grupos = (("REMUNERATIVOS", "remunerativo"), ("NO REMUNERATIVOS", "no_remunerativo"),
              ("DESCUENTOS", "deduccion"))
    shade = 0
    for titulo, tipo in grupos:
        rows = [r for r in worker if r["tipo"] == tipo]
        if not rows:
            continue
        y = _concept_band(c, y, titulo)
        for row in rows:
            y = _row(c, y, row, font, row_h, shade % 2 == 1); shade += 1
    y -= row_h / 2 + 3
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(28, y - 5, 540, 17, fill=1, stroke=1)
    _text(c, 38, y, f"SUELDO BRUTO: {_money(data['bruto'])}", 7, True)
    _text(c, 330, y, f"DESCUENTOS: {_money(data['total_deducciones'])}", 7, True)
    y -= 22

    y = _section(c, y, "4. SUELDO NETO")
    c.setFillColor(white); c.setStrokeColor(DARK); c.setLineWidth(1); c.rect(28, y - 28, 540, 35, fill=1, stroke=1)
    _text(c, 38, y - 7, "NETO A COBRAR", 8.5, True, DARK)
    _text(c, 558, y - 7, _money(data["neto"]), 11, True, GREEN, True)
    _draw_fit(c, 38, y - 21, _money_words(data["neto"]), 500, 6.5, bold=True, max_lines=1, min_size=5)
    y -= 40

    y = _section(c, y, "5. COMPOSICIÓN DEL COSTO LABORAL")
    y = _composition_block(c, y, _decimal(data["neto"]), worker, contributions)
    if y < 112:
        raise ValueError("El recibo excede una hoja A4; deben agruparse líneas equivalentes")
    _bloque_firmas(c, data, firma, y)
    c.showPage(); c.save(); return output.getvalue()
