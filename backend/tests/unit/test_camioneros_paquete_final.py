from decimal import Decimal
from pathlib import Path

import pytest

from domain.entities.novedad import DatosNovedadMensual
from domain.payroll_engine.camioneros import novedades_camioneros_desde_dict
from ui_page import HTML


BASE = {
    "rama": "larga_distancia",
    "zona": "COEF_1_20",
    "camara_frio": False,
    "dias_comida": 2,
    "kilometros_viatico": "800.5",
    "dias_en_viaje": 2,
}


def test_detalle_camioneros_se_valida_y_persiste_sin_importes():
    datos = DatosNovedadMensual(periodo="2026-08", camioneros_detalle=BASE)
    persistido = datos.para_persistir()["camioneros_detalle"]
    novedad = novedades_camioneros_desde_dict(persistido)
    assert novedad.zona == "COEF_1_20"
    assert novedad.kilometros_viatico == Decimal("800.5")
    assert "importe" not in persistido and "basico" not in persistido


@pytest.mark.parametrize("cambio", [
    {"rama": "inventada"}, {"zona": "SUR"}, {"camara_frio": "sí"},
    {"dias_comida": -1}, {"campo_desconocido": 1},
])
def test_detalle_camioneros_rechaza_datos_inseguros(cambio):
    with pytest.raises(ValueError):
        DatosNovedadMensual(periodo="2026-08", camioneros_detalle={**BASE, **cambio})


def test_interfaz_camioneros_cubre_carga_edicion_y_contexto():
    assert 'id="novCamioneros"' in HTML
    assert "emp.cct_numero==='40/89'" in HTML
    assert "camioneros_detalle:datosCamioneros()" in HTML
    assert "cargarCamioneros(n.camioneros_detalle||{})" in HTML
    for identificador in ("camRama", "camZona", "camKmViatico", "camCordillera", "camFrontera"):
        assert f'id="{identificador}"' in HTML


def test_migracion_final_es_idempotente_y_no_habilita_recibo_sin_verificacion():
    sql = Path("backend/migrations/030_novedades_camioneros_final.sql").read_text()
    assert "ADD COLUMN IF NOT EXISTS camioneros_detalle" in sql
    assert "BLOQUEADA_HASTA_INCIDENCIAS_VERIFICADAS" in sql
    assert "ON CONFLICT (cct_numero, paquete_version) DO UPDATE" in sql
    assert "habilitada_liquidacion = true" not in sql.lower()
