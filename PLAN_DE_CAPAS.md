# SUELDO CLARO — Plan de capas (según Documento Maestro v1.0)

Estado al 2026-08-01. App en producción: https://my-project-six-rho-76.vercel.app
Regla: una capa por vez, se verifica en producción antes de pasar a la siguiente.

## ✅ Capa 0 — Base (hecha y verificada)
Motor de cálculo con golden tests, multi-empresa con aislamiento RLS verificado,
API en Vercel + BD Supabase (gratis), pantalla en español, smoke test en verde.

## ✅ Capa 1 — Convenios por sindicato (hecha 2026-08-01)
- 6 convenios cargados: Comercio 130/75 (FAECYS), Metalúrgicos 260/75 (UOM),
  Construcción 76/75 (UOCRA, sin presentismo), Gastronómicos 389/04 (UTHGRA),
  Sanidad 122/75 (FATSA), Camioneros 40/89. 17 categorías.
- Amparo del art. 131 (Ley 27.802) cargado por gremio (EJEMPLO, verificar).
- Cuota sindical propia de cada convenio (FATSA 3%, UOM/UOCRA/UTHGRA 2,5%...).
- La pantalla ahora tiene selector de Convenio → Categorías dinámicas.
- TODO valor sigue marcado is_verified=false hasta revisión de contador.

## ⏳ Capa 2 — Circuito de aprobación (siguiente)
Simulación → borrador → comparación con el mes anterior → rol "aprobador" →
cierre definitivo. Historial de liquidaciones en pantalla. (Doc secciones 13 y 30.)

## ⏳ Capa 3 — Novedades completas
Ausencias, licencias, premios, embargos, anticipos, retroactivos, con controles
por tipo. (Doc sección 15.)

## ⏳ Capa 4 — Recibo PDF oficial
Formato Anexo III Decreto 407/2026 (4 secciones + gráfico de torta), hash de
integridad, descarga y envío por email. (Doc sección 20.)

## ⏳ Capa 5 — Liquidación final / desvinculación
Fecha libre, causal, indemnizaciones, reglas vigentes a la fecha del hecho.
(Doc sección 14.)

## ⏳ Capa 6 — Roles ampliados y seguridad
Propietario/aprobador/auditor, MFA, contador revisor con acceso por caso.
(Doc secciones 9, 19 y 25.)

## ⏳ Capa 7 — Motor normativo pleno
Fórmulas como datos versionados con estados (borrador→aprobada→vigente),
pipeline de cambios legales con aprobación humana, conceptos configurables
por el usuario. (Doc secciones 16 y 17.)

## ⏳ Capa 8 — IA asistente
Carga de novedades en lenguaje cotidiano, explicación de cálculos, detección
de inconsistencias. La IA propone, nunca aprueba. (Doc sección 18.)

## Decisiones registradas (para Documento Maestro v1.1)
- D-C1: Backend Python/FastAPI VALIDADO en producción (reemplaza la propuesta
  TypeScript de la sección 23; el propio doc pedía validar con prototipo).
- D-C2: Infraestructura gratuita actual: Vercel (API+pantalla) + Supabase (BD
  con RLS). Documentada en ENTORNO_NUBE.md.
- D-C3: El aporte del art. 131 se modela con estrategia por amparo por CCT,
  extensible a otros artículos vía tabla amparo_cct.
