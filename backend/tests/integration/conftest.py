"""Fixtures de integración: DB Postgres de test + cliente httpx sobre la app.

Requiere un PostgreSQL accesible (RLS es específico de Postgres). Si no hay DB,
la suite de integración se saltea (los tests unitarios siguen corriendo).
Config: SUELDOCLARO_TEST_DATABASE_URL (async, asyncpg).
"""
from __future__ import annotations

import os

import pytest
import pytest_asyncio

TEST_DB = os.environ.get(
    "SUELDOCLARO_TEST_DATABASE_URL",
    "postgresql+asyncpg://sueldoclaro:sueldoclaro@localhost:5432/sueldoclaro_test",
)
# La app crea su engine desde SUELDOCLARO_DATABASE_URL al importarse: lo fijamos ANTES.
os.environ["SUELDOCLARO_DATABASE_URL"] = TEST_DB


@pytest_asyncio.fixture(scope="function")
async def app_client():
    from httpx import ASGITransport, AsyncClient

    from infrastructure.database.bootstrap import (
        borrar_esquema,
        crear_esquema,
        sembrar_parametros,
    )
    from infrastructure.database.session import SessionFactory, engine

    # Verifica conectividad; si no hay DB, se saltea.
    try:
        async with engine.begin():
            pass
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"PostgreSQL de test no disponible: {e}")

    await borrar_esquema(engine)
    await crear_esquema(engine)
    async with SessionFactory() as s:
        async with s.begin():
            await sembrar_parametros(s)

    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await borrar_esquema(engine)


async def _registrar(client, razon, cuit, email):
    r = await client.post("/auth/register", json={
        "razon_social": razon, "cuit": cuit, "email": email, "password": "password123",
    })
    assert r.status_code == 201, r.text
    return r.json()


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
