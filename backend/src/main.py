"""Punto de entrada de la API SUELDOCLARO (FastAPI)."""
from __future__ import annotations

import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from api.dependencies.auth import Principal, require_tenant
from api.middleware.rate_limit import RateLimitMiddleware
from api.routes import auth, convenios, empleados, liquidaciones
from infrastructure.database import models as m
from infrastructure.database.session import dispose_engine, plain_session
from ui_page import HTML as UI_HTML


def create_app() -> FastAPI:
    app = FastAPI(
        title="SUELDOCLARO API",
        version="0.6.0",
        description="Liquidación de sueldos Argentina (Ley 27.802 / Decreto 407/2026)",
    )
    app.add_middleware(RateLimitMiddleware)

    app.include_router(auth.router)
    app.include_router(convenios.router)
    app.include_router(empleados.router)
    app.include_router(liquidaciones.router)

    @app.exception_handler(ValueError)
    async def _value_error(_: Request, exc: ValueError):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.get("/", include_in_schema=False)
    async def home():
        return HTMLResponse(UI_HTML)

    @app.get("/empresa", tags=["empresa"])
    async def empresa(principal: Principal = Depends(require_tenant)):
        """Datos del empleador (para la cabecera del recibo)."""
        async with plain_session() as s:
            t = await s.get(m.Tenant, uuid.UUID(principal.tenant_id))
            if t is None:
                return {"razon_social": "", "cuit": ""}
            return {"razon_social": t.razon_social, "cuit": t.cuit}

    @app.get("/health", tags=["infra"])
    async def health():
        return {"status": "ok"}

    @app.get("/ready", tags=["infra"])
    async def ready():
        return {"status": "ready"}

    @app.on_event("shutdown")
    async def _shutdown():
        await dispose_engine()

    return app


app = create_app()
