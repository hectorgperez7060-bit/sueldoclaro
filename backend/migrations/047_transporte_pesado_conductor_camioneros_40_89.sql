-- CCT 40/89 · transporte pesado por sistema de arrastre, conductor.
BEGIN;

DELETE FROM public.parametro_legal
WHERE cct_numero = '40/89'
  AND valid_from = DATE '2026-08-01'
  AND version = 1
  AND codigo IN (
    'CAM_PESADO_HASTA_50_PCT',
    'CAM_PESADO_50_100_PCT',
    'CAM_PESADO_MAS_100_PCT'
  );

INSERT INTO public.parametro_legal (
  id, codigo, valor, unidad, ambito, valid_from, valid_to, fuente,
  estado_fuente, is_verified, version, cct_numero, incidencias
)
SELECT
  gen_random_uuid(), codigo, valor, '%', 'rama_pct',
  DATE '2026-08-01', DATE '2026-08-31',
  'CCT 40/89 ítem 5.8.1.2.a; Laudo 16/04/1990 homologado Disp. DNRT 2932/90',
  'VERIFICADA_OFICIAL', true, 1, '40/89',
  jsonb_build_object(
    'descripcion', descripcion,
    'base', 'basico_conductor_primera',
    'remunerativo', true,
    'integra_antiguedad', true,
    'integra_aportes', true,
    'articulo', '5.8.1.2.a'
  )
FROM (VALUES
  ('CAM_PESADO_HASTA_50_PCT', 0.12, 'Hasta 50 toneladas de carga útil'),
  ('CAM_PESADO_50_100_PCT', 0.15, 'Más de 50 y hasta 100 toneladas de carga útil'),
  ('CAM_PESADO_MAS_100_PCT', 0.20, 'Más de 100 toneladas de carga útil')
) AS reglas(codigo, valor, descripcion);

DO $$
BEGIN
  IF (
    SELECT count(*)
    FROM public.parametro_legal
    WHERE cct_numero = '40/89'
      AND valid_from = DATE '2026-08-01'
      AND codigo LIKE 'CAM_PESADO_%_PCT'
      AND is_verified = true
  ) <> 3 THEN
    RAISE EXCEPTION 'No se cargaron los tres tramos verificados de transporte pesado';
  END IF;
END
$$;

COMMIT;
