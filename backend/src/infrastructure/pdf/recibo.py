"""Recibo A4 conforme al Anexo III del Decreto 407/2026."""
from __future__ import annotations

from decimal import Decimal
from io import BytesIO
from typing import Any

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas

GREEN, PALE = HexColor("#087F73"), HexColor("#E8F4F2")
DARK, GRAY, LINE = HexColor("#172033"), HexColor("#5F6876"), HexColor("#C9D1D9")


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _money(value: Any) -> str:
    raw = f"{_decimal(value):,.2f}"
    return "$ " + raw.replace(",", "X").replace(".", ",").replace("X", ".")


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
    c.setFillColor(PALE); c.roundRect(24, y - 13, 547, 16, 2, fill=1, stroke=0)
    _text(c, 30, y - 8, title, 7.2, True, GREEN)
    return y - 19


def _logo(c: Canvas, x: float, y: float) -> None:
    for index, color in enumerate(("#2563EB", "#10B981", "#F59E0B", "#EF4444", "#A855F7")):
        c.setFillColor(HexColor(color)); c.wedge(x - 17, y - 17, x + 17, y + 17, 18 + index * 72, 66, fill=1, stroke=0)
    c.setFillColor(HexColor("#E5E7EB")); c.circle(x, y, 5, fill=1, stroke=0)
    c.setFillColor(DARK); c.circle(x, y, 2, fill=1, stroke=0)


def _row(c: Canvas, y: float, row: dict[str, Any], size: float, height: float) -> float:
    _text(c, 30, y, _fit(row["descripcion"], 255, size), size)
    _text(c, 367, y, _money(row["base_calculo"]), size, right=True)
    _text(c, 374, y, _fit(row["unidad"], 90, size), size)
    _text(c, 507, y, row["cantidad"], size, right=True)
    _text(c, 566, y, _money(row["importe"]), size, right=True)
    c.setStrokeColor(LINE); c.setLineWidth(.35); c.line(28, y - 3, 568, y - 3)
    return y - height


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
    row_h = 10.2 if count <= 24 else max(7.6, 255 / max(count, 1))
    font = 6.3 if count <= 24 else max(5.2, row_h - 3.2)

    c.setFillColor(GREEN); c.roundRect(20, 775, 555, 48, 5, fill=1, stroke=0)
    _logo(c, 48, 799); _text(c, 75, 801, "SUELDO CLARO", 13, True, white)
    _text(c, 75, 784, "RECIBO DE HABERES", 9, True, white)
    _text(c, 560, 797, f"PERIODO {data['periodo']}", 8, True, white, True)
    _text(c, 560, 784, "ANEXO III - DECRETO 407/2026", 6.4, False, white, True)

    y = _section(c, 765, "A. DATOS DEL EMPLEADOR, TRABAJADOR Y PAGO")
    e, w = data["empresa"], data["empleado"]
    left = (("Empleador", e["razon_social"]), ("CUIT", e["cuit"]), ("Domicilio", e["domicilio"]),
            ("Pago sueldo", f"{data['pago']['fecha']} - {data['pago']['lugar']} - {data['pago']['forma']}"),
            ("Cargas sociales", f"{data['cargas_sociales']['fecha']} - {data['cargas_sociales']['lugar']}"))
    right = (("Trabajador", f"{w['apellido']}, {w['nombre']}"), ("CUIL / Legajo", f"{w['cuil']} / {w.get('legajo') or '-'}"),
             ("Ingreso / Antig.", f"{w['fecha_ingreso']} / {w.get('antiguedad') or '-'}"),
             ("Categoría / CCT", f"{w['categoria']} / {w.get('cct_numero') or '-'}"),
             ("Modalidad", w.get("modalidad_contrato") or "-"))
    for i, ((ll, vl), (lr, vr)) in enumerate(zip(left, right)):
        yy = y - i * 12
        _text(c, 30, yy, ll + ":", 6.2, True, GRAY); _text(c, 100, yy, _fit(vl, 178, 6.2), 6.2)
        _text(c, 300, yy, lr + ":", 6.2, True, GRAY); _text(c, 380, yy, _fit(vr, 185, 6.2), 6.2)
    y -= 65

    for title, rows in (("B. CONTRIBUCIONES Y CONCEPTOS A CARGO DEL EMPLEADOR", contributions),
                        ("C. REMUNERACIÓN BRUTA, HABERES Y DEDUCCIONES", worker)):
        y = _section(c, y, title)
        for x, label in zip((30, 292, 374, 475, 522), ("Concepto", "Base", "Unidad", "Cant.", "Monto")):
            _text(c, x, y, label, 6.2, True, GRAY)
        y -= 9
        for row in rows: y = _row(c, y, row, font, row_h)
        if rows is contributions:
            total = sum((_decimal(r["importe"]) for r in rows), Decimal("0"))
            _text(c, 390, y, "TOTAL EMPLEADOR", 6.5, True); _text(c, 566, y, _money(total), 6.5, True, right=True)
        else:
            _text(c, 30, y, f"REMUNERACIÓN BRUTA: {_money(data['bruto'])}", 6.7, True)
            _text(c, 300, y, f"DEDUCCIONES: {_money(data['total_deducciones'])}", 6.7, True)
        y -= 13

    y = _section(c, y, "D. REMUNERACIÓN NETA")
    _text(c, 30, y - 1, "NETO A COBRAR", 9, True, GREEN); _text(c, 566, y - 1, _money(data["neto"]), 11, True, GREEN, True)
    _text(c, 30, y - 13, _fit(_money_words(data["neto"]), 535, 6.5), 6.5, True); y -= 29

    y = _section(c, y, "RESUMEN DE LA COMPOSICIÓN TOTAL DEL COSTO LABORAL")
    groups = {name: Decimal("0") for name in ("Sindical", "Seguridad social", "Obra social", "INSSJP", "ART", "Cámaras / entidades", "Otros rubros")}
    for row in contributions: groups[_cost_group(row)] += _decimal(row["importe"])
    for i, (name, amount) in enumerate(groups.items()):
        x, yy = 30 + (i % 4) * 135, y - (i // 4) * 11
        _text(c, x, yy, _fit(name, 77, 5.8), 5.8, True, GRAY); _text(c, x + 130, yy, _money(amount), 5.8, right=True)
    y -= 25
    total_contrib = sum((_decimal(r["importe"]) for r in contributions), Decimal("0"))
    _text(c, 30, y, f"Neto: {_money(data['neto'])}", 6.3)
    _text(c, 190, y, f"Retenciones: {_money(data['total_deducciones'])}", 6.3)
    _text(c, 375, y, f"COSTO TOTAL: {_money(_decimal(data['bruto']) + total_contrib)}", 7, True, GREEN)
    sy = y - 25
    if sy < 35: raise ValueError("El recibo excede una hoja A4; deben agruparse líneas equivalentes")
    c.setStrokeColor(GRAY); c.line(35, sy, 245, sy); c.line(350, sy, 560, sy)
    _text(c, 82, sy - 10, "Firma del empleador", 6.2)
    _text(c, 388, sy - 10, "Recibí el duplicado - Firma del trabajador", 6.2)
    _text(c, 24, 14, "Original para el trabajador - Conservar el duplicado firmado por el empleador", 5.5, color=GRAY)
    c.showPage(); c.save(); return output.getvalue()
