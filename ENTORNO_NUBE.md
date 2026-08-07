# SUELDOCLARO — Entorno en la nube (creado 2026-07-29)

## Supabase (base de datos PostgreSQL — plan FREE, $0/mes)

- Proyecto: `sueldoclaro` · ref: `tjwohjcsncyykbycziig` · región: `sa-east-1` (São Paulo)
- Dashboard: https://supabase.com/dashboard/project/tjwohjcsncyykbycziig
- Migración `0001_init` aplicada: 12 tablas + RLS forzada + alembic_version marcada.
- Seed de EJEMPLO cargado (`is_verified=false`): CCT 130/75, 4 escalas, 10 parámetros, 1 amparo FAECYS (L27802:131).

## Rol de aplicación (la app NUNCA se conecta como `postgres`)

- Rol: `sueldoclaro` · `NOBYPASSRLS` · password: `Sc2026!xK9mQv4tRw7pZn3j`
- ⚠️ ROTAR este password antes de usar datos reales (quedó en el historial de SQL).
- Motivo: el rol `postgres` de Supabase tiene `BYPASSRLS=true` y saltea el aislamiento.
  Verificado en vivo el 2026-07-29.

## Cadena de conexión para el backend (variable `SUELDOCLARO_DATABASE_URL`)

Usar el **pooler** de Supabase (el host directo `db.<ref>.supabase.co` es solo IPv6):

```
postgresql+asyncpg://sueldoclaro.tjwohjcsncyykbycziig:PASSWORD@aws-0-sa-east-1.pooler.supabase.com:5432/postgres?prepared_statement_cache_size=0
```

Host VERIFICADO en producción el 2026-07-30 (`aws-1` NO existe para esta región).

## Backend API en Vercel (plan FREE, $0/mes) — DESPLEGADO Y FUNCIONANDO

- URL producción: **https://my-project-six-rho-76.vercel.app**
- Proyecto Vercel: `my-project` (existente reutilizado — el conector no tenía
  permiso para crear proyectos nuevos; renombrarlo a "sueldoclaro-api" desde
  el dashboard de Vercel si se desea).
- Documentación interactiva (Swagger): https://my-project-six-rho-76.vercel.app/docs
- Endpoints: `/auth/register`, `/auth/login`, `/auth/refresh`, `/empleados`
  (ABM + import xlsx + plantilla), `/liquidaciones`, `/health`.
- Sin Redis: refresh tokens y rate limit usan fallback en memoria (suficiente
  por ahora; en serverless cada instancia tiene su memoria — pasar a Upstash
  o a Postgres cuando haya usuarios reales).
- Secretos en `.env` dentro del bundle (mover a Environment Variables del
  dashboard de Vercel antes de usar datos reales, y rotar el JWT secret).
- ⚠️ Endpoint TEMPORAL `/smoke?key=sc-smoke-2026`: corre registro→empleado→
  liquidación de prueba. QUITAR antes de uso real.

## Smoke test de producción — VERIFICADO 2026-07-30

`GET /smoke` contra la API desplegada + Supabase real:
- Registro de estudio (tenant + usuario admin con Argon2) ✅
- Alta de empleado (CUIL validado, RLS activa) ✅
- Liquidación 2026-07 Comercio 130/75, Administrativo A, 5 años:
  bruto **568.750,00** · deducciones **108.062,50** · neto **460.687,50** ✅
- Amparo FAECYS aplicado: APORTE_MODERNIZACION = $0, régimen `previa`,
  artículo `L27802:131` (trazabilidad completa) ✅
- Coincide exactamente con los golden tests de Fase 1. GATE FASE 2 CUMPLIDO.

## Gate de Fase 2 — estado

VERIFICADO EN VIVO (contra Supabase, rol `sueldoclaro`):
- ✅ Tenant A ve solo sus filas.
- ✅ Tenant B ve 0 filas del tenant A.
- ✅ Sin `app.current_tenant` seteado → 0 filas (fail-closed).
- ✅ INSERT cross-tenant (tenant B escribiendo fila del A) → rechazado por RLS (42501).

PENDIENTE:
- ⏳ Suite pytest de integración a nivel API (JWT, middleware, flujos de rutas).
  Bloqueada: el sandbox no tiene Postgres ni root, y no llega por red al host de la BD;
  la PC del usuario no tiene Docker funcionando y su Python 3.15 alpha no compila
  las dependencias. Plan: correrla cuando el backend esté desplegado (smoke tests
  contra la API real) o cuando Docker funcione en la PC.

## Próximos pasos (nube gratuita)

1. Repo en GitHub (gratis) con el contenido de esta carpeta.
2. Render (free): web service desde el Dockerfile de `backend/`, con env
   `SUELDOCLARO_DATABASE_URL` (pooler) y secretos JWT. Nota: free duerme tras 15 min.
3. Smoke tests contra la API desplegada (registro → empleado → liquidación).
4. Frontend Next.js → Vercel (free).

## Cambios 2026-08-06 — LISTOS EN CÓDIGO, PENDIENTE REDEPLOY

Todo lo siguiente está en el repo y probado localmente, pero NO está vivo en
producción todavía porque falta redesplegar el backend en Vercel.

Ya vivo (Supabase es la misma base que usa producción):
- Escalas verificadas con fuente oficial: Comercio 130/75, Camioneros 40/89,
  UOM 260/75 (IMGR). `is_verified=true`.
- Aportes de ley verificados (11% Ley 24.241 · 3% Ley 19.032 · 3% Ley 23.660).
- Parámetros nuevos en `parametro_legal`: UOCRA_APORTE_SOLIDARIO_76/75 (2% no
  afiliados, jun–ago 2026), SANIDAD_SUMA_NR_JUN_JUL/AGO, SANIDAD_DIA_SANIDAD_122/75
  y _108/75 (día de la sanidad, septiembre).
- Sanidad 122/75 y UOCRA 76/75: básicos por categoría marcados PENDIENTE (sin verificar).

En código (requiere redeploy para tener efecto en la liquidación):
- Motor: `_sumas_no_rem_gremio` (suma NR Sanidad + Día de la Sanidad) y aporte
  solidario UOCRA 2%. Tests: backend/tests/test_reglas_gremio.py (pasan).
- Generador LSD: backend/src/infrastructure/lsd/generator.py + test dorado
  backend/tests/test_lsd_golden.py (reproduce el archivo real de ARCA).

BLOQUEO del redeploy (resolver con Héctor):
- El bundle del deploy anterior llevaba los secretos en un `.env` que NO está en
  el repo (DATABASE_URL del pooler + JWT secret). Sin esos valores, un redeploy
  compila pero no conecta a Supabase.
- Tampoco está en el repo el andamiaje de Vercel (vercel.json / api entry) que se
  generó al vuelo la vez anterior.
- Plan seguro: (1) cargar los secretos como Environment Variables en el dashboard
  de Vercel (proyecto my-project) en vez de en .env; (2) redeploy; (3) smoke test
  de una liquidación de Sanidad (debe aparecer la suma NR) y una de UOCRA no
  afiliado (debe aparecer el 2%).
