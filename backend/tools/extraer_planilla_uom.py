"""Normaliza la planilla oficial UOM 2026-2027 sin inferir importes.

Uso de auditoría (no se ejecuta en producción):
  python backend/tools/extraer_planilla_uom.py planilla.pdf salida.json

El extractor exige el SHA-256 de la fuente revisada, conserva la página y
separa categorías, IMGR y adicionales. Si cambia el PDF, se detiene.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pdfplumber


SOURCE_SHA256 = "132ff1b0696593efcc136b27145dbc86edf76d4247d63875bde33c6d9bc44f45"
DATES = ("2026-08-01", "2026-09-01", "2026-10-01", "2026-11-01",
         "2026-12-01", "2027-01-01", "2027-03-01", "2027-04-01")
GROUPS = {
    **{p: ("R17_3_13_14_15_16_20", "Ramas 17, 3, 13, 14, 15, 16 y 20") for p in range(1, 6)},
    **{p: ("R4_AUTOMOTOR", "Rama 4 Automotor · Laudo 29") for p in range(6, 10)},
    **{p: ("R5_8_12_18", "Ramas 5, 8, 12 y 18") for p in range(10, 14)},
    **{p: ("R10_CARROCERIAS", "Rama 10 Carrocerías") for p in range(14, 17)},
    **{p: ("R1_ALUMINIO", "Rama 1 Aluminio") for p in range(17, 21)},
}
ADDITIONAL_START = {5: 2, 8: 4, 12: 15, 15: 26, 19: 10}
VALUE_RE = re.compile(r"\$\s*([\d. ]+,\d{2})")
# Seis rótulos quedan atravesados por la firma digital visible del PDF. Se
# corrigen por página + primer valor, nunca por una aproximación del texto.
SIGNED_LABELS = {
    (2, "4143.17"): "3er. Año",
    (4, "5602.95"): "Operario Especializado",
    (7, "1326849.45"): "Cat. Adm. de 3ª",
    (8, "23749.35"): "Título Secundario",
    (18, "3883.50"): "1er. Año",
    (19, "6280.51"): "Con Patente de 2ª",
}


def _amount(value: str) -> str:
    return str(Decimal(value.replace(" ", "").replace(".", "").replace(",", ".")))


def _clean_label(value: str) -> str:
    value = re.sub(r"\(CPA.*?(?:444\)|444)", "", value, flags=re.I)
    value = re.sub(r"Dr\.?\s*Edgardo\s*Khalil", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" -")
    return value


def extract(pdf_path: Path) -> dict:
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    if digest != SOURCE_SHA256:
        raise ValueError(f"La fuente UOM cambió: SHA-256 recibido {digest}")
    rows: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) != 21:
            raise ValueError("La planilla UOM verificada debe tener 21 páginas")
        modality = "HORA"
        current_group = None
        for page_no, page in enumerate(pdf.pages[:20], 1):
            group_code, group_name = GROUPS[page_no]
            if group_code != current_group:
                modality = "HORA"
                current_group = group_code
            additional = page_no in {9, 13, 16, 20}
            pending: list[str] = []
            for line_no, raw in enumerate((page.extract_text(x_tolerance=2, y_tolerance=3) or "").splitlines()):
                text = _clean_label(raw)
                upper = text.upper()
                if page_no in ADDITIONAL_START and line_no >= ADDITIONAL_START[page_no]:
                    additional = True
                if "PERSONAL JORNALIZADO" in upper or "FOGUISTAS Y CHOFERES" in upper:
                    modality = "HORA"
                elif "PERSONAL MENSUALIZADO" in upper or "EMPLEADOS MENORES" in upper:
                    modality = "MENSUAL"
                elif "MENORES AYUDANTES OBREROS" in upper or "APRENDICES" in upper:
                    modality = "HORA"
                values = VALUE_RE.findall(raw)
                if not values:
                    if text and not re.match(r"^(\d{2}/\d{2}/\d{4}|\$)", text):
                        pending = (pending + [text])[-2:]
                    continue
                if len(values) < 1:
                    raise ValueError(f"Fila sin importe en página {page_no}: {raw}")
                label = _clean_label(raw[: raw.find("$")]) or " · ".join(pending)
                first_value = _amount(values[0])
                label = SIGNED_LABELS.get((page_no, first_value), label)
                if not label:
                    raise ValueError(f"Fila sin etiqueta en página {page_no}")
                kind = "IMGR" if "IMGR" in label.upper() else ("ADICIONAL" if additional else "CATEGORIA")
                unit = modality
                if kind == "ADICIONAL":
                    unit = "POR_HORA" if "POR HORA" in label.upper() else (
                        "POR_EVENTO" if "POR CADA" in label.upper() else "FIJO_MENSUAL"
                    )
                rows.append({
                    "grupo_codigo": group_code, "grupo_nombre": group_name,
                    "pagina": page_no, "tipo": kind, "modalidad": unit,
                    "etiqueta": label,
                    # Agosto es el único período que se instala. Las columnas futuras
                    # dañadas por la superposición de firmas permanecen ausentes y
                    # deberán compilarse desde su fuente mensual antes de habilitarse.
                    "valores": dict(zip(DATES, map(_amount, values[:8]))),
                    "columnas_extraidas": len(values[:8]),
                })
                pending = []
    counts = Counter(row["tipo"] for row in rows)
    if counts != {"CATEGORIA": 247, "ADICIONAL": 75, "IMGR": 5}:
        raise ValueError(f"Conteo inesperado: {dict(counts)}")
    for row in rows:
        amounts = [Decimal(value) for value in row["valores"].values()]
        if any(value <= 0 for value in amounts):
            raise ValueError(f"Importe no positivo: {row}")
    return {
        "cct": "260/75", "fuente_url": "https://www.adimra.org.ar/api/public/archivos/4304",
        "fuente_sha256": digest, "expediente": "RE-2026-79536710-APN-CGDTEYS#MCH",
        "vigencias": list(DATES), "conteos": dict(counts), "filas": rows,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: extraer_planilla_uom.py FUENTE.pdf SALIDA.json")
    output = extract(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
