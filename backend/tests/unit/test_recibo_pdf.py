from decimal import Decimal

from infrastructure.pdf.recibo import generar_recibo_pdf


def test_recibo_backend_es_pdf_a4_de_una_sola_pagina():
    data = {
        "periodo": "2026-08",
        "empresa": {"razon_social": "Empresa Prueba", "cuit": "30123456789"},
        "empleado": {
            "apellido": "Sanidad", "nombre": "Prueba", "cuil": "27123456780",
            "legajo": "1", "categoria": "Administrativo de Primera", "cct_numero": "122/75",
            "fecha_ingreso": "2025-01-01", "modalidad_contrato": "Tiempo indeterminado",
        },
        "conceptos": [
            {"descripcion": f"Concepto de prueba {i}", "tipo": "remunerativo" if i < 12 else "deduccion", "importe": Decimal("1000")}
            for i in range(20)
        ] + [
            {"descripcion": f"Contribucion {i}", "tipo": "contribucion", "importe": Decimal("500")}
            for i in range(8)
        ],
        "bruto": Decimal("12000"), "total_deducciones": Decimal("8000"), "neto": Decimal("4000"),
    }
    pdf = generar_recibo_pdf(data)
    assert pdf.startswith(b"%PDF-1.4")
    assert b"/MediaBox [0 0 595.28 841.89]" in pdf
    assert b"/Type /Pages /Kids [3 0 R] /Count 1" in pdf
