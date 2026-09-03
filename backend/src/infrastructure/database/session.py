"""Engine async y manejo de sesión con contexto de tenant para RLS.

El aislamiento multi-tenant se enforcea en PostgreSQL con Row-Level Security.
Cada sesión setea ``app.current_tenant`` mediante ``set_config(..., true)``
(local a la transacción), y las políticas RLS filtran por ese valor. El
``tenant_id`` proviene SIEMPRE del JWT (nunca del body ni de query params).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from config.settings import get_settings

_settings = get_settings()

# En Vercel cada request puede caer en una instancia distinta y la instancia
# queda congelada entre invocaciones. Un pool propio por instancia deja
# conexiones tomadas que nunca se devuelven y el pooler de Supabase se llena
# (EMAXCONNSESSION: max clients reached in session mode). Sin pool, cada
# request abre y cierra su conexion.
_ES_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

# Detras de un pooler (Supavisor / PgBouncer) hay que apagar el cache de
# sentencias preparadas de asyncpg: la conexion no es siempre la misma.
_CONNECT_ARGS: dict = {}
if _settings.database_url.startswith("postgresql+asyncpg"):
    _CONNECT_ARGS = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
    }

if _ES_SERVERLESS:
    engine = create_async_engine(
        _settings.database_url,
        echo=False,
        poolclass=NullPool,
        connect_args=_CONNECT_ARGS,
    )
else:
    engine = create_async_engine(
        _settings.database_url,
        echo=False,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=0,
        pool_recycle=300,
        connect_args=_CONNECT_ARGS,
    )

SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def _set_tenant(session: AsyncSession, tenant_id: Optional[str]) -> None:
    # set_config(name, value, is_local=true) => vive solo en la transacción actual
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, true)"),
        {"tid": str(tenant_id) if tenant_id else ""},
    )


@asynccontextmanager
async def tenant_session(tenant_id: Optional[str]) -> AsyncIterator[AsyncSession]:
    """Abre una sesión dentro de una transacción con el tenant seteado."""
    async with SessionFactory() as session:
        async with session.begin():
            await _set_tenant(session, tenant_id)
            yield session


@asynccontextmanager
async def plain_session() -> AsyncIterator[AsyncSession]:
    """Sesión sin tenant (flujos de auth: registro / login / refresh)."""
    async with SessionFactory() as session:
        async with session.begin():
            yield session


async def dispose_engine() -> None:
    await engine.dispose()
