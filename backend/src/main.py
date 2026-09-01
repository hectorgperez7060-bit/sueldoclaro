"""Punto de entrada de la API SUELDOCLARO (FastAPI)."""
from __future__ import annotations

import base64
import logging
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from sqlalchemy.exc import DBAPIError

from api.dependencies.auth import Principal, require_tenant
from api.middleware.rate_limit import RateLimitMiddleware
from api.routes import auth, carpetas, convenios, empleados, establecimientos, exportaciones, liquidaciones, novedades, recibos
from infrastructure.database import models as m
from infrastructure.database.session import dispose_engine, plain_session
from ui_page import HTML as UI_HTML
from pwa_assets import ICON_192_B64, ICON_512_B64


logger = logging.getLogger("sueldoclaro")


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
    app.include_router(establecimientos.router)
    app.include_router(liquidaciones.router)
    app.include_router(novedades.router)
    app.include_router(carpetas.router)
    app.include_router(exportaciones.router)
    app.include_router(recibos.router)

    @app.exception_handler(ValueError)
    async def _value_error(_: Request, exc: ValueError):
        return JSONResponse({"detail": str(exc)}, status_code=422)

    @app.exception_handler(Exception)
    async def _unexpected_error(request: Request, exc: Exception):
        """Devuelve un diagnóstico seguro y conserva el detalle en los logs."""
        logger.exception("Error no controlado en %s", request.url.path, exc_info=exc)
        detail = "Error interno del servidor"
        if isinstance(exc, DBAPIError):
            sqlstate = getattr(exc.orig, "sqlstate", "")
            detail = {
                "42P01": "La base de producción no tiene una tabla requerida",
                "42703": "La base de producción no tiene una columna requerida",
                "42501": "La aplicación no tiene permiso para usar una tabla requerida",
                "23503": "La operación referencia datos relacionados que no existen",
                "23505": "La operación intentó crear un registro duplicado",
            }.get(sqlstate, "La base de datos rechazó la operación")
        return JSONResponse({"detail": detail}, status_code=500)

    @app.get("/", include_in_schema=False)
    async def home():
        return HTMLResponse(\n            UI_HTML,\n            headers={"Cache-Control": "no-store, max-age=0"},\n        )

    @app.get("/manifest.webmanifest", include_in_schema=False)
    async def manifest():
        return JSONResponse({
            "name": "Sueldo Claro",
            "short_name": "Sueldo Claro",
            "description": "Gestión laboral y liquidación de haberes clara y trazable",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#f2f7f6",
            "theme_color": "#087f72",
            "orientation": "any",
            "icons": [
                {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
                {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
            ],
        }, media_type="application/manifest+json")

    @app.get("/icon-{size}.png", include_in_schema=False)
    async def pwa_icon(size: int):
        data = ICON_512_B64 if size == 512 else ICON_192_B64 if size == 192 else None
        if data is None:
            return Response(status_code=404)
        return Response(
            base64.b64decode(data), media_type="image/png",
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    @app.get("/sw.js", include_in_schema=False)
    async def service_worker():
        script = """const CACHE='sueldo-claro-shell-v2';
const SHELL=['/','/manifest.webmanifest','/icon-192.png','/icon-512.png'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET') return;
  const u=new URL(e.request.url);
  if(u.origin!==self.location.origin) return;
  if(!SHELL.includes(u.pathname)) return;
  e.respondWith(fetch(e.request).then(r=>{const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy));return r;}).catch(()=>caches.match(e.request)));
});"""
        return Response(
            script, media_type="application/javascript",
            headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-store, max-age=0"},
        )

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
