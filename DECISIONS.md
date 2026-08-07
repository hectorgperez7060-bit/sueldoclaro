# DECISIONS.md — SUELDOCLARO

Registro de decisiones tomadas durante la implementación (sección 0.5 del prompt
maestro: "Si una decisión no está especificada, elegí la opción más simple que
cumpla los requisitos y documentala").

## Fase 1 — Dominio y motor de cálculo

### D-01 · Aislamiento del proyecto
SUELDOCLARO vive en su propia carpeta (`sueldoClaeo/`), **separada** del proyecto
Mayolista. No comparte código, dependencias ni configuración.

### D-02 · `Dinero` como value object de precisión completa
`Dinero` guarda un `Decimal` sin redondear. El redondeo `ROUND_HALF_UP` a 2
decimales se aplica **solo** al llamar `.redondear()`, que se invoca únicamente
en el importe final de cada concepto (regla 0.3). Los cálculos intermedios
(valor hora, bases) mantienen precisión completa. Multiplicar o sacar porcentaje
con `float` lanza `TypeError` a propósito.

### D-03 · Base imponible de deducciones
La base de las deducciones es la **suma de los conceptos remunerativos ya
redondeados** (los renglones reales del recibo), no una suma de valores sin
redondear. Esto garantiza reproducibilidad: el recibo cierra con sus renglones.

### D-04 · Tope SIPA
Jubilación, Ley 19.032 y Obra Social se calculan sobre `min(base, TOPE_SIPA)`.
La cuota sindical y el aporte de modernización se calculan sobre la base
remunerativa completa (sin tope), por ser de naturaleza convencional.

### D-05 · Estrategias por amparo (concepto dual)
Cada concepto afectado por la reforma declara dos reglas: `regla_ley_27802` y
`regla_previa`. El `AmparoSet` decide cuál aplicar según CCT + concepto +
vigencia del período. El `Concepto` resultante registra `regimen` y
`articulo_amparo` para trazabilidad ante inspección.

- **Concepto de ejemplo modelado:** `APORTE_MODERNIZACION` (aporte del trabajador
  supuestamente creado por el art. 131 de la Ley 27.802).
  - Sin amparo → `regla_ley_27802`: se retiene el % del parámetro
    `APORTE_MODERNIZACION`. Régimen `ley_27802`.
  - Con amparo FAECYS/Comercio (`L27802:131`) → `regla_previa`: el aporte no
    existía → importe `0.00`. Régimen `previa`.
  - **Marcado como ejemplo:** la existencia y alícuota exacta de este aporte es
    un placeholder (`is_verified = false`). El mecanismo es el entregable; el
    valor legal debe verificarlo un contador.

### D-06 · CUIL módulo 11
Prefijos aceptados: 20, 23, 24, 27, 30, 33, 34. Cuando `11 - (suma % 11) == 10`
(requiere cambio de prefijo), el número se considera inválido tal como está
(se rechaza), en lugar de aplicar el "hack" común de forzar dígito 9. Documentado
por si un contador reporta un CUIL real de ese subconjunto.

### D-07 · Antigüedad
- Antigüedad para el adicional mensual: años **completos** a la fecha de cálculo
  del período (`día 28` del mes por defecto).
- Antigüedad para vacaciones: años completos al **31/12** del año del período
  (LCT art. 151). Tramos LCT art. 150: `<5 → 14`, `<10 → 21`, `<20 → 28`,
  `>=20 → 35` días.

### D-08 · Presentismo Comercio
Se calcula como `(básico + antigüedad) / 12` (equivalente a 8,33%), tomando 12
como divisor parametrizado en `CctConfig`, no como porcentaje hardcodeado.

### D-09 · SAC
`50% × mejor remuneración del semestre × (días_trabajados / 181)`. Se aplican
aportes de seguridad social (jubilación, Ley 19.032, obra social) sobre el SAC;
la cuota sindical no se aplica sobre el SAC en esta fase (revisable por CCT).

### D-10 · Parámetros legales
Ningún valor legal está hardcodeado en el motor. Todos llegan vía `ParametroSet`
/ `EscalaSalarial` / `CctConfig`. El seed (`backend/seed/parametros_seed.py`)
marca **todo** con `is_verified = false` y fuente "EJEMPLO — verificar…".

### D-11 · Python de desarrollo
El target de producción es Python 3.12/3.13 (sección 3). El dominio de Fase 1 es
Python puro (dataclasses + Decimal, sin dependencias de infraestructura) y corre
también en 3.10+, lo que facilita CI y desarrollo local.

## Fase 2 — Persistencia y API

### D-12 · RLS con un solo GUC de sesión
El aislamiento se enforcea en PostgreSQL con `ENABLE`+`FORCE ROW LEVEL SECURITY`
y una política por tabla: `tenant_id = NULLIF(current_setting('app.current_tenant', true), '')::uuid`.
Cada request setea el GUC con `set_config(..., true)` (local a la transacción).
El `NULLIF` hace *fail-closed*: sin tenant seteado, 0 filas. El `tenant_id`
proviene siempre del claim `tid` del JWT, nunca del body/query.

### D-13 · Alcance de RLS
RLS se aplica a las tablas de datos de negocio: `empleado`, `liquidacion`,
`liquidacion_detalle`, `recibo`. Las tablas globales (parámetros legales) no
llevan tenant_id (compartidas).

### D-14 · Tablas de auth scopeadas en la aplicación
`tenant`, `usuario` y `usuario_tenant` se manejan a nivel de aplicación con
chequeo explícito de membresía, no con RLS. Motivo: el login necesita resolver a
qué tenants pertenece un usuario *antes* de tener un tenant activo, lo que RLS
sobre `usuario_tenant` bloquearía. `usuario` es global (un usuario puede
pertenecer a varios estudios con distinto rol).

### D-15 · liquidacion_detalle con conceptos en JSONB
Cada `liquidacion_detalle` es una fila por empleado con los conceptos como array
JSONB (código, descripción, tipo, importe, régimen, artículo de amparo), en lugar
de una fila por concepto. Simplifica el guardado del recibo y conserva la
trazabilidad del régimen aplicado. La liquidación guarda además un
`snapshot_parametros` inmutable (JSONB) para reproducibilidad histórica.

### D-16 · Migración con create_all + RLS
La migración `0001_init` crea el esquema desde el metadata de los modelos y luego
aplica el SQL de RLS (compartido en `infrastructure/database/rls.py`, usado también
por el bootstrap de tests para garantizar paridad prod/test). `audit_log` es
append-only: se revoca UPDATE/DELETE al rol de la app (best-effort si el rol existe).

### D-17 · Refresh rotativo
Access token 15 min (claim `tid` = empresa activa). Refresh con `jti` en un store
revocable (Redis en prod; fallback en memoria para dev/tests): al refrescar se
revoca el `jti` viejo y se emite uno nuevo (rotación). El refresh porta `tid`/`rol`
para poder reemitir el access de la misma empresa.

## Pendiente de verificación por contador matriculado (antes de producción)
- Alícuotas de aportes y contribuciones (valores de ejemplo).
- Existencia, número de artículo y alícuota del "aporte de modernización".
- Escalas salariales FAECYS vigentes.
- Estado y alcance real de las cautelares (FAECYS, Camioneros, CGT).
- Tope de base imponible SIPA vigente.
