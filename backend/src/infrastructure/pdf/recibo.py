"""Recibo A4 conforme al Anexo III del Decreto 407/2026."""
from __future__ import annotations

import math
import re
from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

GREEN, PALE = HexColor("#087F73"), HexColor("#E5E7EB")
DARK, GRAY, LINE = HexColor("#111827"), HexColor("#4B5563"), HexColor("#6B7280")


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


def validar_datos_legales(data: dict[str, Any]) -> None:
    for path in ("periodo", "empresa.razon_social", "empresa.cuit", "empresa.domicilio",
                 "empleado.apellido", "empleado.nombre", "empleado.cuil", "empleado.fecha_ingreso",
                 "empleado.categoria", "pago.fecha", "pago.lugar", "pago.forma",
                 "cargas_sociales.fecha", "cargas_sociales.lugar"):
        _require(data, path)
    if not data.get("conceptos"):
        raise ValueError("El recibo no contiene conceptos liquidados")
    for index, concept in enumerate(data["conceptos"], 1):
        for field in ("descripcion", "tipo", "importe", "base_calculo", "unidad", "cantidad"):
            if concept.get(field) is None or str(concept.get(field)).strip() == "":
                raise ValueError(f"Concepto {index}: falta {field}")


def _fit(value: Any, width: float, size: float, bold: bool = False) -> str:
    text, font = str(value or "-"), "Helvetica-Bold" if bold else "Helvetica"
    if stringWidth(text, font, size) <= width:
        return text
    while text and stringWidth(text + "...", font, size) > width:
        text = text[:-1]
    return text + "..."


def _text(c: Canvas, x: float, y: float, value: Any, size: float = 7, bold: bool = False,
          color: Color = DARK, right: bool = False) -> None:
    c.setFillColor(color); c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    (c.drawRightString if right else c.drawString)(x, y, str(value))


def _section(c: Canvas, y: float, title: str) -> float:
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(24, y - 14, 547, 17, fill=1, stroke=1)
    _text(c, 30, y - 9, title, 8, True, DARK)
    return y - 20


def _unit(value: Any) -> str:
    text = str(value or "")
    if re.fullmatch(r"1/12(?:\.0+)?", text.strip()):
        return "8,33%"
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
    _text(c, 32, y, _fit(row["descripcion"], 250, size), size)
    _text(c, 370, y, _money(row["base_calculo"]), size, right=True)
    _text(c, 380, y, _fit(_unit(row["unidad"]), 86, size), size)
    _text(c, 508, y, row["cantidad"], size, right=True)
    _text(c, 562, y, _money(row["importe"]), size, True, right=True)
    c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.line(28, bottom, 568, bottom)
    for x in (28, 292, 374, 466, 516, 568): c.line(x, bottom, x, bottom + height)
    return y - height


def _concept_band(c: Canvas, y: float, title: str) -> float:
    c.setFillColor(HexColor("#D1D5DB")); c.setStrokeColor(LINE)
    c.rect(28, y - 5, 540, 13, fill=1, stroke=1)
    _text(c, 32, y - 1, title, 6.5, True, DARK)
    return y - 13


def _table_header(c: Canvas, y: float) -> float:
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(28, y - 5, 540, 15, fill=1, stroke=1)
    for x in (292, 374, 466, 516): c.line(x, y - 5, x, y + 10)
    for x, label in zip((32, 300, 380, 476, 522), ("Concepto", "Base", "Unidad", "Cant.", "Monto")):
        _text(c, x, y, label, 6.5, True, DARK)
    return y - 15


def _cost_group(row: dict[str, Any]) -> str:
    code, desc = str(row.get("codigo", "")).lower(), str(row.get("descripcion", "")).lower()
    if "sind" in code or "fatsa" in desc or "faecys" in desc: return "Sindical"
    if "obra_social" in code or "obra social" in desc: return "Obra social"
    if "inssjp" in code or "inssjp" in desc: return "INSSJP"
    if "art" in code or "a.r.t" in desc: return "ART"
    if "camara" in code or "cámara" in desc: return "Cámaras / entidades"
    if any(word in desc for word in (
        "jubil", "asignaciones", "fondo de empleo", "seguridad social",
        "contribuciones patronales", "contribución patronal",
    )): return "Seguridad social"
    return "Otros rubros"


_COMPOSITION_COLORS = (
    HexColor("#087F73"), HexColor("#2563EB"), HexColor("#F59E0B"),
    HexColor("#7C3AED"), HexColor("#DC2626"), HexColor("#0891B2"),
    HexColor("#65A30D"), HexColor("#6B7280"),
)


def _pie_chart(
    c: Canvas, cx: float, cy: float, radius: float,
    items: list[tuple[str, Decimal]],
) -> None:
    total = sum((amount for _, amount in items), Decimal("0")) or Decimal("1")
    angle = 90.0
    for index, (label, amount) in enumerate(items):
        fraction = float(amount / total)
        extent = fraction * 360
        if extent <= 0:
            continue
        c.setFillColor(_COMPOSITION_COLORS[index % len(_COMPOSITION_COLORS)])
        c.setStrokeColor(white); c.setLineWidth(.5)
        c.wedge(cx - radius, cy - radius, cx + radius, cy + radius, angle, extent, fill=1, stroke=1)
        if fraction >= .045:
            middle = math.radians(angle + extent / 2)
            x = cx + math.cos(middle) * radius * .62
            y = cy + math.sin(middle) * radius * .62 - 2
            _text(c, x + 8, y, f"{fraction * 100:.1f}%".replace(".", ","), 5.2, True, white, True)
        angle += extent


def _composition_block(
    c: Canvas, top: float, neto: Decimal,
    worker: list[dict[str, Any]], contributions: list[dict[str, Any]],
) -> float:
    employee = {name: Decimal("0") for name in ("Sindical", "Seguridad social", "Obra social", "INSSJP", "ART", "Cámaras / entidades", "Otros rubros")}
    employer = dict(employee)
    for row in worker:
        if row["tipo"] == "deduccion": employee[_cost_group(row)] += _decimal(row["importe"])
    for row in contributions:
        employer[_cost_group(row)] += _decimal(row["importe"])

    x, width, row_h = 28, 326, 10.2
    c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.setFillColor(PALE); c.rect(x, top - 12, width, 14, fill=1, stroke=1)
    _text(c, x + 5, top - 8, "DETALLE DE LA COMPOSICIÓN SALARIAL", 6.5, True)
    _text(c, x + 210, top - 8, "TRABAJADOR", 5.7, True)
    _text(c, x + 278, top - 8, "EMPLEADOR", 5.7, True)
    yy = top - 21
    for index, name in enumerate(employee):
        if index % 2:
            c.setFillColor(HexColor("#F3F4F6")); c.rect(x, yy - 3, width, row_h, fill=1, stroke=0)
        _text(c, x + 5, yy, name, 5.8, index == 6)
        _text(c, x + 263, yy, _money(employee[name]), 5.8, right=True)
        _text(c, x + 321, yy, _money(employer[name]), 5.8, right=True)
        c.setStrokeColor(LINE); c.line(x, yy - 3, x + width, yy - 3)
        yy -= row_h
    c.rect(x, yy + row_h - 3, width, 14 + row_h * 7, fill=0, stroke=1)
    c.line(x + 202, yy + row_h - 3, x + 202, top + 2)
    c.line(x + 267, yy + row_h - 3, x + 267, top + 2)

    grouped = [("Sueldo neto", neto)] + [
        (name, employee[name] + employer[name]) for name in employee
        if employee[name] + employer[name] > 0
    ]
    total_cost = sum((amount for _, amount in grouped), Decimal("0")) or Decimal("1")
    _pie_chart(c, 414, top - 41, 38, grouped)
    legend_x, legend_y = 456, top - 8
    for index, (name, amount) in enumerate(grouped):
        c.setFillColor(_COMPOSITION_COLORS[index % len(_COMPOSITION_COLORS)])
        c.rect(legend_x, legend_y - 4, 6, 6, fill=1, stroke=0)
        pct = amount / total_cost * 100
        _text(c, legend_x + 10, legend_y - 3, _fit(name, 72, 5.4), 5.4)
        _text(c, 565, legend_y - 3, f"{pct:.1f}%".replace(".", ","), 5.4, True, right=True)
        legend_y -= 9
    _text(c, 565, top - 80, f"Costo total: {_money(total_cost)}", 6.3, True, GREEN, True)
    return top - 92


def generar_recibo_pdf(data: dict[str, Any]) -> bytes:
    validar_datos_legales(data)
    output = BytesIO(); c = Canvas(output, pagesize=A4, pageCompression=1)
    c.setTitle(f"Recibo de haberes {data['periodo']}"); c.setAuthor(str(data["empresa"]["razon_social"]))
    concepts = list(data["conceptos"])
    contributions = [r for r in concepts if r["tipo"] == "contribucion"]
    worker = [r for r in concepts if r["tipo"] != "contribucion"]
    count = len(contributions) + len(worker)
    row_h = 12 if count <= 22 else max(6.3, 185 / max(count, 1))
    font = 7 if count <= 22 else max(4.5, row_h - 2.1)

    # Encabezado documental compacto. La marca pertenece a la aplicación y no
    # ocupa espacio en el instrumento laboral impreso.
    c.setStrokeColor(DARK); c.setLineWidth(.8); c.line(24, 810, 571, 810)
    _text(c, 24, 818, "RECIBO DE HABERES", 10, True)
    _text(c, 571, 818, f"PERÍODO {data['periodo']}", 8.5, True, right=True)

    if data.get("pendiente_aprobacion_contador"):
        c.setFillColor(Color(1, .96, .80)); c.setStrokeColor(Color(.85, .55, 0))
        c.rect(24, 789, 547, 17, fill=1, stroke=1)
        _text(c, 297, 795,
              "NÚMEROS REALES · PENDIENTE DE REVISIÓN Y APROBACIÓN POR CONTADOR PÚBLICO",
              6.7, True, Color(.50, .28, 0), right=True)

    y = _section(c, 784 if data.get("pendiente_aprobacion_contador") else 800,
                 "1. DATOS DEL EMPLEADOR, TRABAJADOR Y PAGO")
    e, w = data["empresa"], data["empleado"]
    left = (("Empleador", e["razon_social"]), ("CUIT", e["cuit"]), ("Domicilio", e["domicilio"]),
            ("Pago sueldo", f"{_date_display(data['pago']['fecha'])} - {data['pago']['lugar']} - {data['pago']['forma']}"),
            ("Último pago cargas", f"{_date_display(data['cargas_sociales']['fecha'])} - {data['cargas_sociales']['lugar']}"))
    worker_name = f"{w['nombre']} {w['apellido']}".strip().title()
    right = (("Trabajador", worker_name), ("CUIL / Legajo", f"{w['cuil']} / {w.get('legajo') or '-'}"),
             ("Ingreso / Antig.", f"{_date_display(w['fecha_ingreso'])} / {w.get('antiguedad') or '-'}"),
             ("Categoría / CCT", f"{w['categoria']} / {w.get('cct_numero') or '-'}"),
             ("Modalidad", w.get("modalidad_contrato") or "-"))
    c.setFillColor(white); c.setStrokeColor(LINE); c.rect(28, y - 62, 540, 68, fill=1, stroke=1)
    c.setStrokeColor(LINE); c.line(297, y - 62, 297, y + 6)
    for i, ((ll, vl), (lr, vr)) in enumerate(zip(left, right)):
        yy = y - 7 - i * 12
        _text(c, 34, yy, ll + ":", 6.7, True, GRAY); _text(c, 104, yy, _fit(vl, 183, 6.7), 6.7)
        _text(c, 303, yy, lr + ":", 6.7, True, GRAY); _text(c, 382, yy, _fit(vr, 176, 6.7), 6.7)
    y -= 72

    y = _section(c, y, "2. CONTRIBUCIONES Y CONCEPTOS A CARGO DEL EMPLEADOR")
    y = _table_header(c, y)
    for index, row in enumerate(contributions): y = _row(c, y, row, font, row_h, index % 2 == 1)
    total = sum((_decimal(r["importe"]) for r in contributions), Decimal("0"))
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(365, y - 5, 203, 15, fill=1, stroke=1)
    _text(c, 375, y, "TOTAL EMPLEADOR", 6.7, True); _text(c, 558, y, _money(total), 7, True, DARK, True)
    y -= 20

    y = _section(c, y, "3. REMUNERACIÓN BRUTA, HABERES Y DEDUCCIONES")
    y = _table_header(c, y)
    grupos = (("REMUNERATIVOS", "remunerativo"), ("NO REMUNERATIVOS", "no_remunerativo"), ("DESCUENTOS", "deduccion"))
    shade = 0
    for titulo, tipo in grupos:
        rows = [r for r in worker if r["tipo"] == tipo]
        if not rows: continue
        y = _concept_band(c, y, titulo)
        for row in rows:
            y = _row(c, y, row, font, row_h, shade % 2 == 1); shade += 1
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(28, y - 5, 540, 17, fill=1, stroke=1)
    _text(c, 38, y, f"SUELDO BRUTO: {_money(data['bruto'])}", 7, True)
    _text(c, 330, y, f"DESCUENTOS: {_money(data['total_deducciones'])}", 7, True)
    y -= 22

    y = _section(c, y, "4. SUELDO NETO")
    c.setFillColor(white); c.setStrokeColor(DARK); c.setLineWidth(1); c.rect(28, y - 28, 540, 35, fill=1, stroke=1)
    _text(c, 38, y - 7, "NETO A COBRAR", 8.5, True, DARK)
    _text(c, 558, y - 7, _money(data["neto"]), 11, True, GREEN, True)
    _text(c, 38, y - 21, _fit(_money_words(data["neto"]), 500, 6.5), 6.5, True, DARK); y -= 40

    y = _section(c, y, "RESUMEN DE LA COMPOSICIÓN TOTAL DEL COSTO LABORAL")
    y = _composition_block(c, y, _decimal(data["neto"]), worker, contributions)
    if y < 105: raise ValueError("El recibo excede una hoja A4; deben agruparse líneas equivalentes")
    c.setFillColor(white); c.setStrokeColor(LINE); c.rect(28, 88, 540, 20, fill=1, stroke=1)
    _text(c, 34, 100, "OBSERVACIONES", 5.8, True, GRAY)
    sy = 82
    c.setStrokeColor(GRAY); c.line(45, sy, 250, sy); c.line(345, sy, 550, sy)
    _text(c, 103, sy - 14, "Firma del empleador", 7)
    _text(c, 395, sy - 14, "Recibí copia fiel - Firma del trabajador", 7)
    c.setFillColor(PALE); c.rect(20, 20, 555, 25, fill=1, stroke=0)
    _text(c, 297, 30, "Recibo confeccionado conforme a los artículos 139 y 140 de la LCT", 6.2, color=GRAY, right=True)
    c.showPage(); c.save(); return output.getvalue()
