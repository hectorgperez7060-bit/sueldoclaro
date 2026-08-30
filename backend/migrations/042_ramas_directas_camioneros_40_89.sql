-- CCT 40/89 · adicionales remunerativos de cinco ramas con fórmula directa.
BEGIN;

DELETE FROM public.parametro_legal
WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01' AND version=1
  AND codigo IN (
   'CAM_RAMA_MATERIA_PRIMA_LACTEA_PCT','CAM_RAMA_AUXILIO_PCT',
   'CAM_RAMA_DIARIOS_REVISTAS_PCT','CAM_RAMA_COMBUSTIBLES_PCT',
   'CAM_RAMA_SUSTANCIAS_PELIGROSAS_PCT'
  );

WITH datos(codigo, valor, articulo, descripcion) AS (VALUES
 ('CAM_RAMA_MATERIA_PRIMA_LACTEA_PCT', 0.15::numeric, '3.1.3', 'Transporte de materia prima láctea'),
 ('CAM_RAMA_AUXILIO_PCT', 0.10::numeric, '3.1.4', 'Conductores de camiones o camionetas de auxilio'),
 ('CAM_RAMA_DIARIOS_REVISTAS_PCT', 0.12::numeric, '5.4.1', 'Distribución de diarios y revistas'),
 ('CAM_RAMA_COMBUSTIBLES_PCT', 0.15::numeric, '5.5.1', 'Transporte de combustibles'),
 ('CAM_RAMA_SUSTANCIAS_PELIGROSAS_PCT', 0.20::numeric, '5.6.2', 'Transporte de sustancias peligrosas')
)
INSERT INTO public.parametro_legal
 (id,codigo,valor,unidad,ambito,valid_from,valid_to,fuente,estado_fuente,
  is_verified,version,cct_numero,incidencias)
SELECT gen_random_uuid(), codigo, valor, '%', 'rama_pct', DATE '2026-08-01',
       DATE '2026-08-31',
       'CCT 40/89 ítem '||articulo||'; Planilla salarial FedCam 8/26 hoja 2',
       'PUBLICADA_POR_PARTE_SIGNATARIA', true, 1, '40/89',
       jsonb_build_object(
         'descripcion', descripcion, 'base', 'basico_categoria',
         'remunerativo', true, 'integra_antiguedad', true,
         'integra_aportes', true, 'articulo', articulo
       )
FROM datos;

DO $$
DECLARE cantidad integer;
BEGIN
 SELECT count(*) INTO cantidad FROM public.parametro_legal
 WHERE cct_numero='40/89' AND valid_from=DATE '2026-08-01'
   AND codigo IN (
    'CAM_RAMA_MATERIA_PRIMA_LACTEA_PCT','CAM_RAMA_AUXILIO_PCT',
    'CAM_RAMA_DIARIOS_REVISTAS_PCT','CAM_RAMA_COMBUSTIBLES_PCT',
    'CAM_RAMA_SUSTANCIAS_PELIGROSAS_PCT'
   ) AND is_verified;
 IF cantidad <> 5 THEN
   RAISE EXCEPTION 'No se cargaron las cinco ramas directas de Camioneros';
 END IF;
END $$;

COMMIT;
