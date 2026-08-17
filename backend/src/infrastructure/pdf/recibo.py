"""Recibo A4 conforme al Anexo III del Decreto 407/2026."""
from __future__ import annotations

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
    parts = text.split("-")
    return f"{parts[2]}/{parts[1]}/{parts[0]}" if len(parts) == 3 else text


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
    _text(c, 30, y - 9, title, 7.5, True, DARK)
    return y - 20


def _logo(c: Canvas, x: float, y: float) -> None:
    for index, color in enumerate(("#2563EB", "#10B981", "#F59E0B", "#EF4444", "#A855F7")):
        c.setFillColor(HexColor(color)); c.wedge(x - 17, y - 17, x + 17, y + 17, 18 + index * 72, 66, fill=1, stroke=0)
    c.setFillColor(HexColor("#E5E7EB")); c.circle(x, y, 5, fill=1, stroke=0)
    c.setFillColor(DARK); c.circle(x, y, 2, fill=1, stroke=0)


def _unit(value: Any) -> str:
    text = str(value or "")
    if text.endswith("%"):
        try:
            number = format(Decimal(text[:-1]), "f")
            if "." in number:
                number = number.rstrip("0").rstrip(".")
            return f"{number or '0'}%"
        except Exception:
            return text
    return text


def _row(c: Canvas, y: float, row: dict[str, Any], size: float, height: float, shaded: bool = False) -> float:
    if shaded:
        c.setFillColor(HexColor("#F3F4F6")); c.rect(28, y - 5, 540, height, fill=1, stroke=0)
    _text(c, 32, y, _fit(row["descripcion"], 250, size), size)
    _text(c, 370, y, _money(row["base_calculo"]), size, right=True)
    _text(c, 380, y, _fit(_unit(row["unidad"]), 86, size), size)
    _text(c, 508, y, row["cantidad"], size, right=True)
    _text(c, 562, y, _money(row["importe"]), size, True, right=True)
    c.setStrokeColor(LINE); c.setLineWidth(.35)
    c.line(28, y - 5, 568, y - 5)
    for x in (28, 292, 374, 466, 516, 568): c.line(x, y - 5, x, y - 5 + height)
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
    if any(word in desc for word in ("jubil", "asignaciones", "fondo de empleo")): return "Seguridad social"
    return "Otros rubros"


def generar_recibo_pdf(data: dict[str, Any]) -> bytes:
    validar_datos_legales(data)
    output = BytesIO(); c = Canvas(output, pagesize=A4, pageCompression=1)
    c.setTitle(f"Recibo de haberes {data['periodo']}"); c.setAuthor(str(data["empresa"]["razon_social"]))
    concepts = list(data["conceptos"])
    contributions = [r for r in concepts if r["tipo"] == "contribucion"]
    worker = [r for r in concepts if r["tipo"] != "contribucion"]
    count = len(contributions) + len(worker)
    row_h = 11 if count <= 22 else max(6.3, 175 / max(count, 1))
    font = 6.5 if count <= 22 else max(5.1, row_h - 1.5)

    c.setFillColor(GREEN); c.rect(20, 775, 555, 47, fill=1, stroke=0)
    _logo(c, 45, 798); _text(c, 70, 801, "SUELDO CLARO", 12, True, white)
    _text(c, 70, 785, "RECIBO DE HABERES", 8, True, white)
    _text(c, 558, 800, f"PERÍODO {data['periodo']}", 8.5, True, white, True)
    _text(c, 558, 785, "ANEXO III - DECRETO 407/2026", 6.2, False, white, True)

    y = _section(c, 765, "DATOS DEL EMPLEADOR, TRABAJADOR Y PAGO")
    e, w = data["empresa"], data["empleado"]
    left = (("Empleador", e["razon_social"]), ("CUIT", e["cuit"]), ("Domicilio", e["domicilio"]),
            ("Pago sueldo", f"{_date_display(data['pago']['fecha'])} - {data['pago']['lugar']} - {data['pago']['forma']}"),
            ("Último pago cargas", f"{_date_display(data['cargas_sociales']['fecha'])} - {data['cargas_sociales']['lugar']}"))
    right = (("Trabajador", f"{w['nombre']} {w['apellido']}"), ("CUIL / Legajo", f"{w['cuil']} / {w.get('legajo') or '-'}"),
             ("Ingreso / Antig.", f"{_date_display(w['fecha_ingreso'])} / {w.get('antiguedad') or '-'}"),
             ("Categoría / CCT", f"{w['categoria']} / {w.get('cct_numero') or '-'}"),
             ("Modalidad", w.get("modalidad_contrato") or "-"))
    c.setFillColor(white); c.setStrokeColor(LINE); c.rect(28, y - 62, 540, 68, fill=1, stroke=1)
    c.setStrokeColor(LINE); c.line(297, y - 62, 297, y + 6)
    for i, ((ll, vl), (lr, vr)) in enumerate(zip(left, right)):
        yy = y - 7 - i * 12
        _text(c, 34, yy, ll + ":", 6.2, True, GRAY); _text(c, 104, yy, _fit(vl, 183, 6.2), 6.2)
        _text(c, 303, yy, lr + ":", 6.2, True, GRAY); _text(c, 382, yy, _fit(vr, 176, 6.2), 6.2)
    y -= 72

    y = _section(c, y, "CONTRIBUCIONES Y CONCEPTOS A CARGO DEL EMPLEADOR")
    y = _table_header(c, y)
    for index, row in enumerate(contributions): y = _row(c, y, row, font, row_h, index % 2 == 1)
    total = sum((_decimal(r["importe"]) for r in contributions), Decimal("0"))
    c.setFillColor(PALE); c.setStrokeColor(LINE); c.rect(365, y - 5, 203, 15, fill=1, stroke=1)
    _text(c, 375, y, "TOTAL EMPLEADOR", 6.7, True); _text(c, 558, y, _money(total), 7, True, DARK, True)
    y -= 20

    y = _section(c, y, "REMUNERACIÓN BRUTA, HABERES Y DEDUCCIONES")
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

    y = _section(c, y, "SUELDO NETO")
    c.setFillColor(white); c.setStrokeColor(DARK); c.setLineWidth(1); c.rect(28, y - 28, 540, 35, fill=1, stroke=1)
    _text(c, 38, y - 7, "NETO A COBRAR", 8.5, True, DARK)
    _text(c, 558, y - 7, _money(data["neto"]), 11, True, GREEN, True)
    _text(c, 38, y - 21, _fit(_money_words(data["neto"]), 500, 6.5), 6.5, True, DARK); y -= 40

    y = _section(c, y, "RESUMEN DE LA COMPOSICIÓN TOTAL DEL COSTO LABORAL")
    groups = {name: Decimal("0") for name in ("Sindical", "Seguridad social", "Obra social", "INSSJP", "ART", "Cámaras / entidades", "Otros rubros")}
    for row in contributions: groups[_cost_group(row)] += _decimal(row["importe"])
    for i, (name, amount) in enumerate(groups.items()):
        col, row = i % 4, i // 4
        x, yy = 28 + col * 135, y - row * 25
        c.setFillColor(HexColor("#F3F4F6")); c.setStrokeColor(LINE); c.rect(x, yy - 15, 128, 22, fill=1, stroke=1)
        _text(c, x + 7, yy - 1, _fit(name, 74, 6.2), 6.2, True, GRAY)
        _text(c, x + 121, yy - 1, _money(amount), 6.2, True, right=True)
    y -= 54
    total_contrib = sum((_decimal(r["importe"]) for r in contributions), Decimal("0"))
    _text(c, 34, y, f"Neto: {_money(data['neto'])}", 7)
    _text(c, 205, y, f"Retenciones: {_money(data['total_deducciones'])}", 7)
    _text(c, 558, y, f"COSTO TOTAL: {_money(_decimal(data['bruto']) + total_contrib)}", 8.5, True, GREEN, True)
    if y < 112: raise ValueError("El recibo excede una hoja A4; deben agruparse líneas equivalentes")
    sy = 82
    c.setStrokeColor(GRAY); c.line(45, sy, 250, sy); c.line(345, sy, 550, sy)
    _text(c, 103, sy - 14, "Firma del empleador", 7)
    _text(c, 381, sy - 14, "Recibí el duplicado - Firma del trabajador", 7)
    c.setFillColor(PALE); c.rect(20, 20, 555, 25, fill=1, stroke=0)
    _text(c, 297, 30, "Original para el trabajador - Conservar el duplicado firmado por el empleador", 6.2, color=GRAY, right=True)
    c.showPage(); c.save(); return output.getvalue()
