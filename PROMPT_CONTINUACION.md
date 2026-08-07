# PROMPT DE CONTINUACIÓN — SUELDOCLARO

> Pegá este archivo al inicio de una sesión nueva para retomar el proyecto con
> contexto completo. Está escrito como instrucciones para vos (Claude).

## Rol y objetivo
Estás construyendo **SUELDOCLARO**, un SaaS de liquidación de sueldos para
Argentina (estudios contables y PyMEs), según el `SUELDOCLARO_PROMPT_MAESTRO_v2.md`
que vive en la carpeta del proyecto. Se ejecuta **por fases**, validando cada una
antes de seguir. La base legal es real y verificada: **Ley 27.802 de Modernización
Laboral** + **Decreto 407/2026** (recibo Anexo III de 4 secciones + gráfico de
torta, vigente 01/06/2026), con régimen de **amparos judiciales por CCT** que
suspenden artículos según el convenio.

## Ubicación y entorno
- Proyecto: `C:\Users\usuario\OneDrive\Favoritos\sueldoClaeo` (carpeta propia,
  SEPARADA del proyecto "mayolista.2" del usuario — no mezclar).
- El usuario es **no-programador**, habla español, prefiere respuestas concisas y
  directas. Quiere una herramienta que **"devuelva lo que se le pide"** (flexible),
  y aclaró que funciones no incluidas en el prompt original igual se deben agregar
  si son útiles.
- Restricciones de entorno vividas (tenerlas en cuenta):
  - El **shell del sandbox se traba** con frecuencia (procesos colgados, timeouts).
    Cuando pase, seguí trabajando con las herramientas de archivo (Write/Edit) y
    corré tests copiando a `/tmp` local (fuera del mount OneDrive) — ahí pytest
    corre limpio.
  - La carpeta es **OneDrive**: escrituras vía Write funcionan; `rm` en bash puede
    dar "Operation not permitted" (usar el permiso de borrado de cowork).
  - La PC del usuario tiene **Docker Desktop instalado pero el motor no arranca**
    (WSL2 recién instalado; falta reiniciar y/o activar virtualización en BIOS).
    Tiene **Python 3.15.0a7** instalado y funcionando.

## Estado por fases

### Fase 1 — Dominio y motor de cálculo ✅ (implementada y verificada)
Dominio puro (sin BD, sin API), en `backend/src/domain/`:
- `value_objects/`: `Dinero` (Decimal siempre; ROUND_HALF_UP solo en el importe
  final de cada concepto; prohíbe float), `Cuil` (validación real módulo 11),
  `Periodo`.
- `entities/`: `Empleado` (incluye `proporcion_jornada`), `Concepto` (con
  `regimen` y `articulo_amparo` para trazabilidad), parámetros legales, `ResultadoLiquidacion`.
- `payroll_engine/`: `MotorLiquidacion` + `CctConfig` + `Novedades`.
  Estrategias por amparo: cada concepto afectado declara `regla_ley_27802` y
  `regla_previa`; el `AmparoSet` decide cuál aplicar por CCT/período.
- **24 golden tests en verde** (`backend/tests/unit/`, casos YAML legibles por un
  contador). Correr con: copiar `backend` a `/tmp`, `pytest -q` (no en OneDrive).

Conceptos que el motor ya liquida: básico de escala o pactado, antigüedad,
presentismo, horas extra 50%/100%, **jornada parcial** (LCT 92 ter, prorratea
todo el recibo), SAC, vacaciones (LCT 150/151), aportes del trabajador
(jubilación, Ley 19.032, obra social, cuota sindical), tope SIPA, contribuciones
patronales, y el régimen de amparos.

### Fase 2 — Persistencia y API ✅ (escrita) / ⚠️ GATE NO EJECUTADO
Todo el código está en `backend/src/{infrastructure,application,api}`, más
migración Alembic, docker-compose y suite de integración. **Falta ejecutarlo**:
el shell se trabó y la PC del usuario no pudo levantar Docker/Postgres. El gate de
Fase 2 (tests de aislamiento multi-tenant en verde) **no está verificado**.
Incluye: modelos SQLAlchemy 2.0 async, **RLS** (política por tenant con
`app.current_tenant`), Alembic `0001_init` con RLS, auth JWT (access 15m + refresh
rotativo, argon2), middleware (tenant/rate limit/audit), rutas auth/empleados/
liquidaciones, audit log append-only, import xlsx con reporte por fila,
docker-compose (postgres/redis/mailhog/backend/worker).

### Feature agregada fuera del prompt (a pedido del usuario)
**Jornada parcial** (`proporcion_jornada` en Empleado/DTO/ORM/engine): media
jornada = 0.5 prorratea básico y en cascada antigüedad, presentismo, aportes y
contribuciones. Verificado en el demo: neto media jornada $227.500 = exactamente
la mitad de $455.000.

## Cómo lo corre el usuario HOY (sin Docker, sin BD)
Archivo `backend/demo_liquidacion.py` (solo Python, sin dependencias externas):
```
cd C:\Users\usuario\OneDrive\Favoritos\sueldoClaeo\backend
python demo_liquidacion.py
```
Muestra el recibo de Comercio 130/75 con y sin amparo, y en media jornada.
**Números verificados en pantalla** (empleado Administrativo A, 5 años, 2026-07):
- Sin amparo: bruto 568.750,00 · deducciones 113.750,00 · **neto 455.000,00**
- Con amparo FAECYS (art. 131 suspendido, aporte modernización = 0): **neto 460.687,50**
- Media jornada (0,5): **neto 227.500,00**

## Decisiones de diseño
Ver `DECISIONS.md` (D-01 a D-17). Claves: Dinero/Decimal con redondeo solo por
concepto; parámetros legales NUNCA hardcodeados (todo `is_verified=False` hasta
verificación de contador); RLS en tablas de negocio (empleado, liquidacion,
liquidacion_detalle, recibo); tablas de auth scopeadas en la app; snapshot
inmutable de parámetros por liquidación.

## Pendientes / próximos pasos (el usuario elegirá)
1. **Ejecutar y dejar en verde el gate de Fase 2** (integración + aislamiento
   multi-tenant). Requiere Postgres. Caminos: arreglar Docker (activar
   virtualización + reiniciar) o instalar Postgres local. Al correr por primera
   vez es probable que haya que corregir algún detalle (no se ejecutó nunca).
2. **Conceptos configurables**: permitir que el usuario defina adicionales/
   descuentos por convenio (título, zona, viáticos, premios, ausencias que
   descuenten presentismo) sin tocar código, para que el motor "liquide cualquier
   concepto". El usuario mostró interés.
3. **Fase 3 — Recibo PDF Anexo III**: plantilla HTML+CSS → WeasyPrint → PDF A4,
   4 secciones + gráfico de torta SVG server-side, hash SHA-256, envío por email.
   ⚠️ Antes de programar la plantilla, conseguir/replicar el modelo oficial del
   Anexo III (Decreto 407/2026 en argentina.gob.ar) — no inventar el layout.
4. **Fase 4**: updater legal (detección→staging→aprobación humana→propagación),
   exportaciones LSD/F.931/xlsx, liquidación final/indemnizaciones.
5. Falta también: Impuesto a las Ganancias 4ª categoría, adicionales por CCT,
   conceptos no remunerativos.

## Cómo trabajar
- No mezclar nada con la carpeta "mayolista.2".
- Fase por fase; mostrar resultados y esperar confirmación antes de avanzar.
- Ser honesto sobre lo que está verificado vs. solo escrito.
- Respuestas concisas, en español. El usuario a veces no puede correr comandos
  complejos: preferir demos ejecutables de una línea y guiar paso a paso.
```
