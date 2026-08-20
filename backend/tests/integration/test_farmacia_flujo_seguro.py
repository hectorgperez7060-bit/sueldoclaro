"""Flujo SEGURO de Farmacia 414/05 contra Postgres real (rama farmacia-segura).

Aplica la migración 010 real (datos versionados en las tablas de escalas y
parámetros) y verifica: catálogo con las 6 categorías, las 5 restantes sin
escala (bloqueo con mensaje), julio verificado, agosto provisorio confirmado,
agosto sin NR, y aislamiento multiempresa.
"""
from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).parents[2]
CATEGORIAS = (
    "Empleado Especializado de Farmacia",   # única con escala verificada
    "Categoría Inicial A", "Categoría Inicial B",
    "Cajero, Perfumería y Administrativo", "Empleado de Farmacia", "Farmacéutico",
)


def _sub(token: str) -> str:
    payload = token.split(".")[1] + "=="
    return json.loads(base64.urlsafe_b64decode(payload))["sub"]


def _cuil(prefijo: int, dni: int) -> str:
    base = f"{prefijo:02d}{dni:08d}"
    pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    resto = sum(int(d) * p for d, p in zip(base, pesos)) % 11
    ver = 11 - resto
    if ver == 11:
        ver = 0
    assert ver != 10, "elegir otro DNI"
    return base + str(ver)


async def _sembrar_referencia():
    """Cct 414/05 + aportes ADEF (mig 004) + escala/NR verificados (mig 010)."""
    from infrastructure.database.session import engine
    sql_cct = (
        "INSERT INTO public.cct (id, numero, nombre, sindicato, cuota_sindical_pct, "
        "antiguedad_pct_por_anio, presentismo_divisor, divisor_horas, aplica_presentismo, "
        "aplica_cuota_sindical, activo) VALUES (gen_random_uuid(), '414/05', 'Farmacia', "
        "'ADEF', 0, 0, 12, 200, false, false, true) ON CONFLICT (numero) DO NOTHING;"
    )
    mig004 = (RAIZ / "migrations" / "004_aportes_adef_414_05.sql").read_text()
    mig010 = (RAIZ / "migrations" / "010_escala_verificada_farmacia_414_05.sql").read_text()
    async with engine.begin() as conn:
        raw = await conn.get_raw_connection()
        drv = raw.driver_connection           # asyncpg: protocolo simple, multi-statement
        await drv.execute(sql_cct)
        await drv.execute(mig004)
        await drv.execute(mig010)


async def _crear_empleado(tenant_id, categoria, cuil, apellido):
    from infrastructure.database.repositories import EmpleadoRepo
    from infrastructure.database.session import tenant_session
    async with tenant_session(tenant_id) as s:
        await EmpleadoRepo(s).crear(uuid.UUID(tenant_id), {
            "nombre": "Emp", "apellido": apellido, "cuil": cuil,
            "fecha_ingreso": date(2018, 4, 9), "cct_numero": "414/05",
            "categoria": categoria, "afiliado_sindicato": True,
        })


async def _registrar(app_client, razon, cuit, email):
    r = await app_client.post("/auth/register", json={
        "razon_social": razon, "cuit": cuit, "email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    return r.json()["tenant_id"], _sub(r.json()["access_token"])


async def test_catalogo_seis_categorias_y_cinco_sin_escala(app_client):
    await _sembrar_referencia()
    tenant_id, usuario_id = await _registrar(
        app_client, "Farmacia A", "30123456781", "a@farma.com")

    # Catálogo: las 6 categorías oficiales quedan seleccionables en encuadramiento.
    from infrastructure.database.repositories import ParametrosRepo
    from infrastructure.database.session import plain_session
    async with plain_session() as s:
        catalogo = await ParametrosRepo(s).catalogo_encuadramientos()
    assert set(CATEGORIAS) <= catalogo["414/05"]
    assert len(catalogo["414/05"]) == 6

    # Un empleado por cada categoría.
    for i, cat in enumerate(CATEGORIAS):
        await _crear_empleado(tenant_id, cat, _cuil(20, 20000000 + i), f"Ap{i}")

    from application.use_cases.liquidar_periodo import LiquidarPeriodo
    jul = await LiquidarPeriodo().ejecutar(tenant_id, "2026-07", "mensual", {}, usuario_id)

    # Solo el Especializado liquida; las otras cinco se bloquean con el mensaje.
    assert len(jul["detalles"]) == 1
    basico = next(c for c in jul["detalles"][0]["conceptos"] if c["codigo"] == "BASICO")
    assert basico["importe"] == "1828730.75"
    nr = next(c for c in jul["detalles"][0]["conceptos"] if c["codigo"].startswith("FARMACIA_NR"))
    assert nr["importe"] == "54100.54"
    # ADEF 2% remunerativo separado (acá sin premio de feriado: 2% de básico+antigüedad).
    adef_rem = next(c for c in jul["detalles"][0]["conceptos"] if c["codigo"] == "APORTE_ADEF_REM_414/05")
    assert adef_rem["importe"] == "43889.54"

    assert len(jul["bloqueos"]) == 5
    for b in jul["bloqueos"]:
        assert b["motivo"] == "Sin escala salarial verificada para el período"
        assert b["categoria"] != "Empleado Especializado de Farmacia"


async def test_agosto_provisorio_confirmado_sin_nr(app_client):
    await _sembrar_referencia()
    tenant_id, usuario_id = await _registrar(
        app_client, "Farmacia B", "30222222226", "b@farma.com")
    await _crear_empleado(tenant_id, "Empleado Especializado de Farmacia",
                          _cuil(20, 21000000), "Esp")
    from application.use_cases.liquidar_periodo import LiquidarPeriodo

    # Agosto sin confirmar: no liquida, exige confirmación (provisorio).
    ago = await LiquidarPeriodo().ejecutar(tenant_id, "2026-08", "mensual", {}, usuario_id)
    assert len(ago["detalles"]) == 0 and len(ago["bloqueos"]) == 1
    b = ago["bloqueos"][0]
    assert b["provisorio"] is True and b["requiere_confirmacion"] is True
    assert b["motivo"] == "Valor provisorio: última escala verificada disponible"

    # Agosto confirmado: liquida como provisorio, reusando julio, SIN NR.
    ok = await LiquidarPeriodo().ejecutar(
        tenant_id, "2026-08", "mensual", {}, usuario_id, confirmar_provisorios=True)
    assert len(ok["detalles"]) == 1
    det = ok["detalles"][0]
    assert det["escala_provisoria"]["nota"] == "Valor provisorio: última escala verificada disponible"
    basico = next(c for c in det["conceptos"] if c["codigo"] == "BASICO")
    assert basico["importe"] == "1828730.75"
    assert not any(c["codigo"].startswith("FARMACIA_NR") for c in det["conceptos"]), "no trasladar el NR"


async def test_aislamiento_multiempresa(app_client):
    await _sembrar_referencia()
    a_id, a_u = await _registrar(app_client, "Est A", "30111111118", "ma@farma.com")
    b_id, b_u = await _registrar(app_client, "Est B", "30333333334", "mb@farma.com")
    await _crear_empleado(a_id, "Empleado Especializado de Farmacia", _cuil(20, 22000000), "A")
    await _crear_empleado(b_id, "Empleado Especializado de Farmacia", _cuil(20, 23000000), "B")

    from application.use_cases.liquidar_periodo import LiquidarPeriodo
    a = await LiquidarPeriodo().ejecutar(a_id, "2026-07", "mensual", {}, a_u)
    b = await LiquidarPeriodo().ejecutar(b_id, "2026-07", "mensual", {}, b_u)
    assert len(a["detalles"]) == 1 and len(b["detalles"]) == 1
    assert a["detalles"][0]["empleado_id"] != b["detalles"][0]["empleado_id"]
