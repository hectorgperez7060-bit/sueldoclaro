-- CCT 40/89 · auxiliares especializados de transporte pesado.
BEGIN;

DELETE FROM public.parametro_legal
WHERE cct_numero = '40/89'
  AND valid_from = DATE '2026-08-01'
  AND version = 1
  AND codigo IN (
    'CAM_PESADO_AUX_MECANICO_PCT',
    'CAM_PESADO_AUX_HIDRAULICO_PCT'
  );

INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to, fuente,
  estado_fuente, is_verified, version, cct_numero, incidencias
)
SELECT
  gen_random_uuid(), codigo, valor, '%', 'rama_pct',
  DATE '2026-08-01', DATE '2026-08-31',
  'CCT 40/89 ítem 5.8.1.2.b; Laudo 16/04/1990 homologado Disp. DNRT 2932/90',
  'VERIFICADA_OFICIAL', true, 1, '40/89',
  jsonb_build_object(
    'descripcion', descripcion,
    'base', 'basico_operario_especializado',
    'remunerativo', true,
    'integra_antiguedad', true,
    'integra_aportes', true,
    'articulo', '5.8.1.2.b',
    'categoria_no_permanente', true
  )
FROM (VALUES
  ('CAM_PESADO_AUX_MECANICO_PCT', 0.10, 'Auxiliar especializado · carretón mecánico'),
  ('CAM_PESADO_AUX_HIDRAULICO_PCT', 0.13, 'Auxiliar especializado · carretón hidráulico')
) AS reglas(codigo, valor, descripcion);

DO $$
BEGIN
  IF (
    SELECT count(*) FROM public.parametro_legal
    WHERE cct_numero = '40/89'
      AND valid_from = DATE '2026-08-01'
      AND codigo IN ('CAM_PESADO_AUX_MECANICO_PCT','CAM_PESADO_AUX_HIDRAULICO_PCT')
      AND is_verified = true
  ) <> 2 THEN
    RAISE EXCEPTION 'No se cargaron las reglas verificadas de auxiliares de transporte pesado';
  END IF;
END
$$;

COMMIT;
