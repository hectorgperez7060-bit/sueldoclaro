"""Generador mínimo y determinista de recibos A4 de una sola página.

No usa el diálogo de impresión del navegador: construye un PDF válido en el
backend para que iOS sólo tenga que descargarlo.
"""
from __future__ import annotations

from decimal import Decimal
from math import cos, pi, sin
from typing import Any


def _pdf_text(value: Any) -> str:
    text = str(value or "—").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    return text.encode("cp1252", "replace").decode("latin1")


def _money(value: Any) -> str:
    number = Decimal(str(value or 0)).quantize(Decimal("0.01"))
    raw = f"{number:,.2f}"
    return raw.replace(",", "X").replace(".", ",").replace("X", ".")


class _Page:
    def __init__(self) -> None:
        self.ops: list[str] = []

    def fill(self, x: float, y: float, w: float, h: float, rgb: tuple[float, float, float]) -> None:
        self.ops.append(f"{rgb[0]} {rgb[1]} {rgb[2]} rg {x:.1f} {y:.1f} {w:.1f} {h:.1f} re f")

    def line(self, x1: float, y1: float, x2: float, y2: float, gray: float = .82) -> None:
        self.ops.append(f"{gray} G {x1:.1f} {y1:.1f} m {x2:.1f} {y2:.1f} l S")

    def polygon(self, points: list[tuple[float, float]], rgb: tuple[float, float, float]) -> None:
        start, *rest = points
        path = f"{start[0]:.1f} {start[1]:.1f} m " + " ".join(
            f"{x:.1f} {y:.1f} l" for x, y in rest
        )
        self.ops.append(f"{rgb[0]} {rgb[1]} {rgb[2]} rg {path} h f")

    def circle(self, cx: float, cy: float, radius: float, rgb: tuple[float, float, float]) -> None:
        k = .55228475 * radius
        self.ops.append(
            f"{rgb[0]} {rgb[1]} {rgb[2]} rg "
            f"{cx + radius:.1f} {cy:.1f} m "
            f"{cx + radius:.1f} {cy + k:.1f} {cx + k:.1f} {cy + radius:.1f} {cx:.1f} {cy + radius:.1f} c "
            f"{cx - k:.1f} {cy + radius:.1f} {cx - radius:.1f} {cy + k:.1f} {cx - radius:.1f} {cy:.1f} c "
            f"{cx - radius:.1f} {cy - k:.1f} {cx - k:.1f} {cy - radius:.1f} {cx:.1f} {cy - radius:.1f} c "
            f"{cx + k:.1f} {cy - radius:.1f} {cx + radius:.1f} {cy - k:.1f} {cx + radius:.1f} {cy:.1f} c f"
        )

    def text(self, x: float, y: float, text: Any, size: float = 8, bold: bool = False,
             rgb: tuple[float, float, float] = (0, 0, 0)) -> None:
        font = "F2" if bold else "F1"
        self.ops.append(
            f"BT /{font} {size:.1f} Tf {rgb[0]} {rgb[1]} {rgb[2]} rg "
            f"1 0 0 1 {x:.1f} {y:.1f} Tm ({_pdf_text(text)}) Tj ET"
        )


def _build_pdf(stream: bytes) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Resources << /Font << /F1 4 0 R /F2 5 0 R >> >> /Contents 6 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
    ]
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode())
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects)+1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(f"trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(out)


def generar_recibo_pdf(data: dict[str, Any]) -> bytes:
    page = _Page()
    green = (0.05, .47, .43)
    pale = (.90, .95, .94)
    dark = (.08, .13, .20)
    left, right, width = 30, 565, 535

    page.fill(left, 770, width, 48, green)
    # Emblema circular multicolor original de Sueldo Claro, dibujado como
    # vector para conservar nitidez en pantalla e impresión.
    logo_x, logo_y = 58.0, 794.0
    logo_colors = [
        (.10, .38, .88),  # azul
        (.10, .55, .42),  # verde
        (.90, .42, .24),  # naranja
        (.86, .25, .31),  # rojo
        (.72, .25, .48),  # magenta
    ]
    for index, color in enumerate(logo_colors):
        start = (-88 + index * 72) * pi / 180
        end = start + 68 * pi / 180
        # Cada aspa comparte una circunferencia exterior; el último punto
        # vuelve hacia el centro para conservar el efecto de molinete.
        points = [(logo_x, logo_y)]
        for step in range(9):
            a = start + (end - start) * step / 8
            points.append((logo_x + 22 * cos(a), logo_y + 22 * sin(a)))
        inner = end - 18 * pi / 180
        points.append((logo_x + 8 * cos(inner), logo_y + 8 * sin(inner)))
        page.polygon(points, color)
    page.circle(logo_x, logo_y, 6.0, (.88, .90, .91))
    page.circle(logo_x, logo_y, 2.5, (.25, .31, .36))
    page.text(88, 797, "SUELDO CLARO", 14, True, (1, 1, 1))
    page.text(88, 781, "RECIBO DE HABERES", 10, True, (1, 1, 1))
    page.text(375, 789, f"Anexo III  |  Periodo {data['periodo']}", 8, False, (1, 1, 1))

    page.fill(left, 744, width, 17, pale)
    page.text(36, 749, "DATOS DEL EMPLEADOR Y DEL TRABAJADOR", 8, True, green)
    employer = data["empresa"]
    employee = data["empleado"]
    page.text(38, 728, "EMPLEADOR", 8, True, dark)
    page.text(38, 714, f"Razon social: {employer.get('razon_social') or '—'}", 8)
    page.text(38, 700, f"CUIT: {employer.get('cuit') or '—'}", 8)
    page.text(310, 728, "TRABAJADOR", 8, True, dark)
    page.text(310, 714, f"Apellido y nombre: {employee.get('apellido','')}, {employee.get('nombre','')}", 8)
    page.text(310, 700, f"CUIL: {employee.get('cuil') or '—'}  |  Legajo: {employee.get('legajo') or '—'}", 8)
    page.text(310, 686, f"Categoria: {employee.get('categoria') or '—'}  |  CCT {employee.get('cct_numero') or '—'}", 8)
    page.text(38, 686, f"Ingreso: {employee.get('fecha_ingreso') or '—'}  |  Modalidad: {employee.get('modalidad_contrato') or '—'}", 8)

    concepts = data["conceptos"]
    contributions = [c for c in concepts if c["tipo"] == "contribucion"]
    earnings = [c for c in concepts if c["tipo"] in ("remunerativo", "no_remunerativo")]
    deductions = [c for c in concepts if c["tipo"] == "deduccion"]
    total_rows = max(1, len(contributions) + len(earnings) + len(deductions) + 4)
    row_h = max(10.0, min(15.0, 355.0 / total_rows))

    y = 658
    page.fill(left, y, width, 18, pale)
    page.text(36, y + 5, "CONTRIBUCIONES DEL EMPLEADOR", 8, True, green)
    y -= row_h
    for concept in contributions:
        page.text(38, y + 3, str(concept["descripcion"])[:68], 7.5)
        page.text(490, y + 3, f"$ {_money(concept['importe'])}", 7.5, False)
        page.line(38, y, right, y)
        y -= row_h
    total_contrib = sum(Decimal(str(c["importe"])) for c in contributions)
    page.text(38, y + 3, "Total contribuciones", 8, True)
    page.text(490, y + 3, f"$ {_money(total_contrib)}", 8, True)
    y -= row_h + 7

    page.fill(left, y, width, 18, pale)
    page.text(36, y + 5, "HABERES Y DEDUCCIONES", 8, True, green)
    y -= row_h
    page.text(38, y + 3, "Concepto", 7.5, True)
    page.text(395, y + 3, "Haberes", 7.5, True)
    page.text(490, y + 3, "Deducciones", 7.5, True)
    y -= row_h
    for concept in earnings + deductions:
        page.text(38, y + 3, str(concept["descripcion"])[:58], 7.5)
        x = 395 if concept["tipo"] != "deduccion" else 490
        page.text(x, y + 3, f"$ {_money(concept['importe'])}", 7.5)
        page.line(38, y, right, y)
        y -= row_h

    y -= 2
    page.text(38, y, f"BRUTO: $ {_money(data['bruto'])}", 9, True, dark)
    page.text(220, y, f"DEDUCCIONES: $ {_money(data['total_deducciones'])}", 9, True, dark)
    page.text(405, y, f"NETO: $ {_money(data['neto'])}", 10, True, green)
    y -= 25
    page.fill(left, y, width, 18, pale)
    page.text(36, y + 5, "RESUMEN DEL COSTO LABORAL", 8, True, green)
    y -= 18
    cost = Decimal(str(data["bruto"])) + total_contrib
    page.text(38, y, f"Neto trabajador: $ {_money(data['neto'])}", 8)
    page.text(205, y, f"Retenciones: $ {_money(data['total_deducciones'])}", 8)
    page.text(355, y, f"Cargas patronales: $ {_money(total_contrib)}", 8)
    y -= 15
    page.text(38, y, f"COSTO LABORAL TOTAL: $ {_money(cost)}", 9, True, green)
    y = max(35, y - 32)
    page.line(55, y, 250, y, .55)
    page.line(345, y, 540, y, .55)
    page.text(105, y - 12, "Firma del empleador", 7)
    page.text(385, y - 12, "Recibi conforme - Firma del trabajador", 7)
    page.text(30, 15, "DOCUMENTO DE PRUEBA - Parametros sujetos a validacion profesional.", 6, False, (.45, .45, .45))

    return _build_pdf("\n".join(page.ops).encode("latin1"))
