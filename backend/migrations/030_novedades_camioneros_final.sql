-- Paquete final de captura Camioneros CCT 40/89.
-- Conserva en una sola columna versionable los hechos de viaje y rama.
BEGIN;

ALTER TABLE public.novedad_mensual
  ADD COLUMN IF NOT EXISTS camioneros_detalle jsonb NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE public.novedad_mensual
  DROP CONSTRAINT IF EXISTS camioneros_detalle_objeto;
ALTER TABLE public.novedad_mensual
  ADD CONSTRAINT camioneros_detalle_objeto
  CHECK (jsonb_typeof(camioneros_detalle) = 'object');

COMMENT ON COLUMN public.novedad_mensual.camioneros_detalle IS
  'Hechos variables CCT 40/89: rama, zona, frío, viajes, kilómetros, viáticos y permanencias. No contiene importes.';

INSERT INTO public.cct_paquete_version
  (cct_numero, paquete_version, hash_sha256, estado, resumen, fuente_manifest)
VALUES
  ('40/89', '2026.08-captura-final-v3',
   '746d05bbdce040bd2b04b564e44b7c2aebb3a0d7d813fe07f40a52508c92c37a',
   'VALIDADO',
   jsonb_build_object(
     'captura_novedades', 'PRODUCTIVA',
     'motor_variables', 'VISTA_PREVIA',
     'liquidacion_recibo', 'BLOQUEADA_HASTA_INCIDENCIAS_VERIFICADAS',
     'migracion', '030_novedades_camioneros_final'
   ),
   'FADEEAC Planilla agosto 2026 + CCT 40/89; incidencias pendientes se bloquean')
ON CONFLICT (cct_numero, paquete_version) DO UPDATE SET
  estado = EXCLUDED.estado,
  resumen = EXCLUDED.resumen,
  fuente_manifest = EXCLUDED.fuente_manifest,
  hash_sha256 = EXCLUDED.hash_sha256,
  instalado_at = now();

COMMIT;
