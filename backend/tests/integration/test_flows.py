"""Flujos: validación CUIL, import xlsx, refresh y liquidación end-to-end."""
from __future__ import annotations

from decimal import Decimal


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


async def _registrar(client, email="dueno@estudio.com"):
    r = await client.post("/auth/register", json={
        "razon_social": "Estudio Demo", "cuit": "30111111118",
        "email": email, "password": "password123",
    })
    assert r.status_code == 201, r.text
    return r.json()


async def test_cuil_invalido_rechazado(app_client):
    tok = (await _registrar(app_client))["access_token"]
    r = await app_client.post("/empleados", headers=_auth(tok), json={
        "nombre": "X", "apellido": "Y", "cuil": "20123456785",  # DV incorrecto
        "fecha_ingreso": "2021-07-01", "cct_numero": "130/75",
        "categoria": "Administrativo A",
    })
    assert r.status_code == 422, r.text


async def test_refresh_rota_token(app_client):
    reg = await _registrar(app_client)
    r = await app_client.post("/auth/refresh", json={"refresh_token": reg["refresh_token"]})
    assert r.status_code == 200, r.text
    nuevo = r.json()
    assert nuevo["access_token"] and nuevo["refresh_token"]
    # El refresh viejo ya no sirve (rotación)
    r2 = await app_client.post("/auth/refresh", json={"refresh_token": reg["refresh_token"]})
    assert r2.status_code == 401


async def test_import_xlsx_reporta_errores_por_fila(app_client):
    from openpyxl import Workbook
    import io

    tok = (await _registrar(app_client))["access_token"]
    wb = Workbook(); ws = wb.active
    ws.append(["nombre", "apellido", "cuil", "fecha_ingreso", "cct_numero", "categoria"])
    ws.append(["Ana", "Gómez", "27123456780", "2020-03-01", "130/75", "Administrativo A"])  # ok
    ws.append(["Mal", "Cuil", "20123456785", "2020-03-01", "130/75", "Administrativo A"])   # cuil malo
    buf = io.BytesIO(); wb.save(buf)

    r = await app_client.post("/empleados/import", headers=_auth(tok),
                              files={"archivo": ("e.xlsx", buf.getvalue(),
                                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["importados"] == 1
    assert len(data["errores"]) == 1
    assert data["errores"][0]["fila"] == 3


async def test_liquidacion_end_to_end_con_amparo(app_client):
    tok = (await _registrar(app_client))["access_token"]
    r = await app_client.post("/empleados", headers=_auth(tok), json={
        "nombre": "Juan", "apellido": "Pérez", "cuil": "20123456786",
        "fecha_ingreso": "2021-07-01", "cct_numero": "130/75",
        "categoria": "Administrativo A", "legajo": "0001", "forma_pago": "1",
    })
    assert r.status_code == 201, r.text

    r = await app_client.post("/liquidaciones", headers=_auth(tok),
                              json={"periodo": "2026-07", "tipo": "mensual", "novedades": []})
    assert r.status_code == 201, r.text
    liq = r.json()
    assert len(liq["detalles"]) == 1
    det = liq["detalles"][0]
    # El seed incluye el amparo FAECYS vigente (L27802:131) -> aporte suspendido
    modern = next(c for c in det["conceptos"] if c["codigo"] == "APORTE_MODERNIZACION")
    assert modern["regimen"] == "previa"
    assert Decimal(det["neto"]) == Decimal("460687.50")
