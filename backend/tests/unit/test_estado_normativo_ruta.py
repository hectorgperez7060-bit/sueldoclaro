"""El semáforo del convenio nunca había funcionado.

El número de convenio lleva una barra ("749/18"). El navegador lo manda como
``749%2F18`` y llega decodificado, así que la ruta ``/convenios/{numero}/
estado-normativo`` veía un segmento de más y no enganchaba con nada: la
pantalla de liquidar mostraba siempre "No se pudo consultar el estado del
convenio: Not Found", para cualquier convenio.
"""
from fastapi.testclient import TestClient

from main import create_app


CLIENTE = TestClient(create_app(), raise_server_exceptions=False)

# 404 = la ruta no engancha. 401 = enganchó y pidió sesión, que es lo correcto
# para un pedido sin token.
SIN_SESION = 401


def test_el_semaforo_engancha_con_un_convenio_que_lleva_barra():
    for numero in ("749%2F18", "130%2F75", "389%2F04", "76%2F75"):
        r = CLIENTE.get(f"/convenios/{numero}/estado-normativo?periodo=2026-08")
        assert r.status_code == SIN_SESION, (
            f"{numero}: la ruta no engancha, devuelve {r.status_code} {r.text[:60]}"
        )


def test_tambien_engancha_si_la_barra_llega_sin_codificar():
    """Vercel decodifica el %2F antes de pasar el pedido: llega la barra cruda."""
    r = CLIENTE.get("/convenios/749/18/estado-normativo?periodo=2026-08")
    assert r.status_code == SIN_SESION, r.text[:80]


def test_el_parametro_glotón_no_se_come_las_otras_rutas_de_convenios():
    esquema = create_app().openapi()["paths"]
    assert "/convenios/paquetes" in esquema
    assert "/convenios/gestor-normativo" in esquema
    assert "/convenios/{numero}/estado-normativo" in esquema
