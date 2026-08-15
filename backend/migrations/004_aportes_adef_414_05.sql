-- Aportes ADEF del CCT 414/05, arts. 46 y 47.
-- Fuente oficial: https://www.adef.org.ar/institucional/legislacion/
-- convenio-colectivo-de-trabajo-nro-414-05?showall=1
-- No crea una cuota de afiliado: el art. 47 exige notificación de ADEF.

BEGIN;

INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to,
  fuente, is_verified, version, cct_numero, incidencias
)
SELECT
  gen_random_uuid(), 'APORTE_ADEF_REM_414/05', 0.02, '%', 'ded_todos',
  DATE '2005-09-01', NULL,
  'CCT 414/05 art. 46 — ADEF, texto oficial', true, 1, '414/05',
  '{"base_deduccion":"remunerativa","destino_pago":"ADEF","codigo_boleta":"ADEF_APORTES","canal_pago":"Sistema de Aportes en Linea ADEF","url_pago":"https://www.adef.org.ar/sistema-de-aportes-en-linea","regla_vencimiento":"Misma fecha que los aportes sindicales; fecha exacta segun la boleta emitida por ADEF","fuente_pago":"CCT 414/05 art. 46 y Sistema de Aportes en Linea ADEF"}'::jsonb
WHERE NOT EXISTS (
  SELECT 1 FROM public.parametro_legal
  WHERE codigo = 'APORTE_ADEF_REM_414/05' AND valid_to IS NULL
);

INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to,
  fuente, is_verified, version, cct_numero, incidencias
)
SELECT
  gen_random_uuid(), 'APORTE_ADEF_ASISTENCIA_414/05', 0.01, '%', 'ded_todos',
  DATE '2005-06-01', NULL,
  'CCT 414/05 art. 46 — ADEF, texto oficial', true, 1, '414/05',
  '{"base_deduccion":"remunerativa","meses_aplicacion":[6,12],"destino_pago":"ADEF","codigo_boleta":"ADEF_APORTES","canal_pago":"Sistema de Aportes en Linea ADEF","url_pago":"https://www.adef.org.ar/sistema-de-aportes-en-linea","regla_vencimiento":"Misma fecha que los aportes sindicales; fecha exacta segun la boleta emitida por ADEF","fuente_pago":"CCT 414/05 art. 46 y Sistema de Aportes en Linea ADEF"}'::jsonb
WHERE NOT EXISTS (
  SELECT 1 FROM public.parametro_legal
  WHERE codigo = 'APORTE_ADEF_ASISTENCIA_414/05' AND valid_to IS NULL
);

-- Si el codigo ya existia, completa la trazabilidad oficial sin duplicarlo.
UPDATE public.parametro_legal
SET valor = 0.02,
    unidad = '%',
    ambito = 'ded_todos',
    fuente = 'CCT 414/05 art. 46 — ADEF, texto oficial',
    is_verified = true,
    cct_numero = '414/05',
    incidencias = COALESCE(incidencias, '{}'::jsonb) ||
      '{"base_deduccion":"remunerativa","destino_pago":"ADEF","codigo_boleta":"ADEF_APORTES","canal_pago":"Sistema de Aportes en Linea ADEF","url_pago":"https://www.adef.org.ar/sistema-de-aportes-en-linea","regla_vencimiento":"Misma fecha que los aportes sindicales; fecha exacta segun la boleta emitida por ADEF","fuente_pago":"CCT 414/05 art. 46 y Sistema de Aportes en Linea ADEF"}'::jsonb
WHERE codigo = 'APORTE_ADEF_REM_414/05' AND valid_to IS NULL;

UPDATE public.parametro_legal
SET valor = 0.01,
    unidad = '%',
    ambito = 'ded_todos',
    fuente = 'CCT 414/05 art. 46 — ADEF, texto oficial',
    is_verified = true,
    cct_numero = '414/05',
    incidencias = COALESCE(incidencias, '{}'::jsonb) ||
      '{"base_deduccion":"remunerativa","meses_aplicacion":[6,12],"destino_pago":"ADEF","codigo_boleta":"ADEF_APORTES","canal_pago":"Sistema de Aportes en Linea ADEF","url_pago":"https://www.adef.org.ar/sistema-de-aportes-en-linea","regla_vencimiento":"Misma fecha que los aportes sindicales; fecha exacta segun la boleta emitida por ADEF","fuente_pago":"CCT 414/05 art. 46 y Sistema de Aportes en Linea ADEF"}'::jsonb
WHERE codigo = 'APORTE_ADEF_ASISTENCIA_414/05' AND valid_to IS NULL;

COMMIT;
