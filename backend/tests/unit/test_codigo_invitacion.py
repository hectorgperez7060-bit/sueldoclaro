import hashlib

from fastapi.testclient import TestClient

from api.routes import auth
from api.routes.auth import codigo_invitacion_valido
from main import create_app
from ui_page import HTML


def test_codigo_beta_admite_mayusculas_y_espacios_pero_no_otro_valor(monkeypatch):
    codigo = "codigo-de-prueba"
    resumen = hashlib.sha256(codigo.encode("utf-8")).hexdigest()
    monkeypatch.setattr(auth, "INVITE_CODE_SHA256", resumen)
    assert codigo_invitacion_valido(codigo)
    assert codigo_invitacion_valido("  CODIGO-DE-PRUEBA  ")
    assert not codigo_invitacion_valido("otro-codigo")
    assert not codigo_invitacion_valido("")


def test_registro_directo_sin_codigo_correcto_es_rechazado_antes_de_crear_datos():
    cliente = TestClient(create_app())
    respuesta = cliente.post("/auth/register", json={
        "razon_social": "Empresa ficticia",
        "cuit": "30" + "00000000" + "7",
        "email": "prueba@example.com",
        "password": "password123",
        "codigo_invitacion": "incorrecto",
        "modo_cuenta": "EMPRESA",
    })
    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "El código de invitación no es válido"


def test_registro_directo_sin_codigo_es_rechazado_por_el_contrato():
    cliente = TestClient(create_app())
    respuesta = cliente.post("/auth/register", json={
        "razon_social": "Empresa ficticia",
        "cuit": "30" + "00000000" + "7",
        "email": "prueba@example.com",
        "password": "password123",
        "modo_cuenta": "EMPRESA",
    })
    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "El código de invitación no es válido"


def test_interfaz_pide_y_envia_el_codigo_sin_publicar_su_valor():
    assert 'id="rzCodigoInvitacion"' in HTML
    assert "codigo_invitacion:$('rzCodigoInvitacion').value.trim()" in HTML
    campo = HTML[HTML.index('id="rzCodigoInvitacion"'):]
    assert "value=" not in campo[:campo.index(">")]
