"""Gate de Fase 2: aislamiento multi-tenant (RLS). Tenant A no ve datos de B."""
from __future__ import annotations


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _registrar(client, razon, cuit, email):
    r = await client.post("/auth/register", json={
        "razon_social": razon, "cuit": cuit, "email": email, "password": "password123",
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _crear_empleado(client, token, apellido="Pérez", cuil="20123456786"):
    r = await client.post("/empleados", headers=_auth(token), json={
        "nombre": "Juan", "apellido": apellido, "cuil": cuil,
        "fecha_ingreso": "2021-07-01", "cct_numero": "130/75",
        "categoria": "Administrativo A", "legajo": "0001",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def test_tenant_no_accede_a_empleado_de_otro(app_client):
    a = await _registrar(app_client, "Estudio A", "30111111118", "a@estudio.com")
    b = await _registrar(app_client, "Estudio B", "30222222226", "b@estudio.com")

    emp_a = await _crear_empleado(app_client, a["access_token"], "AperA", "20123456786")

    # B intenta leer el empleado de A -> 404 (RLS lo hace invisible)
    r = await app_client.get(f"/empleados/{emp_a}", headers=_auth(b["access_token"]))
    assert r.status_code == 404, r.text

    # A sí lo ve
    r = await app_client.get(f"/empleados/{emp_a}", headers=_auth(a["access_token"]))
    assert r.status_code == 200


async def test_listado_no_filtra_datos_cruzados(app_client):
    a = await _registrar(app_client, "Estudio A", "30111111118", "a@estudio.com")
    b = await _registrar(app_client, "Estudio B", "30222222226", "b@estudio.com")

    await _crear_empleado(app_client, a["access_token"], "DeA", "20123456786")

    ra = await app_client.get("/empleados", headers=_auth(a["access_token"]))
    rb = await app_client.get("/empleados", headers=_auth(b["access_token"]))
    assert ra.status_code == 200 and rb.status_code == 200
    assert len(ra.json()) == 1
    assert len(rb.json()) == 0  # B no ve nada de A


async def test_sin_token_401(app_client):
    r = await app_client.get("/empleados")
    assert r.status_code in (401, 403)
