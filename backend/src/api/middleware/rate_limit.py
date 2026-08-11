"""Rate limiting simple por IP (ventana fija de 1 minuto).

En producción usar Redis (INCR + EXPIRE) para soportar réplicas horizontales;
acá se provee un fallback en memoria suficiente para dev/tests.
"""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from config.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._limite = get_settings().rate_limit_por_minuto
        self._buckets: dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "desconocido"
        ahora = time.time()
        ventana = self._buckets[ip]
        # descarta timestamps de hace más de 60s
        self._buckets[ip] = [t for t in ventana if ahora - t < 60]
        if len(self._buckets[ip]) >= self._limite:
            return JSONResponse({"detail": "Rate limit excedido"}, status_code=429)
        self._buckets[ip].append(ahora)
        return await call_next(request)
