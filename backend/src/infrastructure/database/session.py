"""Engine async y manejo de sesión con contexto de tenant para RLS.

El aislamiento multi-tenant se enforcea en PostgreSQL con Row-Level Security.
Cada sesión setea ``app.current_tenant`` mediante ``set_config(..., true)``
(local a la transacción), y las políticas RLS filtran por ese valor. El
``tenant_id`` proviene SIEMPRE del JWT (nunca del body ni de query params).
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import get_settings

_settings = get_settings()

engine = create_async_engine(_settings.database_url, echo=False, pool_pre_ping=True)
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
