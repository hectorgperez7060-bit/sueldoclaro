# SUELDOCLARO

SaaS de liquidación de sueldos para Argentina (Ley 27.802 de Modernización
Laboral + Decreto 407/2026, recibo Anexo III). Orientado a estudios contables y
PyMEs. Ver `SUELDOCLARO_PROMPT_MAESTRO_v2.md` (en la carpeta del proyecto) para
la especificación completa y `DECISIONS.md` para las decisiones de diseño.

> ⚠️ Todos los valores legales cargados son **de ejemplo** (`is_verified = false`).
> No usar para liquidaciones reales hasta que un contador matriculado verifique
> los parámetros vigentes.

## Estado

- **Fase 1 — Dominio y motor de cálculo:** ✅ implementada. Dominio puro, value
  objects, motor con estrategias por amparo, golden tests (24 en verde).
- **Fase 2 — Persistencia y API:** ✅ implementada. PostgreSQL + RLS, repos,
  auth JWT (access 15m + refresh rotativo, argon2), middleware (tenant/rate
  limit), rutas de auth/empleados/liquidaciones, audit log, import xlsx,
  migración Alembic con RLS, docker-compose, y suite de integración con test de
  aislamiento multi-tenant. (Ver nota de ejecución abajo.)
- Fases 3–4 (recibos + frontend, updater legal): pendientes.

## Cómo correr (Fase 2)

```bash
# 1) Levantar infra + API (aplica migración Alembic con RLS automáticamente)
docker compose up --build        # API en http://localhost:8000 (OpenAPI en /docs)

# 2) Correr toda la suite (unit + integración) contra un Postgres de test
cd backend
pip install -e ".[dev]"
createdb sueldoclaro_test        # o: docker exec -it <pg> createdb -U sueldoclaro sueldoclaro_test
export SUELDOCLARO_TEST_DATABASE_URL=postgresql+asyncpg://sueldoclaro:sueldoclaro@localhost:5432/sueldoclaro_test
pytest -v
```

Los tests de integración se **saltean automáticamente** si no hay un PostgreSQL
accesible (los tests unitarios del dominio siguen corriendo sin DB).

### Gate de Fase 2
`tests/integration/test_isolation.py` verifica el aislamiento multi-tenant: un
usuario del tenant A no puede leer ni listar datos del tenant B (404 / lista
vacía), enforced por Row-Level Security en PostgreSQL.

## Estructura (Fase 1)

```
backend/
├── src/domain/
│   ├── value_objects/   # Dinero (Decimal), Cuil (módulo 11), Periodo
│   ├── entities/        # Empleado, Concepto, parámetros, ResultadoLiquidacion
│   ├── payroll_engine/  # Motor de cálculo + CctConfig + estrategias por amparo
│   └── repositories/    # Interfaces (Protocol) — sin ORM
├── seed/                # Datos de ejemplo (is_verified = false)
└── tests/unit/
    ├── test_cuil.py     # válidos e inválidos (módulo 11)
    ├── test_dinero.py   # Decimal + ROUND_HALF_UP + prohibido float
    ├── test_golden.py   # loader de casos golden
    └── golden/*.yaml    # casos legibles por un contador
```

## Correr los tests

```bash
cd backend
pip install -e ".[dev]"      # pytest + pyyaml
pytest -v
```

## Gate de la Fase 1

Todos los golden tests en verde, incluyendo el mismo empleado **con y sin
amparo** (netos distintos y trazables). Ver `tests/unit/golden/`.
