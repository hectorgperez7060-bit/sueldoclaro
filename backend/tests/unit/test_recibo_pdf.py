import io
import re
from decimal import Decimal

import pytest
from pypdf import PdfReader

from infrastructure.pdf.recibo import (
    RUBROS_MINIMOS, _cost_group, _date_display, _destinos_sindicales,
    _etiqueta_sindical, _porcentajes_visibles, _unit, generar_recibo_pdf,
)


def _concepto(codigo, descripcion, tipo, importe, unidad="10%", **extra):
    base = {
        "codigo": codigo, "descripcion": descripcion, "tipo": tipo,
        "importe": Decimal(importe), "base_calculo": Decimal("1000000"),
        "unidad": unidad, "cantidad": Decimal("1"),
    }
    base.update(extra)
    return base


CONCEPTOS_BASE = [
    _concepto("BASICO", "Sueldo básico", "remunerativo", "1000000", "mes"),
    _concepto("ANTIGUEDAD", "Antigüedad", "remunerativo", "60000", "1% por año"),
    _concepto("PRESENTISMO", "Presentismo", "remunerativo", "88300", "1/12.0000"),
    _concepto("APORTE_JUBILACION", "Jubilación", "deduccion", "126113", "11.00%"),
    _concepto("APORTE_LEY19032", "Ley 19.032 - INSSJP", "deduccion", "34394", "3.00%"),
    _concepto("APORTE_OBRA_SOCIAL", "Obra social", "deduccion", "34394", "3.00%"),
    _concepto("APORTE_ADEF_REM_414/05", "Aporte ADEF sobre remunerativos", "deduccion",
              "43889.54", "2.00%", destino_pago="ADEF", codigo_boleta="ADEF_APORTES"),
    _concepto("CONTRIB_JUBILACION", "Contribuciones patronales seguridad social (18%)",
              "contribucion", "206363", "18.00%"),
    _concepto("CONTRIB_OBRA_SOCIAL", "Contribución patronal obra social (6%)",
              "contribucion", "68787", "6.00%"),
]


def _datos(**cambios):
    data = {
        "periodo": "2026-08",
        "empresa": {"razon_social": "Empresa Prueba S.R.L.", "cuit": "30123456789",
                    "domicilio": "Maipú 589, Merlo, Provincia de Buenos Aires"},
        "empleado": {
            "apellido": "Sanidad", "nombre": "Prueba", "cuil": "27123456780",
            "legajo": "1", "categoria": "Administrativo de Primera", "cct_numero": "122/75",
            "fecha_ingreso": "2025-01-01", "modalidad_contrato": "Tiempo indeterminado",
            "antiguedad": "1 año",
        },
        "pago": {"fecha": "2026-09-04", "lugar": "Sucursal Merlo",
                 "forma": "Acreditación en cuenta",
                 "establecimiento": "Sucursal Merlo Centro",
                 "domicilio_trabajo": "Av. Rivadavia 1234, Merlo"},
        "cargas_sociales": {},
        "conceptos": list(CONCEPTOS_BASE),
        "bruto": Decimal("1148300"), "total_deducciones": Decimal("238790.54"),
        "neto": Decimal("909509.46"),
    }
    data.update(cambios)
    return data


def _texto(data):
    pdf = generar_recibo_pdf(data)
    reader = PdfReader(io.BytesIO(pdf))
    return pdf, reader, reader.pages[0].extract_text()


# --------------------------------------------------------------------------- #
# 1-4. Contenido legal mínimo (LCT arts. 139 y 140).
# --------------------------------------------------------------------------- #
def test_contiene_cuit_del_empleador_y_cuil_del_trabajador():
    _, _, texto = _texto(_datos())
    assert "30123456789" in texto
    assert "27123456780" in texto


def test_contiene_periodo_fecha_de_ingreso_y_categoria():
    _, _, texto = _texto(_datos())
    assert "2026-08" in texto
    assert "01/01/2025" in texto
    assert "Administrativo de Primera" in texto


def test_contiene_bruto_deducciones_y_neto_en_numeros_y_letras():
    _, _, texto = _texto(_datos())
    assert "$ 1.148.300,00" in texto
    assert "$ 238.790,54" in texto
    assert "$ 909.509,46" in texto
    assert "Pesos novecientos nueve mil quinientos nueve con 46/100" in texto


def test_incluye_las_contribuciones_patronales_con_su_porcentaje_real():
    _, _, texto = _texto(_datos())
    assert "2. CONTRIBUCIONES Y CONCEPTOS A CARGO DEL EMPLEADOR" in texto
    assert "Contribuciones patronales seguridad social" in texto
    assert "Contribución patronal obra social" in texto
    assert "18%" in texto and "6%" in texto


# --------------------------------------------------------------------------- #
# 5-7. Nada de totales falsos ni ART en cero.
# --------------------------------------------------------------------------- #
def test_no_contiene_el_total_a_depositar_del_f931():
    _, _, texto = _texto(_datos())
    assert "Total a depositar (F.931)" not in texto
    assert "F.931" not in texto


def test_sin_art_no_dice_costo_total_y_declara_el_subtotal():
    _, _, texto = _texto(_datos())
    assert "Costo total" not in texto
    assert "Subtotal conocido del costo laboral" in texto


def test_sin_art_muestra_pendiente_y_no_un_importe_en_cero():
    _, _, texto = _texto(_datos())
    assert "ART pendiente de contrato/cálculo" in texto
    assert "ART $ 0,00" not in texto


def test_con_art_calculada_el_pdf_la_muestra_sin_cambiar_la_estructura():
    datos = _datos(conceptos=CONCEPTOS_BASE + [
        _concepto("CUOTA_ART", "Cuota de riesgos del trabajo", "contribucion",
                  "34449", "3.00%"),
    ])
    _, _, texto = _texto(datos)
    assert "A.R.T." in texto
    assert "$ 34.449,00" in texto
    assert "ART pendiente de contrato/cálculo" not in texto
    assert "Costo laboral con ART incluida" in texto


# --------------------------------------------------------------------------- #
# 8. Clasificación por metadatos, no por gremio.
# --------------------------------------------------------------------------- #
def test_un_aporte_sindical_no_cae_en_otros_rubros():
    _, _, texto = _texto(_datos())
    assert "Aportes sindicales / ADEF" in texto
    assert "$ 43.889,54" in texto


def test_la_clasificacion_sindical_sale_de_los_metadatos_para_cualquier_gremio():
    fatsa = {"codigo": "APORTE_SOLIDARIO_FATSA", "descripcion": "Aporte solidario FATSA 1%",
             "destino_pago": "FATSA", "codigo_boleta": "FATSA_APORTES"}
    adef = {"codigo": "APORTE_ADEF_REM_414/05", "descripcion": "Aporte ADEF sobre remunerativos",
            "destino_pago": "ADEF", "codigo_boleta": "ADEF_APORTES"}
    # El rubro es el que exige el decreto; el destino real sale de los metadatos.
    assert _cost_group(fatsa) == "Sindical"
    assert _cost_group(adef) == "Sindical"
    assert _etiqueta_sindical(_destinos_sindicales([adef])) == "Aportes sindicales / ADEF"
    assert _etiqueta_sindical(_destinos_sindicales([adef, fatsa])) == "Aportes sindicales / ADEF, FATSA"
    # Sin metadatos, un código sindical conocido sigue sin caer en "Otros rubros".
    assert _cost_group({"codigo": "CUOTA_SINDICAL", "descripcion": "Cuota sindical"}) == "Sindical"


def test_una_cuota_sindical_del_articulo_101_no_se_confunde_con_art():
    assert _cost_group({
        "codigo": "CUOTA_SINDICAL_ART101", "descripcion": "Cuota sindical (art. 101, afiliados)",
    }) != "ART"


def test_contribuciones_patronales_se_clasifican_como_seguridad_social():
    assert _cost_group({
        "codigo": "CONTRIB_SEG_SOCIAL",
        "descripcion": "Contribuciones patronales seguridad social (18%)",
    }) == "Seguridad social"


# --------------------------------------------------------------------------- #
# 9. Nada truncado.
# --------------------------------------------------------------------------- #
def test_los_datos_largos_no_quedan_truncados():
    datos = _datos()
    datos["empleado"]["nombre"] = "María de los Ángeles Guadalupe"
    datos["empleado"]["apellido"] = "Fernández Iturriaga de Etchevehere"
    datos["empleado"]["categoria"] = "Auxiliar especializado en administración y sistemas"
    datos["empresa"]["domicilio"] = (
        "Avenida Presidente Juan Domingo Perón 12345, piso 7, oficina 703, Merlo"
    )
    datos["pago"]["establecimiento"] = "Establecimiento Industrial Parque Norte — Planta 2"
    datos["pago"]["domicilio_trabajo"] = (
        "Ruta Provincial 24 kilómetro 17,5, Parque Industrial Norte, Moreno"
    )
    _, reader, texto = _texto(datos)
    assert "..." not in texto
    assert "Fernández Iturriaga De Etchevehere" in texto
    assert "Ruta Provincial 24" in texto
    assert len(reader.pages) == 1


# --------------------------------------------------------------------------- #
# 10. Vista previa mientras no haya firma acreditada.
# --------------------------------------------------------------------------- #
def test_sin_firma_el_pdf_se_identifica_como_vista_previa():
    _, _, texto = _texto(_datos())
    assert "VISTA PREVIA — SIN FIRMA NI CONSTANCIA DE ENTREGA" in texto
    assert "Firma del empleador" in texto
    assert "Firma o aceptación del trabajador" in texto
    assert "Fecha de recepción" in texto
    assert "recibí copia fiel" in texto.lower()


def test_una_firma_incompleta_sigue_siendo_vista_previa():
    datos = _datos(firma={"tipo": "digital"})
    _, _, texto = _texto(datos)
    assert "VISTA PREVIA — SIN FIRMA NI CONSTANCIA DE ENTREGA" in texto


def test_una_firma_enviada_por_el_cliente_no_se_considera_acreditada():
    datos = _datos(firma={
        "tipo": "digital",
        "verificacion": "Aceptación electrónica ID 8f3c-2026-0091",
        "fecha_recepcion": "2026-09-05",
    })
    _, _, texto = _texto(datos)
    assert "VISTA PREVIA — SIN FIRMA NI CONSTANCIA DE ENTREGA" in texto
    assert "Firma registrada" not in texto


# --------------------------------------------------------------------------- #
# 11. Ley 17.250 art. 12: fecha, período y banco por separado.
# --------------------------------------------------------------------------- #
def test_sin_datos_del_ultimo_deposito_los_declara_pendientes():
    _, _, texto = _texto(_datos())
    assert "Datos del último depósito pendientes de completar" in texto


def test_datos_incompletos_del_ultimo_deposito_tambien_quedan_pendientes():
    datos = _datos(cargas_sociales={"fecha": "2026-08-10", "lugar": "ARCA"})
    _, _, texto = _texto(datos)
    assert "Datos del último depósito pendientes de completar" in texto


def test_el_ultimo_deposito_se_muestra_en_tres_campos_separados():
    datos = _datos(cargas_sociales={
        "fecha": "2026-08-10", "periodo": "2026-07",
        "banco": "Banco de la Nación Argentina",
    })
    _, _, texto = _texto(datos)
    assert "Fecha del último depósito" in texto
    assert "10/08/2026" in texto
    assert "Período al que corresponde" in texto
    assert "2026-07" in texto
    assert "Banco o entidad" in texto
    assert "Banco de la Nación Argentina" in texto
    assert "Datos del último depósito pendientes de completar" not in texto


# --------------------------------------------------------------------------- #
# 12. Una sola hoja A4, también con muchas líneas.
# --------------------------------------------------------------------------- #
def test_sigue_siendo_una_sola_hoja_a4():
    _, reader, _ = _texto(_datos())
    assert len(reader.pages) == 1
    assert tuple(round(float(v), 2) for v in reader.pages[0].mediabox[2:]) == (595.28, 841.89)


def test_una_liquidacion_larga_entra_en_una_hoja():
    conceptos = list(CONCEPTOS_BASE) + [
        _concepto(f"ADIC_{i}", f"Adicional convencional número {i}", "remunerativo", "15000")
        for i in range(10)
    ] + [
        _concepto(f"CONTRIB_CONV_{i}", f"Contribución convencional {i}", "contribucion",
                  "9000", destino_pago="FATSA", codigo_boleta="FATSA_CONTRIB")
        for i in range(6)
    ]
    _, reader, texto = _texto(_datos(conceptos=conceptos))
    assert len(reader.pages) == 1
    assert "..." not in texto


def test_el_pdf_conserva_los_datos_del_pago_en_campos_separados():
    _, _, texto = _texto(_datos())
    for etiqueta in ("Período liquidado", "Fecha efectiva de pago", "Forma de pago",
                     "Lugar o establecimiento de pago", "Domicilio del lugar de trabajo"):
        assert etiqueta in texto
    assert "04/09/2026" in texto
    assert "Acreditación en cuenta" in texto
    assert "Av. Rivadavia 1234, Merlo" in texto


def test_un_dato_de_pago_no_informado_se_declara_no_informado():
    datos = _datos()
    datos["pago"]["domicilio_trabajo"] = ""
    datos["pago"]["establecimiento"] = ""
    _, _, texto = _texto(datos)
    assert "No informado" in texto


# --------------------------------------------------------------------------- #
# Utilidades ya cubiertas antes de esta corrección.
# --------------------------------------------------------------------------- #
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


def test_recibo_rechaza_datos_legales_incompletos():
    with pytest.raises(ValueError, match="empresa.domicilio"):
        generar_recibo_pdf({
            "periodo": "2026-08", "empresa": {"razon_social": "X", "cuit": "30123456789"},
            "empleado": {}, "pago": {}, "cargas_sociales": {}, "conceptos": [],
        })


def test_el_recibo_no_lleva_marca_de_la_aplicacion_ni_texto_de_prueba():
    _, _, texto = _texto(_datos())
    assert "DOCUMENTO DE PRUEBA" not in texto
    assert "SUELDO CLARO" not in texto
    assert "Recibo confeccionado conforme a los artículos 139 y 140 de la LCT" in texto
    assert "Ley 17.250" in texto


# --------------------------------------------------------------------------- #
# Decreto 407/2026, Anexo I art. 5: rubros mínimos y gráfico de porciones.
# --------------------------------------------------------------------------- #
def test_muestra_los_siete_rubros_minimos_aunque_esten_en_cero():
    _, _, texto = _texto(_datos())
    assert len(RUBROS_MINIMOS) == 7
    for rubro in ("Seguridad social", "Obra social", "INSSJP", "A.R.T.",
                  "Cámaras / entidades", "Otros rubros"):
        assert rubro in texto, rubro
    assert "Aportes sindicales / ADEF" in texto


def test_el_grafico_de_porciones_esta_presente_y_suma_cien():
    _, _, texto = _texto(_datos())
    porcentajes = [
        float(p.replace(",", ".")) for p in re.findall(r"(\d+,\d)%", texto)
    ]
    # Las porciones del gráfico llevan un decimal; deben cubrir el 100 % del
    # subtotal conocido, sin la ART pendiente.
    assert porcentajes, "el recibo no muestra porcentajes de composición"
    # La suma se compara con tolerancia: los porcentajes se leen del PDF como
    # float y 66,8 + 21,6 + 6,0 + 2,2 + 3,4 da 100,00000000000001 en binario.
    # La suma exacta de las décimas ya la controla el test de _porcentajes_visibles.
    assert abs(sum(p for p in porcentajes if p <= 100) - 100.0) < 0.05


def test_el_redondeo_visible_del_grafico_suma_exactamente_cien():
    porcentajes = _porcentajes_visibles([
        ("a", Decimal("1")), ("b", Decimal("1")), ("c", Decimal("1")),
    ])
    assert porcentajes == [Decimal("33.4"), Decimal("33.3"), Decimal("33.3")]
    assert sum(porcentajes) == Decimal("100.0")


def test_la_art_pendiente_no_entra_como_porcion_del_grafico():
    _, _, texto = _texto(_datos())
    assert "pendiente, no incluida en las porciones" in texto
