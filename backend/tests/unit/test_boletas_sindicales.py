from domain.entities.boleta_sindical import agrupar_obligaciones_sindicales


def _detalle(emp, cct, destino, boleta, importe, filial=None):
    return {
        "empleado_id": emp,
        "cct_numero": cct,
        "filial_sindical": filial,
        "localidad": "Buenos Aires",
        "conceptos": [{
            "codigo": "APORTE", "importe": importe,
            "destino_pago": destino, "codigo_boleta": boleta,
        }],
    }


def test_empresa_con_dos_convenios_genera_obligaciones_separadas():
    grupos = agrupar_obligaciones_sindicales([
        _detalle("e1", "130/75", "FAECYS", "FAECYS_ART100", "100.00"),
        _detalle("e2", "40/89", "CAMIONEROS", "CAMIONEROS_APORTES", "200.00"),
    ])
    assert len(grupos) == 2
    assert {g["destino_pago"] for g in grupos} == {"FAECYS", "CAMIONEROS"}


def test_mismo_gremio_puede_generar_varias_boletas():
    grupos = agrupar_obligaciones_sindicales([
        _detalle("e1", "76/75", "UOCRA", "UOCRA_CUOTA", "120.00"),
        _detalle("e1", "76/75", "UOCRA", "UOCRA_SEGURO", "80.00"),
    ])
    assert len(grupos) == 2
    assert {g["codigo_boleta"] for g in grupos} == {"UOCRA_CUOTA", "UOCRA_SEGURO"}


def test_misma_boleta_suma_empleados_sin_recalcular():
    grupos = agrupar_obligaciones_sindicales([
        _detalle("e1", "414/05", "ADEF", "ADEF_APORTES", "45515.08"),
        _detalle("e1", "414/05", "ADEF", "ADEF_APORTES", "1082.01"),
        _detalle("e2", "414/05", "ADEF", "ADEF_APORTES", "1000.00"),
    ])
    assert grupos[0]["importe"] == "47597.09"
    assert grupos[0]["cantidad_empleados"] == 2


def test_concepto_sin_destino_no_se_inventa_como_sindical():
    assert agrupar_obligaciones_sindicales([{
        "empleado_id": "e1", "cct_numero": "130/75",
        "conceptos": [{"codigo": "APORTE_JUBILACION", "importe": "100"}],
    }]) == []
