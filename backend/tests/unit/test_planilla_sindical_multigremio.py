import csv
import io

import pytest

from api.routes.exportaciones import construir_planilla_sindical


def _contenido():
    return {
        "snapshot_parametros": {
            "empresa": {"cuit": "30" + "00000000" + "7", "razon_social": "Empresa ficticia"},
        },
        "obligaciones_sindicales": [
            {
                "cct_numero": "414/05", "destino_pago": "ADEF",
                "codigo_boleta": "ADEF_APORTES", "filial_sindical": None,
                "localidad": "Localidad de prueba", "cantidad_empleados": 2,
                "conceptos": {"APORTE_ADEF_REM_414/05": "123.45"},
                "importe": "123.45", "canal_pago": "Aportes en Línea ADEF",
                "url_pago": "https://www.adef.org.ar/sistema-de-aportes-en-linea",
                "regla_vencimiento": "Según boleta emitida", "fuente_pago": "CCT 414/05",
            },
            {
                "cct_numero": "749/18", "destino_pago": "SOECRA",
                "codigo_boleta": "SOECRA_FONDO_FALLECIMIENTO",
                "filial_sindical": "Filial de prueba", "localidad": "Localidad de prueba",
                "cantidad_empleados": 1,
                "conceptos": {"FONDO_FALLECIMIENTO_SOECRA_749/18": "67.89"},
                "importe": "67.89", "canal_pago": "CuotaQ",
                "url_pago": "https://www.cuotaq.com/soecra",
                "regla_vencimiento": "Según boleta", "fuente_pago": "CCT 749/18",
            },
        ],
    }


def test_planilla_sindical_separa_gremios_y_conserva_totales_calculados():
    datos = construir_planilla_sindical(_contenido(), "2026-08", 3)
    texto = datos.decode("utf-8-sig")
    filas = list(csv.DictReader(io.StringIO(texto.split("\r\n", 1)[1]), delimiter=";"))

    assert len(filas) == 2
    assert {f["destino"] for f in filas} == {"ADEF", "SOECRA"}
    assert {f["importe_total"] for f in filas} == {"123.45", "67.89"}
    assert filas[0]["cuit_empleador"] == "30000000007"
    assert "APORTE_ADEF_REM_414/05: 123.45" in filas[0]["conceptos"]


def test_planilla_sindical_vacia_no_fabrica_una_boleta():
    with pytest.raises(ValueError, match="no contiene obligaciones sindicales"):
        construir_planilla_sindical({}, "2026-08", 1)
