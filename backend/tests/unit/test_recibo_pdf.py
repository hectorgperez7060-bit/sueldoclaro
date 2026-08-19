from decimal import Decimal

import io

import pytest
from pypdf import PdfReader

from infrastructure.pdf.recibo import _cost_group, _date_display, _unit, generar_recibo_pdf


def test_recibo_backend_es_pdf_a4_de_una_sola_pagina():
    data = {
        "periodo": "2026-08",
        "empresa": {"razon_social": "Empresa Prueba", "cuit": "30123456789", "domicilio": "Maipu 589, Merlo"},
        "empleado": {
            "apellido": "Sanidad", "nombre": "Prueba", "cuil": "27123456780",
            "legajo": "1", "categoria": "Administrativo de Primera", "cct_numero": "122/75",
            "fecha_ingreso": "2025-01-01", "modalidad_contrato": "Tiempo indeterminado",
            "antiguedad": "1 año",
        },
        "pago": {"fecha": "2026-09-04", "lugar": "Merlo, Buenos Aires", "forma": "Acreditación en cuenta"},
        "cargas_sociales": {"fecha": "2026-08-10", "lugar": "ARCA"},
        "conceptos": [
            {"codigo": f"C{i}", "descripcion": f"Concepto de prueba {i}",
             "tipo": "remunerativo" if i < 12 else "deduccion", "importe": Decimal("1000"),
             "base_calculo": Decimal("10000"), "unidad": "10%", "cantidad": Decimal("1")}
            for i in range(20)
        ] + [
            {"codigo": f"CONTRIB_{i}", "descripcion": f"Contribucion {i}", "tipo": "contribucion",
             "importe": Decimal("500"), "base_calculo": Decimal("10000"),
             "unidad": "5%", "cantidad": Decimal("1")}
            for i in range(8)
        ],
        "bruto": Decimal("12000"), "total_deducciones": Decimal("8000"), "neto": Decimal("4000"),
    }
    pdf = generar_recibo_pdf(data)
    assert pdf.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(pdf))
    assert len(reader.pages) == 1
    assert tuple(round(float(v), 2) for v in reader.pages[0].mediabox[2:]) == (595.28, 841.89)
    text = reader.pages[0].extract_text()
    assert "1. DATOS DEL EMPLEADOR, TRABAJADOR Y PAGO" in text
    assert "2. CONTRIBUCIONES Y CONCEPTOS A CARGO DEL EMPLEADOR" in text
    assert "3. REMUNERACIÓN BRUTA, HABERES Y DEDUCCIONES" in text
    assert "4. SUELDO NETO" in text
    assert "Base" in text and "Unidad" in text and "Cant." in text
    assert "REMUNERATIVOS" in text and "DESCUENTOS" in text
    assert "Pesos cuatro mil con 00/100" in text
    assert "Seguridad social" in text and "Otros rubros" in text
    assert "DOCUMENTO DE PRUEBA" not in text
    assert "SUELDO CLARO" not in text
    assert "Recibo confeccionado conforme a los artículos 139 y 140 de la LCT" in text


def test_porcentajes_conservan_el_valor_completo():
    assert _unit("10%") == "10%"
    assert _unit("6.00%") == "6%"
    assert _unit("1.00000000% por año") == "1% por año"
    assert _unit("8.33%") == "8,33%"
    assert _unit("1/12.0000") == "8,33%"


def test_fechas_del_recibo_siempre_se_muestran_dia_mes_anio():
    assert _date_display("2026-08-19") == "19/08/2026"
    assert _date_display("2026/08/19") == "19/08/2026"
    assert _date_display("19/08/2026") == "19/08/2026"


def test_contribuciones_patronales_se_clasifican_como_seguridad_social():
    assert _cost_group({
        "codigo": "CONTRIB_SEG_SOCIAL",
        "descripcion": "Contribuciones patronales seguridad social (18%)",
    }) == "Seguridad social"


def test_recibo_rechaza_datos_legales_incompletos():
    with pytest.raises(ValueError, match="empresa.domicilio"):
        generar_recibo_pdf({
            "periodo": "2026-08", "empresa": {"razon_social": "X", "cuit": "30123456789"},
            "empleado": {}, "pago": {}, "cargas_sociales": {}, "conceptos": [],
        })
