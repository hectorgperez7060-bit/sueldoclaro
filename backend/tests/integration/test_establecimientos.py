from datetime import date
import uuid

from sqlalchemy import select

from infrastructure.database import models as m
from infrastructure.database.session import tenant_session


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _registrar(client):
    r = await client.post("/auth/register", json={
        "razon_social": "Empresa Lugares", "cuit": "30777777774",
        "email": "lugares@estudio.com", "password": "password123",
    })
    assert r.status_code == 201, r.text
    return r.json()


async def _establecimiento(client, token, nombre):
    r = await client.post("/establecimientos", headers=_auth(token), json={
        "nombre": nombre, "domicilio": f"Calle {nombre} 100",
        "localidad": "Merlo", "provincia": "Buenos Aires",
        "actividad": "Comercio", "activo": True,
    })
    assert r.status_code == 201, r.text
    return r.json()


def _empleado(establecimiento_id, desde="2024-01-01"):
    return {
        "nombre": "Juan", "apellido": "Lugares", "cuil": "20123456786",
        "fecha_ingreso": "2024-01-01", "cct_numero": "130/75",
        "categoria": "Administrativo A", "legajo": "L-1", "forma_pago": "1",
        "establecimiento_id": establecimiento_id, "lugar_trabajo_desde": desde,
    }


async def test_cambio_de_lugar_cierra_historial_y_rechaza_inactivo(app_client):
    sesion = await _registrar(app_client)
    token, tid = sesion["access_token"], sesion["tenant_id"]
    primero = await _establecimiento(app_client, token, "Central")
    segundo = await _establecimiento(app_client, token, "Sucursal")

    desactivar = dict(segundo, activo=False)
    desactivar.pop("id")
    r = await app_client.put(
        f"/establecimientos/{segundo['id']}", headers=_auth(token), json=desactivar,
    )
    assert r.status_code == 200, r.text
    r = await app_client.post("/empleados", headers=_auth(token), json=_empleado(segundo["id"]))
    assert r.status_code == 422

    activar = dict(segundo, activo=True)
    activar.pop("id")
    assert (await app_client.put(
        f"/establecimientos/{segundo['id']}", headers=_auth(token), json=activar,
    )).status_code == 200

    creado = await app_client.post(
        "/empleados", headers=_auth(token), json=_empleado(primero["id"]),
    )
    assert creado.status_code == 201, creado.text
    empleado_id = creado.json()["id"]
    cambio = await app_client.put(
        f"/empleados/{empleado_id}", headers=_auth(token),
        json=_empleado(segundo["id"], "2024-06-01"),
    )
    assert cambio.status_code == 200, cambio.text

    async with tenant_session(tid) as s:
        filas = list((await s.execute(
            select(m.EmpleadoEstablecimientoHistorial)
            .where(m.EmpleadoEstablecimientoHistorial.empleado_id == uuid.UUID(empleado_id))
            .order_by(m.EmpleadoEstablecimientoHistorial.vigente_desde)
        )).scalars())
    assert [(f.vigente_desde, f.vigente_hasta) for f in filas] == [
        (date(2024, 1, 1), date(2024, 5, 31)),
        (date(2024, 6, 1), None),
    ]
